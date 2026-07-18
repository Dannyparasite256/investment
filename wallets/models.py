"""Wallet, cryptocurrency, and balance models."""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F

from core.models import TimeStampedModel, UUIDModel


class Cryptocurrency(TimeStampedModel):
    """Supported cryptocurrencies and networks."""

    class Network(models.TextChoices):
        BITCOIN = 'BTC', 'Bitcoin'
        ETHEREUM = 'ERC20', 'Ethereum (ERC20)'
        TRON = 'TRC20', 'Tron (TRC20)'
        BSC = 'BEP20', 'BNB Smart Chain (BEP20)'
        LITECOIN = 'LTC', 'Litecoin'

    symbol = models.CharField(max_length=20, unique=True)  # BTC, ETH, USDT_TRC20, etc.
    name = models.CharField(max_length=100)
    network = models.CharField(max_length=20, choices=Network.choices)
    contract_address = models.CharField(max_length=128, blank=True)
    decimals = models.PositiveSmallIntegerField(default=8)
    icon = models.CharField(max_length=50, blank=True, help_text='CSS icon class or emoji')
    is_active = models.BooleanField(default=True)
    min_deposit = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0.001'))
    min_withdrawal = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('10'))
    max_withdrawal = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('100000'))
    withdrawal_fee = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    sort_order = models.PositiveIntegerField(default=0)

    # Platform deposit address (admin-managed)
    deposit_address = models.CharField(max_length=256, blank=True)
    qr_code = models.ImageField(upload_to='wallet_qr/', blank=True, null=True)
    # USD price for display conversion (admin-updated)
    usd_price = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        default=Decimal('1'),
        help_text='Current price in USD used for balance display conversion',
    )

    class Meta:
        ordering = ['sort_order', 'symbol']
        verbose_name_plural = 'Cryptocurrencies'

    def __str__(self):
        return f'{self.name} ({self.symbol})'


class Wallet(UUIDModel, TimeStampedModel):
    """User balance wallet (single balance pool in USD-equivalent)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
    )
    balance = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
    )
    locked_balance = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        default=Decimal('0'),
        help_text='Funds locked in active investments or pending withdrawals',
        validators=[MinValueValidator(Decimal('0'))],
    )
    total_deposited = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    total_withdrawn = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    total_profit = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    total_invested = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Wallet({self.user.email}) bal={self.balance}'

    @property
    def available_balance(self):
        return self.balance - self.locked_balance

    @property
    def portfolio_value(self):
        """Available + locked (invested) capital."""
        return self.balance

    @transaction.atomic
    def credit(self, amount, update_deposited=False, update_profit=False):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('Credit amount must be positive')
        updates = {'balance': F('balance') + amount}
        if update_deposited:
            updates['total_deposited'] = F('total_deposited') + amount
        if update_profit:
            updates['total_profit'] = F('total_profit') + amount
        Wallet.objects.filter(pk=self.pk).update(**updates)
        self.refresh_from_db()
        return self.balance

    @transaction.atomic
    def debit(self, amount, update_withdrawn=False):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('Debit amount must be positive')
        wallet = Wallet.objects.select_for_update().get(pk=self.pk)
        if wallet.available_balance < amount:
            raise ValueError('Insufficient available balance')
        wallet.balance -= amount
        if update_withdrawn:
            wallet.total_withdrawn += amount
        wallet.save()
        self.refresh_from_db()
        return self.balance

    @transaction.atomic
    def lock_funds(self, amount):
        amount = Decimal(str(amount))
        wallet = Wallet.objects.select_for_update().get(pk=self.pk)
        if wallet.available_balance < amount:
            raise ValueError('Insufficient available balance to lock')
        wallet.locked_balance += amount
        wallet.save(update_fields=['locked_balance', 'updated_at'])
        self.refresh_from_db()

    @transaction.atomic
    def unlock_funds(self, amount):
        amount = Decimal(str(amount))
        wallet = Wallet.objects.select_for_update().get(pk=self.pk)
        wallet.locked_balance = max(Decimal('0'), wallet.locked_balance - amount)
        wallet.save(update_fields=['locked_balance', 'updated_at'])
        self.refresh_from_db()


class UserWalletAddress(UUIDModel, TimeStampedModel):
    """User-saved withdrawal addresses."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet_addresses',
    )
    cryptocurrency = models.ForeignKey(
        Cryptocurrency,
        on_delete=models.CASCADE,
        related_name='user_addresses',
    )
    address = models.CharField(max_length=256)
    label = models.CharField(max_length=100, blank=True)
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_default', '-created_at']
        unique_together = [('user', 'cryptocurrency', 'address')]
        verbose_name_plural = 'User wallet addresses'

    def __str__(self):
        return f'{self.user.email} — {self.cryptocurrency.symbol}: {self.address[:12]}…'

    def save(self, *args, **kwargs):
        if self.is_default:
            UserWalletAddress.objects.filter(
                user=self.user,
                cryptocurrency=self.cryptocurrency,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class WalletLedger(UUIDModel, TimeStampedModel):
    """Double-entry style balance change log."""

    class EntryType(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'
        INVESTMENT = 'investment', 'Investment'
        PROFIT = 'profit', 'Profit'
        REFUND = 'refund', 'Refund'
        REFERRAL = 'referral', 'Referral Bonus'
        FEE = 'fee', 'Fee'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        REINVEST = 'reinvest', 'Reinvest'

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='ledger')
    entry_type = models.CharField(max_length=20, choices=EntryType.choices, db_index=True)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    balance_after = models.DecimalField(max_digits=18, decimal_places=8)
    description = models.CharField(max_length=255, blank=True)
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=64, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['entry_type', '-created_at']),
        ]

    def __str__(self):
        return f'{self.entry_type} {self.amount} → {self.balance_after}'
