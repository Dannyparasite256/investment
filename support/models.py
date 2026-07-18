"""Support tickets and contact requests."""
from django.conf import settings
from django.db import models

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

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'#{str(self.id)[:8]} {self.subject}'


class TicketMessage(UUIDModel, TimeStampedModel):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    is_staff_reply = models.BooleanField(default=False)
    attachment = models.FileField(upload_to='tickets/%Y/%m/', blank=True, null=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Message on {self.ticket_id}'
