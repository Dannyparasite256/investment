"""Celery tasks for transactions."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('transactions')


@shared_task
def flag_stale_deposits():
    """Mark long-pending deposits as waiting confirmation for admin attention."""
    from transactions.models import Deposit

    cutoff = timezone.now() - timedelta(hours=24)
    updated = Deposit.objects.filter(
        status=Deposit.Status.PENDING,
        created_at__lt=cutoff,
    ).update(status=Deposit.Status.WAITING_CONFIRMATION)
    logger.info('flag_stale_deposits: updated=%s', updated)
    return updated
