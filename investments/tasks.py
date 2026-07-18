"""Celery tasks for scheduled earnings processing."""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('investments')


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_scheduled_earnings(self):
    """Pay out earnings for all investments due."""
    from investments.models import Investment
    from investments.services import process_earning

    now = timezone.now()
    due = Investment.objects.filter(
        status=Investment.Status.ACTIVE,
        next_payout_at__lte=now,
    ).select_related('plan', 'user')

    processed = 0
    errors = 0
    for inv in due.iterator():
        try:
            process_earning(inv)
            processed += 1
        except Exception as exc:
            errors += 1
            logger.exception('Failed processing earning for %s: %s', inv.id, exc)

    # Also complete matured investments that may have missed end payout
    matured = Investment.objects.filter(
        status=Investment.Status.ACTIVE,
        matures_at__lte=now,
    )
    from investments.services import complete_investment

    for inv in matured.iterator():
        try:
            # If end-only frequency, process final earning then complete
            if inv.payout_frequency == 'end' and inv.payouts_count < inv.expected_payouts:
                process_earning(inv)
            elif inv.status == Investment.Status.ACTIVE:
                complete_investment(inv)
            processed += 1
        except Exception as exc:
            errors += 1
            logger.exception('Failed completing investment %s: %s', inv.id, exc)

    logger.info('process_scheduled_earnings: processed=%s errors=%s', processed, errors)
    return {'processed': processed, 'errors': errors}


@shared_task
def process_single_earning(investment_id: str):
    from investments.models import Investment
    from investments.services import process_earning

    inv = Investment.objects.get(pk=investment_id)
    result = process_earning(inv)
    return str(result.id) if result else None
