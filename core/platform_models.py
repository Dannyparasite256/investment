"""Platform growth, compliance, and ops models."""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel, UUIDModel


class VIPTier(TimeStampedModel):
    """Loyalty tier based on total invested / deposited."""

    name = models.CharField(max_length=50)  # Bronze, Silver, Gold, Platinum
    slug = models.SlugField(unique=True)
    min_total_invested = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    deposit_fee_percent = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0'))
    withdrawal_fee_percent = models.DecimalField(max_digits=6, decimal_places=3, default=Decimal('0'))
    referral_bonus_boost = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('0'),
        help_text='Extra % points added to referral commission',
    )
    badge_color = models.CharField(max_length=20, default='#8B5CF6')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'min_total_invested']
        verbose_name = 'VIP tier'

    def __str__(self):
        return f'{self.name} (≥{self.min_total_invested})'

    @classmethod
    def for_amount(cls, total_invested):
        total = Decimal(str(total_invested or 0))
        return (
            cls.objects.filter(is_active=True, min_total_invested__lte=total)
            .order_by('-min_total_invested')
            .first()
        )


class PromoCode(UUIDModel, TimeStampedModel):
    code = models.CharField(max_length=32, unique=True, db_index=True)
    description = models.CharField(max_length=255, blank=True)
    bonus_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0'))
    bonus_fixed = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    min_deposit = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    uses_count = models.PositiveIntegerField(default=0)
    per_user_limit = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.starts_at and now < self.starts_at:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        if self.max_uses is not None and self.uses_count >= self.max_uses:
            return False
        return True


class PromoRedemption(UUIDModel, TimeStampedModel):
    promo = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='redemptions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='promo_redemptions')
    deposit_id = models.CharField(max_length=64, blank=True)
    bonus_amount = models.DecimalField(max_digits=18, decimal_places=8, default=0)

    class Meta:
        indexes = [models.Index(fields=['user', 'promo'])]


class TermsVersion(TimeStampedModel):
    version = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=200, default='Terms of Service')
    content = models.TextField()
    is_current = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return f'ToS {self.version}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            TermsVersion.objects.exclude(pk=self.pk).update(is_current=False)


class TermsAcceptance(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='terms_acceptances')
    terms = models.ForeignKey(TermsVersion, on_delete=models.CASCADE, related_name='acceptances')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        unique_together = [('user', 'terms')]
        ordering = ['-created_at']


class GeoRule(TimeStampedModel):
    """Country allow/block for registration and deposits."""

    class Mode(models.TextChoices):
        ALLOW = 'allow', 'Allow only listed'
        BLOCK = 'block', 'Block listed'

    name = models.CharField(max_length=100, default='Default geo rules')
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.BLOCK)
    country_codes = models.TextField(
        blank=True,
        help_text='Comma-separated ISO codes e.g. US,CN,KP',
    )
    is_active = models.BooleanField(default=True)
    block_message = models.CharField(
        max_length=255,
        default='Service is not available in your region.',
    )

    def codes_set(self):
        return {c.strip().upper() for c in self.country_codes.split(',') if c.strip()}

    def is_country_allowed(self, country_code: str) -> bool:
        if not self.is_active:
            return True
        code = (country_code or '').strip().upper()
        codes = self.codes_set()
        if not codes:
            return True
        if self.mode == self.Mode.BLOCK:
            return code not in codes
        return code in codes


class PortfolioSnapshot(UUIDModel, TimeStampedModel):
    """Daily equity point for portfolio performance chart."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio_snapshots')
    date = models.DateField(db_index=True)
    balance = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    invested = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    profit = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    equity = models.DecimalField(max_digits=18, decimal_places=8, default=0)

    class Meta:
        unique_together = [('user', 'date')]
        ordering = ['date']


class PriceAlert(UUIDModel, TimeStampedModel):
    class Direction(models.TextChoices):
        ABOVE = 'above', 'Above'
        BELOW = 'below', 'Below'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='price_alerts')
    symbol = models.CharField(max_length=64, db_index=True)  # FX:EURUSD
    label = models.CharField(max_length=100, blank=True)
    target_price = models.DecimalField(max_digits=24, decimal_places=8)
    direction = models.CharField(max_length=10, choices=Direction.choices, default=Direction.ABOVE)
    is_active = models.BooleanField(default=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    last_price = models.DecimalField(max_digits=24, decimal_places=8, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class WatchlistItem(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist')
    symbol = models.CharField(max_length=64)
    label = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = [('user', 'symbol')]
        ordering = ['label', 'symbol']


class TradingSignal(UUIDModel, TimeStampedModel):
    """Admin-published market signals (informational, not advice)."""

    class Side(models.TextChoices):
        BUY = 'buy', 'Buy'
        SELL = 'sell', 'Sell'
        HOLD = 'hold', 'Hold'

    title = models.CharField(max_length=200)
    symbol = models.CharField(max_length=64)
    side = models.CharField(max_length=10, choices=Side.choices, default=Side.HOLD)
    entry_note = models.TextField(blank=True)
    target = models.CharField(max_length=100, blank=True)
    stop_loss = models.CharField(max_length=100, blank=True)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )

    class Meta:
        ordering = ['-created_at']


class WebhookEndpoint(UUIDModel, TimeStampedModel):
    """Outgoing webhooks for payment/event integrations."""

    name = models.CharField(max_length=100)
    url = models.URLField()
    secret = models.CharField(max_length=128, blank=True)
    events = models.CharField(
        max_length=255,
        default='deposit.approved,withdrawal.paid',
        help_text='Comma-separated event names',
    )
    is_active = models.BooleanField(default=True)

    def event_list(self):
        return [e.strip() for e in self.events.split(',') if e.strip()]


class PlatformBackup(UUIDModel, TimeStampedModel):
    filename = models.CharField(max_length=255)
    path = models.CharField(max_length=512)
    size_bytes = models.BigIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']
