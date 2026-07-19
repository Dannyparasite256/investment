"""Login history, suspicious activity, and session security."""
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel, UUIDModel


class LoginHistory(UUIDModel, TimeStampedModel):
    """Record every login attempt (success and failure)."""

    class Result(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        BLOCKED = 'blocked', 'Blocked'
        SUSPICIOUS = 'suspicious', 'Suspicious'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='login_history',
    )
    email_attempted = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    timezone_name = models.CharField(max_length=64, blank=True, help_text='IANA timezone at access location')
    isp = models.CharField(max_length=120, blank=True)
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.SUCCESS)
    is_suspicious = models.BooleanField(default=False)
    suspicion_reason = models.CharField(max_length=255, blank=True)
    session_key = models.CharField(max_length=64, blank=True)
    auth_method = models.CharField(
        max_length=20,
        blank=True,
        default='password',
        help_text='password | google | x | unknown',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Login histories'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address', '-created_at']),
            models.Index(fields=['is_suspicious', '-created_at']),
        ]

    def __str__(self):
        who = self.user.email if self.user else self.email_attempted
        return f'{who} @ {self.ip_address} — {self.result}'

    @property
    def location_display(self) -> str:
        parts = [p for p in (self.city, self.region, self.country) if p]
        cleaned = []
        for p in parts:
            if not cleaned or cleaned[-1].lower() != p.lower():
                cleaned.append(p)
        return ', '.join(cleaned) or (self.ip_address or 'Unknown')


class AdminActivityLog(UUIDModel, TimeStampedModel):
    """Staff panel activity trail."""

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='admin_activities',
    )
    action = models.CharField(max_length=100, db_index=True)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['admin', '-created_at'])]

    def __str__(self):
        return f'{self.admin} — {self.action} @ {self.created_at}'


class UserSuspension(UUIDModel, TimeStampedModel):
    """Track user suspensions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='suspensions',
    )
    reason = models.TextField()
    suspended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='suspensions_issued',
    )
    is_active = models.BooleanField(default=True)
    lifted_at = models.DateTimeField(null=True, blank=True)
    lifted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='suspensions_lifted',
    )

    class Meta:
        ordering = ['-created_at']

    def lift(self, admin_user):
        self.is_active = False
        self.lifted_at = timezone.now()
        self.lifted_by = admin_user
        self.save()
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
