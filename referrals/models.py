"""Referral commissions and program configuration."""
from decimal import Decimal

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel, UUIDModel


class ReferralProgram(TimeStampedModel):
    """Singleton referral program settings."""

    name = models.CharField(max_length=100, default='Standard Referral')
    commission_percent = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('5.00'),
        help_text='Commission % of referred user deposit or investment',
    )
    commission_on = models.CharField(
        max_length=20,
        choices=[
            ('deposit', 'First Deposit'),
            ('investment', 'Each Investment'),
            ('profit', 'Profits'),
        ],
        default='deposit',
    )
    is_active = models.BooleanField(default=True)
    min_deposit_for_commission = models.DecimalField(
        max_digits=18, decimal_places=8, default=Decimal('0'),
    )
    max_commission_per_referral = models.DecimalField(
        max_digits=18, decimal_places=8, null=True, blank=True,
    )
    # Multi-level (up to 3 tiers up the chain)
    level1_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('5.00'))
    level2_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('2.00'))
    level3_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('1.00'))
    max_levels = models.PositiveSmallIntegerField(default=2, help_text='1–3 levels')

    class Meta:
        verbose_name = 'Referral Program'

    def __str__(self):
        return f'{self.name} ({self.commission_percent}%)'

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).order_by('-created_at').first()


class ReferralCommission(UUIDModel, TimeStampedModel):
    """Individual commission payout to a referrer."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        CANCELLED = 'cancelled', 'Cancelled'

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commissions_earned',
    )
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='commissions_generated',
    )
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    rate_percent = models.DecimalField(max_digits=6, decimal_places=2)
    base_amount = models.DecimalField(max_digits=18, decimal_places=8)
    source = models.CharField(max_length=20, default='deposit')  # deposit | investment | profit
    level = models.PositiveSmallIntegerField(default=1, help_text='1 = direct, 2–3 = upline')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=64, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['referrer', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f'{self.referrer.email} +{self.amount} from {self.referred_user.email}'
