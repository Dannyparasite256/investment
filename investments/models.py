"""Investment plans and user investments with configurable earnings."""
from datetime import timedelta
from decimal import Decimal

import re
import uuid as uuid_lib

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

from core.models import TimeStampedModel, UUIDModel
from core.utils import quantize_amount


class InvestmentPlan(UUIDModel, TimeStampedModel):
    """Admin-configurable investment product."""

    class ProfitMethod(models.TextChoices):
        PERCENTAGE_OF_PRINCIPAL = 'pct_principal', 'Percentage of Principal'
        FIXED_AMOUNT = 'fixed', 'Fixed Amount per Period'
        COMPOUND = 'compound', 'Compound Interest'

    class PayoutFrequency(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        END = 'end', 'At Maturity Only'

    class RiskLevel(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        VERY_HIGH = 'very_high', 'Very High'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        COMING_SOON = 'coming_soon', 'Coming Soon'
        ARCHIVED = 'archived', 'Archived'

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=255, blank=True)

    min_deposit = models.DecimalField(max_digits=18, decimal_places=8, validators=[MinValueValidator(Decimal('0.01'))])
    max_deposit = models.DecimalField(max_digits=18, decimal_places=8, validators=[MinValueValidator(Decimal('0.01'))])

    # Duration in days (flexible maturity)
    duration_days = models.PositiveIntegerField(help_text='Investment duration in days')
    duration_flexible = models.BooleanField(
        default=False,
        help_text='If true, user can choose duration within min/max below',
    )
    min_duration_days = models.PositiveIntegerField(null=True, blank=True)
    max_duration_days = models.PositiveIntegerField(null=True, blank=True)
    early_exit_fee_percent = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('0'),
        help_text='Fee % if user exits before maturity',
    )

    profit_method = models.CharField(
        max_length=20,
        choices=ProfitMethod.choices,
        default=ProfitMethod.PERCENTAGE_OF_PRINCIPAL,
    )
    # Expected return range (admin-configurable, not hard-coded)
    return_percent_min = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0'),
        help_text='Minimum expected return % over full duration',
        validators=[MinValueValidator(Decimal('0'))],
    )
    return_percent_max = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0'),
        help_text='Maximum expected return % over full duration',
        validators=[MinValueValidator(Decimal('0'))],
    )
    # Actual profit rate used for calculations (admin-defined rule)
    profit_rate_percent = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('0'),
        help_text='Profit % applied per payout period (or total if end-only)',
        validators=[MinValueValidator(Decimal('0'))],
    )
    fixed_profit_amount = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal('0'),
        help_text='Used when profit_method is fixed amount',
    )

    payout_frequency = models.CharField(
        max_length=20,
        choices=PayoutFrequency.choices,
        default=PayoutFrequency.DAILY,
    )
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    is_featured = models.BooleanField(default=False)
    allow_auto_reinvest = models.BooleanField(default=True)
    allow_manual_reinvest = models.BooleanField(default=True)
    return_principal = models.BooleanField(
        default=True,
        help_text='Return principal at maturity',
    )
    max_investments_per_user = models.PositiveIntegerField(null=True, blank=True)
    total_invested = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    investors_count = models.PositiveIntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True, default='bi-graph-up-arrow')
    color = models.CharField(max_length=20, blank=True, default='#f0b90b')
    sort_order = models.PositiveIntegerField(default=0)
    require_kyc = models.BooleanField(
        default=False,
        help_text='Only KYC-verified users may invest in this plan',
    )
    # Staking-style early exit
    early_exit_allowed = models.BooleanField(default=False)
    early_exit_penalty_percent = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('10'),
        help_text='Penalty % of principal if user exits early',
    )
    is_premium = models.BooleanField(
        default=False,
        help_text='Premium plan (VIP Gold+ or KYC often required)',
    )
    min_vip_slug = models.CharField(
        max_length=50, blank=True,
        help_text='Optional VIP tier slug required e.g. gold',
    )

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Always produce a URL-safe slug (no spaces or special chars)
        base = slugify(self.slug or self.name) or 'plan'
        base = re.sub(r'[^a-z0-9_-]', '', base.lower())[:140] or 'plan'
        candidate = base
        n = 2
        while InvestmentPlan.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f'{base}-{n}'
            n += 1
            if n > 100:
                candidate = f'{base}-{uuid_lib.uuid4().hex[:8]}'
                break
        self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        return self.status == self.Status.ACTIVE

    def expected_return_display(self):
        if self.return_percent_min == self.return_percent_max:
            return f'{self.return_percent_min}%'
        return f'{self.return_percent_min}% – {self.return_percent_max}%'

    def calculate_period_profit(self, principal: Decimal) -> Decimal:
        """Calculate profit for a single payout period based on admin rules."""
        principal = Decimal(str(principal))
        if self.profit_method == self.ProfitMethod.FIXED_AMOUNT:
            return quantize_amount(self.fixed_profit_amount)
        if self.profit_method == self.ProfitMethod.COMPOUND:
            # Period rate applied to growing principal handled in service
            rate = self.profit_rate_percent / Decimal('100')
            return quantize_amount(principal * rate)
        # Default: percentage of original principal
        rate = self.profit_rate_percent / Decimal('100')
        return quantize_amount(principal * rate)

    def periods_count(self, duration_days=None):
        days = duration_days or self.duration_days
        if self.payout_frequency == self.PayoutFrequency.DAILY:
            return days
        if self.payout_frequency == self.PayoutFrequency.WEEKLY:
            return max(1, days // 7)
        if self.payout_frequency == self.PayoutFrequency.MONTHLY:
            return max(1, days // 30)
        return 1  # end only

    def period_delta(self):
        if self.payout_frequency == self.PayoutFrequency.DAILY:
            return timedelta(days=1)
        if self.payout_frequency == self.PayoutFrequency.WEEKLY:
            return timedelta(weeks=1)
        if self.payout_frequency == self.PayoutFrequency.MONTHLY:
            return timedelta(days=30)
        return timedelta(days=self.duration_days)


class Investment(UUIDModel, TimeStampedModel):
    """User subscription to an investment plan."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        PAUSED = 'paused', 'Paused'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investments',
    )
    plan = models.ForeignKey(
        InvestmentPlan,
        on_delete=models.PROTECT,
        related_name='investments',
    )
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    # Snapshot of plan rules at investment time (admin-configurable, frozen)
    profit_rate_percent = models.DecimalField(max_digits=8, decimal_places=4)
    profit_method = models.CharField(max_length=20)
    payout_frequency = models.CharField(max_length=20)
    duration_days = models.PositiveIntegerField()
    return_principal = models.BooleanField(default=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    auto_reinvest = models.BooleanField(default=False)

    total_earned = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    last_payout_at = models.DateTimeField(null=True, blank=True)
    next_payout_at = models.DateTimeField(null=True, blank=True)
    payouts_count = models.PositiveIntegerField(default=0)
    expected_payouts = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(default=timezone.now)
    matures_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'next_payout_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f'{self.user.email} — {self.plan.name} ({self.amount})'

    @property
    def progress_percent(self):
        if not self.started_at or not self.matures_at:
            return 0
        total = (self.matures_at - self.started_at).total_seconds()
        if total <= 0:
            return 100
        elapsed = (timezone.now() - self.started_at).total_seconds()
        return min(100, max(0, round(elapsed / total * 100, 1)))

    @property
    def is_matured(self):
        return timezone.now() >= self.matures_at

    def calculate_period_profit(self):
        principal = self.amount
        if self.profit_method == InvestmentPlan.ProfitMethod.FIXED_AMOUNT:
            # Use plan's fixed amount if still linked
            return quantize_amount(self.plan.fixed_profit_amount)
        if self.profit_method == InvestmentPlan.ProfitMethod.COMPOUND:
            rate = self.profit_rate_percent / Decimal('100')
            base = self.amount + self.total_earned
            return quantize_amount(base * rate)
        rate = self.profit_rate_percent / Decimal('100')
        return quantize_amount(principal * rate)


class Earning(UUIDModel, TimeStampedModel):
    """Individual profit payout record."""

    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='earnings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='earnings')
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    period_number = models.PositiveIntegerField(default=1)
    is_reinvested = models.BooleanField(default=False)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f'Earning {self.amount} for {self.user.email}'


class Reinvestment(UUIDModel, TimeStampedModel):
    """Record of reinvestment actions."""

    class Mode(models.TextChoices):
        AUTO = 'auto', 'Automatic'
        MANUAL = 'manual', 'Manual'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reinvestments')
    source_investment = models.ForeignKey(
        Investment,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reinvestments_from',
    )
    new_investment = models.ForeignKey(
        Investment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reinvestments_to',
    )
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.MANUAL)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Reinvest {self.amount} ({self.mode})'
