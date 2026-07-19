"""Celery tasks for portfolio snapshots and admin digests."""
import logging

from celery import shared_task
from django.core.mail import mail_admins
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
    from django.contrib.auth import get_user_model
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
    logger.info('Admin digest sent')
    return body


@shared_task
def check_price_alerts_task():
    from django.core.management import call_command
    call_command('check_price_alerts')
    return 'ok'


@shared_task
def send_weekly_digests():
    """Email weekly portfolio summary to users with weekly_digest_emails=True."""
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mail
    from django.conf import settings
    from wallets.models import Wallet
    from investments.models import Earning
    from datetime import timedelta

    User = get_user_model()
    since = timezone.now() - timedelta(days=7)
    sent = 0
    for u in User.objects.filter(is_active=True, weekly_digest_emails=True).iterator():
        if not u.email:
            continue
        wallet, _ = Wallet.objects.get_or_create(user=u)
        earned = Earning.objects.filter(user=u, created_at__gte=since).aggregate(
            t=__import__('django.db.models', fromlist=['Sum']).Sum('amount')
        )['t'] or 0
        body = (
            f"Hi {u.get_full_name() or u.email},\n\n"
            f"Your weekly CryptoInvest summary:\n"
            f"- Available: {wallet.available_balance}\n"
            f"- Invested: {wallet.total_invested}\n"
            f"- Profit this week: {earned}\n\n"
            f"Log in to view details.\n"
        )
        try:
            send_mail(
                'Your weekly investment digest',
                body,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost'),
                [u.email],
                fail_silently=True,
            )
            sent += 1
        except Exception:
            pass
    logger.info('Weekly digests sent: %s', sent)
    return sent
