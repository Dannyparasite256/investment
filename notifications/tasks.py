"""Celery tasks for notifications."""
import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('notifications')


@shared_task
def cleanup_old_notifications():
    """Delete read notifications older than 90 days."""
    from notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=90)
    deleted, _ = Notification.objects.filter(is_read=True, created_at__lt=cutoff).delete()
    logger.info('cleanup_old_notifications: deleted=%s', deleted)
    return deleted
