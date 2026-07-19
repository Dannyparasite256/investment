"""Support tickets and contact requests."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel, UUIDModel


class SupportTicket(UUIDModel, TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        WAITING = 'waiting', 'Waiting on User'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tickets',
    )
    subject = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True, default='general')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tickets',
    )
    # Cross-process realtime flags (works without Redis on PythonAnywhere)
    user_typing_at = models.DateTimeField(null=True, blank=True)
    staff_typing_at = models.DateTimeField(null=True, blank=True)
    user_last_seen_at = models.DateTimeField(null=True, blank=True)
    staff_last_seen_at = models.DateTimeField(null=True, blank=True)
    # Explicit in-chat flags so online flips off immediately on leave
    user_in_chat = models.BooleanField(default=False)
    staff_in_chat = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at', '-created_at']

    def __str__(self):
        return f'#{str(self.id)[:8]} {self.subject}'


class TicketMessage(UUIDModel, TimeStampedModel):
    """
    Chat message with WhatsApp-style delivery receipts:
    - created_at  → sent (single grey tick)
    - delivered_at → delivered to recipient device (double grey ticks)
    - read_at     → viewed by recipient (double blue ticks)
    - reply_to    → quoted message (WhatsApp-style reply)
    """
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='tickets/%Y/%m/', blank=True, null=True)
    reply_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='replies',
    )
    delivered_at = models.DateTimeField(null=True, blank=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Message on {self.ticket_id}'

    @property
    def receipt_status(self) -> str:
        """sent | delivered | read"""
        if self.read_at:
            return 'read'
        if self.delivered_at:
            return 'delivered'
        return 'sent'

    def mark_delivered(self, when=None):
        if self.delivered_at:
            return False
        self.delivered_at = when or timezone.now()
        self.save(update_fields=['delivered_at', 'updated_at'])
        return True

    def mark_read(self, when=None):
        now = when or timezone.now()
        fields = []
        if not self.delivered_at:
            self.delivered_at = now
            fields.append('delivered_at')
        if not self.read_at:
            self.read_at = now
            fields.append('read_at')
        if fields:
            fields.append('updated_at')
            self.save(update_fields=fields)
            return True
        return False
