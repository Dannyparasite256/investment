"""In-app notifications with optional WebSocket push."""
import logging

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel, UUIDModel

logger = logging.getLogger('notifications')


class Notification(UUIDModel, TimeStampedModel):
    class Level(models.TextChoices):
        INFO = 'info', 'Info'
        SUCCESS = 'success', 'Success'
        WARNING = 'warning', 'Warning'
        DANGER = 'danger', 'Danger'

    class Category(models.TextChoices):
        SYSTEM = 'system', 'System'
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'
        INVESTMENT = 'investment', 'Investment'
        EARNING = 'earning', 'Earning'
        KYC = 'kyc', 'KYC'
        SECURITY = 'security', 'Security'
        REFERRAL = 'referral', 'Referral'
        ANNOUNCEMENT = 'announcement', 'Announcement'
        SUPPORT = 'support', 'Support'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications',
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.INFO)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.SYSTEM)
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(max_length=512, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_read', '-created_at'])]

    def __str__(self):
        return f'{self.title} → {self.user.email}'

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read', 'updated_at'])

    def to_payload(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'message': self.message,
            'level': self.level,
            'category': self.category,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else '',
        }


def push_notification_ws(user_id, payload):
    """Best-effort WebSocket broadcast via channel layer."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(
            f'user_{user_id}',
            {'type': 'notify.message', 'payload': payload},
        )
    except Exception as exc:
        logger.debug('WS push skipped: %s', exc)


def send_web_push(user, title: str, body: str, url: str = '') -> int:
    """
    Browser Web Push for devices that subscribed (Profile → Enable push).
    Requires VAPID keys + pywebpush. Silently no-ops when not configured.
    """
    from django.conf import settings

    public = getattr(settings, 'VAPID_PUBLIC_KEY', '') or ''
    private = getattr(settings, 'VAPID_PRIVATE_KEY', '') or ''
    if not public or not private:
        return 0
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.debug('pywebpush not installed — skip web push')
        return 0

    try:
        from core.platform_models import PushSubscription
    except Exception:
        return 0

    import json

    sent = 0
    payload = json.dumps({
        'title': title[:120],
        'body': (body or '')[:200],
        'url': url or '/app/notifications',
        'tag': f'ci-{(url or "notif")[:80]}',
    })
    claims = {
        'sub': getattr(settings, 'VAPID_ADMIN_EMAIL', None) or 'mailto:admin@localhost',
    }
    for sub in PushSubscription.objects.filter(user=user, is_active=True)[:20]:
        if not sub.endpoint or not sub.p256dh or not sub.auth:
            continue
        try:
            webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                },
                data=payload,
                vapid_private_key=private,
                vapid_claims=claims,
            )
            sent += 1
        except Exception as exc:
            # Gone / unsubscribed → deactivate
            status = getattr(getattr(exc, 'response', None), 'status_code', None)
            if status in (404, 410):
                PushSubscription.objects.filter(pk=sub.pk).update(is_active=False)
            else:
                logger.debug('Web push failed for %s: %s', user.pk, exc)
    return sent


def notify(user, title, message, level=Notification.Level.INFO, category=Notification.Category.SYSTEM, link='', **meta):
    n = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        level=level,
        category=category,
        link=link,
        metadata=meta or {},
    )
    payload = n.to_payload()
    push_notification_ws(user.pk, payload)
    try:
        send_web_push(user, title, message, url=link or '/app/notifications')
    except Exception as exc:
        logger.debug('Web push outer skip: %s', exc)
    return n
