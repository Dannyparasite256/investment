"""Celery tasks for portfolio snapshots, digests, lifecycle emails."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('core')


@shared_task
def daily_portfolio_snapshots():
    from core.portfolio import snapshot_all_users
    n = snapshot_all_users()
    logger.info('Portfolio snapshots: %s users', n)
    return n


@shared_task
def update_market_prices():
    """Refresh crypto + fiat prices from free public APIs."""
    from core.price_feed import refresh_all_prices
    result = refresh_all_prices(force=True)
    logger.info('Price feed: %s', result)
    return result


@shared_task
def daily_admin_digest():
    """Branded ops digest to staff (+ classic mail_admins fallback)."""
    try:
        from core.email_events import email_staff_ops_digest
        n = email_staff_ops_digest()
        logger.info('Staff ops digest emailed to %s recipients', n)
        return n
    except Exception:
        logger.exception('staff ops digest failed')
        from django.contrib.auth import get_user_model
        from django.core.mail import mail_admins
        from transactions.models import Deposit, Withdrawal
        from core.models import SiteConfiguration

        User = get_user_model()
        today = timezone.now().date()
        body = (
            f"Site: {SiteConfiguration.get_solo().site_name}\n"
            f"New users today: {User.objects.filter(date_joined__date=today).count()}\n"
            f"Pending deposits: {Deposit.objects.filter(status=Deposit.Status.PENDING).count()}\n"
            f"Pending withdrawals: {Withdrawal.objects.filter(status=Withdrawal.Status.PENDING).count()}\n"
        )
        mail_admins('Daily platform digest', body, fail_silently=True)
        return body


@shared_task
def check_price_alerts_task():
    from django.core.management import call_command
    call_command('check_price_alerts')
    return 'ok'


@shared_task
def send_weekly_digests():
    """Branded weekly portfolio summary."""
    from django.contrib.auth import get_user_model
    from django.db.models import Sum
    from wallets.models import Wallet
    from investments.models import Earning
    from core.email_events import email_weekly_digest_html

    User = get_user_model()
    since = timezone.now() - timedelta(days=7)
    sent = 0
    for u in User.objects.filter(is_active=True, weekly_digest_emails=True).iterator():
        if not u.email:
            continue
        wallet, _ = Wallet.objects.get_or_create(user=u)
        earned = Earning.objects.filter(user=u, created_at__gte=since).aggregate(t=Sum('amount'))['t'] or 0
        try:
            if email_weekly_digest_html(
                u, wallet.available_balance, wallet.total_invested, earned,
            ):
                sent += 1
        except Exception:
            logger.exception('weekly digest failed %s', u.email)
    logger.info('Weekly digests sent: %s', sent)
    return sent


@shared_task
def send_welcome_series():
    """Day-1 and day-3 onboarding emails (day-0 sent at register)."""
    from django.contrib.auth import get_user_model
    from accounts.models import ActivityEvent
    from core.email_events import email_welcome

    User = get_user_model()
    now = timezone.now()
    sent = 0
    # Day 1: registered ~24–48h ago, no day1 email yet
    d1_start, d1_end = now - timedelta(hours=48), now - timedelta(hours=24)
    for u in User.objects.filter(is_active=True, date_joined__gte=d1_start, date_joined__lt=d1_end).iterator():
        if ActivityEvent.objects.filter(user=u, event_type='welcome_email_d1').exists():
            continue
        try:
            email_welcome(u, day=1)
            ActivityEvent.objects.create(user=u, event_type='welcome_email_d1', title='Welcome day-1 email')
            sent += 1
        except Exception:
            logger.exception('welcome d1 %s', u.email)

    d3_start, d3_end = now - timedelta(hours=96), now - timedelta(hours=72)
    for u in User.objects.filter(is_active=True, date_joined__gte=d3_start, date_joined__lt=d3_end).iterator():
        if ActivityEvent.objects.filter(user=u, event_type='welcome_email_d3').exists():
            continue
        try:
            email_welcome(u, day=3)
            ActivityEvent.objects.create(user=u, event_type='welcome_email_d3', title='Welcome day-3 email')
            sent += 1
        except Exception:
            logger.exception('welcome d3 %s', u.email)
    logger.info('Welcome series emails: %s', sent)
    return sent


@shared_task
def nudge_stale_deposits():
    """Remind users about deposits pending > 24h."""
    from transactions.models import Deposit
    from accounts.models import ActivityEvent
    from core.email_events import email_stale_deposit_nudge

    cutoff = timezone.now() - timedelta(hours=24)
    qs = Deposit.objects.filter(
        status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION],
        created_at__lte=cutoff,
    ).select_related('user', 'cryptocurrency')[:200]
    sent = 0
    for dep in qs:
        key = f'stale_deposit_nudge_{dep.id}'
        if ActivityEvent.objects.filter(user=dep.user, event_type=key).exists():
            continue
        try:
            email_stale_deposit_nudge(dep)
            ActivityEvent.objects.create(
                user=dep.user, event_type=key, title='Stale deposit nudge',
                description=str(dep.id),
            )
            sent += 1
        except Exception:
            logger.exception('stale deposit nudge %s', dep.id)
    logger.info('Stale deposit nudges: %s', sent)
    return sent


@shared_task
def winback_inactive_users():
    """Email users inactive ~14–16 days."""
    from django.contrib.auth import get_user_model
    from accounts.models import ActivityEvent
    from core.email_events import email_winback

    User = get_user_model()
    now = timezone.now()
    start, end = now - timedelta(days=16), now - timedelta(days=14)
    sent = 0
    for u in User.objects.filter(is_active=True, last_login__gte=start, last_login__lt=end).iterator():
        if ActivityEvent.objects.filter(user=u, event_type='winback_14d').exists():
            continue
        try:
            email_winback(u, days_inactive=14)
            ActivityEvent.objects.create(user=u, event_type='winback_14d', title='Win-back email')
            sent += 1
        except Exception:
            logger.exception('winback %s', u.email)
    logger.info('Win-back emails: %s', sent)
    return sent


@shared_task
def check_withdrawal_sla_breaches():
    """Alert staff (and soft-update users) when withdrawal SLA is overdue."""
    from transactions.models import Withdrawal
    from accounts.models import ActivityEvent
    from core.email_events import email_withdrawal_sla_breach

    now = timezone.now()
    qs = Withdrawal.objects.filter(
        status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.APPROVED, Withdrawal.Status.PROCESSING],
        sla_deadline__isnull=False,
        sla_deadline__lt=now,
    ).select_related('user')[:100]
    sent = 0
    for w in qs:
        key = f'withdrawal_sla_{w.id}'
        if ActivityEvent.objects.filter(user=w.user, event_type=key).exists():
            continue
        try:
            email_withdrawal_sla_breach(w)
            ActivityEvent.objects.create(
                user=w.user, event_type=key, title='Withdrawal SLA breach emailed',
            )
            sent += 1
        except Exception:
            logger.exception('sla breach %s', w.id)
    logger.info('SLA breach emails: %s', sent)
    return sent


@shared_task
def monthly_statement_emails():
    """Notify users that monthly statements are available."""
    from django.contrib.auth import get_user_model
    from accounts.models import ActivityEvent
    from core.email_events import email_statement_ready

    User = get_user_model()
    period = timezone.now().strftime('%B %Y')
    key = f'statement_{timezone.now().strftime("%Y_%m")}'
    sent = 0
    for u in User.objects.filter(is_active=True, weekly_digest_emails=True).iterator():
        if not u.email:
            continue
        if ActivityEvent.objects.filter(user=u, event_type=key).exists():
            continue
        try:
            email_statement_ready(u, period)
            ActivityEvent.objects.create(user=u, event_type=key, title=f'Statement email {period}')
            sent += 1
        except Exception:
            logger.exception('statement email %s', u.email)
    logger.info('Monthly statement emails: %s', sent)
    return sent
