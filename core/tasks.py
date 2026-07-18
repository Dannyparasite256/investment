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
