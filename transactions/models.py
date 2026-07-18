"""Deposits, withdrawals, and unified ledger transactions."""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone

from core.models import TimeStampedModel, UUIDModel
from wallets.models import Cryptocurrency, Wallet, WalletLedger


class Deposit(UUIDModel, TimeStampedModel):
    """Crypto deposit — balance credits only after admin approval."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        WAITING_CONFIRMATION = 'waiting_confirmation', 'Waiting Confirmation'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits',
    )
    cryptocurrency = models.ForeignKey(
        Cryptocurrency, on_delete=models.PROTECT, related_name='deposits',
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000001'))],
    )
    fee = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    credit_amount = models.DecimalField(
        max_digits=18, decimal_places=8, null=True, blank=True,
        help_text='Platform credit in USD-equivalent after approval (crypto amount × rate)',
    )
    # Snapshot rate used at approval for audit
    rate_usd = models.DecimalField(
        max_digits=24, decimal_places=8, null=True, blank=True,
        help_text='USD price of 1 unit of deposited crypto at approval',
    )
    transaction_hash = models.CharField(max_length=128, db_index=True)
    screenshot = models.ImageField(upload_to='deposits/%Y/%m/', blank=True, null=True)
    network = models.CharField(max_length=20, blank=True)
    deposit_address = models.CharField(max_length=256, blank=True)
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    promo_code = models.CharField(max_length=32, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_deposits',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f'Deposit {self.amount} {self.cryptocurrency.symbol} — {self.status}'

    def save(self, *args, **kwargs):
        if self.cryptocurrency_id and not self.network:
            self.network = self.cryptocurrency.network
        if self.cryptocurrency_id and not self.deposit_address:
            self.deposit_address = self.cryptocurrency.deposit_address
        super().save(*args, **kwargs)

    def crypto_net_amount(self):
        """Deposit amount in selected crypto units (minus fee)."""
        return Decimal(str(self.amount)) - (self.fee or Decimal('0'))

    def platform_credit_usd(self):
        """
        Convert crypto amount → platform balance (USD-equivalent)
        using the cryptocurrency's current usd_price.
        e.g. 0.01 BTC × $95,000 = $950 platform credit.
        USDT at $1 → 100 USDT = $100 credit.
        """
        crypto_amt = self.crypto_net_amount()
        price = Decimal(str(self.cryptocurrency.usd_price or 1))
        if price <= 0:
            price = Decimal('1')
        return (crypto_amt * price).quantize(Decimal('0.00000001'))

    @transaction.atomic
    def approve(self, admin_user, credit_amount=None, notes=''):
        if self.status == self.Status.APPROVED:
            raise ValueError('Deposit already approved')

        price = Decimal(str(self.cryptocurrency.usd_price or 1))
        if price <= 0:
            price = Decimal('1')

        if credit_amount is not None:
            credit = Decimal(str(credit_amount))
        elif self.credit_amount is not None:
            credit = Decimal(str(self.credit_amount))
        else:
            # Convert selected crypto amount into platform value
            credit = self.platform_credit_usd()

        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        wallet.credit(credit, update_deposited=True)
        WalletLedger.objects.create(
            wallet=wallet,
            entry_type=WalletLedger.EntryType.DEPOSIT,
            amount=credit,
            balance_after=wallet.balance,
            description=(
                f'Deposit approved: {self.amount} {self.cryptocurrency.symbol} '
                f'@ ${price} = {credit} platform'
            ),
            reference_type='deposit',
            reference_id=str(self.id),
            created_by=admin_user,
        )
        self.status = self.Status.APPROVED
        self.credit_amount = credit
        self.rate_usd = price
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()

        # Keep permanent display currency (UGX/USD/…). Only seed if empty.
        user = self.user
        if not (user.preferred_currency or '').strip():
            user.preferred_currency = self.cryptocurrency.symbol
            user.save(update_fields=['preferred_currency'])

        Transaction.objects.update_or_create(
            reference_type='deposit',
            reference_id=str(self.id),
            defaults={
                'user': self.user,
                'tx_type': Transaction.TxType.DEPOSIT,
                'amount': self.amount,  # crypto units for history
                'fee': self.fee or Decimal('0'),
                'currency': self.cryptocurrency.symbol,
                'network': self.network,
                'wallet_address': self.deposit_address,
                'tx_hash': self.transaction_hash,
                'status': Transaction.Status.COMPLETED,
                'description': (
                    f'Deposit {self.amount} {self.cryptocurrency.symbol} '
                    f'(≈ {credit} platform @ ${price})'
                ),
                'administrator': admin_user,
                'notes': self.admin_notes,
                'metadata': {
                    'crypto_amount': str(self.amount),
                    'rate_usd': str(price),
                    'platform_credit': str(credit),
                },
            },
        )
        # Pay referrers using the *current* active commission % (idempotent)
        try:
            from referrals.services import process_referral_commission
            process_referral_commission(
                self.user,
                credit,
                source='deposit',
                reference_type='deposit',
                reference_id=self.id,
            )
        except Exception:
            import logging
            logging.getLogger('transactions').exception(
                'Referral commission failed for deposit %s', self.id,
            )
        return self

    @transaction.atomic
    def reject(self, admin_user, reason='', notes=''):
        if self.status == self.Status.APPROVED:
            raise ValueError('Cannot reject an approved deposit')
        self.status = self.Status.REJECTED
        self.rejection_reason = reason
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
        Transaction.objects.filter(
            reference_type='deposit', reference_id=str(self.id),
        ).update(
            status=Transaction.Status.FAILED,
            administrator=admin_user,
            notes=reason or notes,
        )
        return self


class Withdrawal(UUIDModel, TimeStampedModel):
    """
    Withdrawal workflow (admin approval required):
      Pending → Approved → Paid
                ↘ Rejected
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        PAID = 'paid', 'Paid'
        # Legacy aliases kept for migration compatibility
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals',
    )
    cryptocurrency = models.ForeignKey(
        Cryptocurrency, on_delete=models.PROTECT, related_name='withdrawals',
    )
    amount = models.DecimalField(
        max_digits=18, decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000001'))],
    )
    fee = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    net_amount = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    wallet_address = models.CharField(max_length=256)
    network = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    transaction_hash = models.CharField(max_length=128, blank=True)
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_withdrawals',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    funds_locked = models.BooleanField(default=True)
    # SLA / queue
    sla_deadline = models.DateTimeField(
        null=True, blank=True,
        help_text='Target time to complete withdrawal (admin SLA)',
    )
    priority = models.PositiveSmallIntegerField(
        default=0,
        help_text='Higher = process first (VIP)',
    )

    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
        verbose_name_plural = 'Withdrawals'

    def __str__(self):
        return f'Withdrawal {self.amount} — {self.status}'

    def save(self, *args, **kwargs):
        if self.cryptocurrency_id and not self.network:
            self.network = self.cryptocurrency.network
        if not self.net_amount:
            self.net_amount = self.amount - (self.fee or Decimal('0'))
        super().save(*args, **kwargs)

    @transaction.atomic
    def approve(self, admin_user, notes=''):
        """Mark as approved (awaiting on-chain payout). Funds stay locked."""
        if self.status not in (self.Status.PENDING, self.Status.PROCESSING):
            raise ValueError(f'Cannot approve withdrawal in status {self.status}')
        self.status = self.Status.APPROVED
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
        Transaction.objects.filter(
            reference_type='withdrawal', reference_id=str(self.id),
        ).update(
            status=Transaction.Status.PROCESSING,
            administrator=admin_user,
            notes=notes or self.admin_notes,
        )
        return self

    @transaction.atomic
    def mark_paid(self, admin_user, tx_hash='', notes=''):
        """Final payout: debit wallet and mark Paid."""
        if self.status not in (self.Status.APPROVED, self.Status.PENDING, self.Status.PROCESSING):
            raise ValueError(f'Cannot mark paid from status {self.status}')
        wallet = Wallet.objects.select_for_update().get(user=self.user)
        if self.funds_locked:
            wallet.unlock_funds(self.amount)
            self.funds_locked = False
        # Debit only if not already debited (idempotent check via status)
        if self.status != self.Status.PAID and self.status != self.Status.COMPLETED:
            wallet.debit(self.amount, update_withdrawn=True)
            WalletLedger.objects.create(
                wallet=wallet,
                entry_type=WalletLedger.EntryType.WITHDRAWAL,
                amount=-self.amount,
                balance_after=wallet.balance,
                description=f'Withdrawal paid to {self.wallet_address[:16]}…',
                reference_type='withdrawal',
                reference_id=str(self.id),
                created_by=admin_user,
            )
        self.status = self.Status.PAID
        self.transaction_hash = tx_hash or self.transaction_hash
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.paid_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
        Transaction.objects.update_or_create(
            reference_type='withdrawal',
            reference_id=str(self.id),
            defaults={
                'user': self.user,
                'tx_type': Transaction.TxType.WITHDRAWAL,
                'amount': self.amount,
                'fee': self.fee or Decimal('0'),
                'currency': self.cryptocurrency.symbol,
                'network': self.network,
                'wallet_address': self.wallet_address,
                'tx_hash': self.transaction_hash,
                'status': Transaction.Status.COMPLETED,
                'description': f'Withdrawal paid {self.amount} {self.cryptocurrency.symbol}',
                'administrator': admin_user,
                'notes': self.admin_notes,
            },
        )
        return self

    @transaction.atomic
    def reject(self, admin_user, reason='', notes=''):
        if self.status in (self.Status.PAID, self.Status.COMPLETED):
            raise ValueError('Cannot reject a paid withdrawal')
        if self.funds_locked:
            wallet = Wallet.objects.select_for_update().get(user=self.user)
            wallet.unlock_funds(self.amount)
            self.funds_locked = False
        self.status = self.Status.REJECTED
        self.rejection_reason = reason
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
        Transaction.objects.filter(
            reference_type='withdrawal', reference_id=str(self.id),
        ).update(
            status=Transaction.Status.FAILED,
            administrator=admin_user,
            notes=reason or notes,
        )
        return self


class Transaction(UUIDModel, TimeStampedModel):
    """
    Unified transaction record.

    Fields: UUID, amount, currency, fee, status, network, wallet, hash,
    timestamp, administrator, notes.
    """

    class TxType(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'
        INVESTMENT = 'investment', 'Investment'
        PROFIT = 'profit', 'Profit'
        REFERRAL = 'referral', 'Referral'
        REINVEST = 'reinvest', 'Reinvest'
        REFUND = 'refund', 'Refund'
        FEE = 'fee', 'Fee'
        ADJUSTMENT = 'adjustment', 'Adjustment'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions',
    )
    tx_type = models.CharField(max_length=20, choices=TxType.choices, db_index=True)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    fee = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal('0'))
    currency = models.CharField(max_length=20, blank=True, default='USD')
    network = models.CharField(max_length=32, blank=True)
    wallet_address = models.CharField(max_length=256, blank=True)
    tx_hash = models.CharField(max_length=128, blank=True, db_index=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    description = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='administered_transactions',
    )
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['tx_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f'{self.tx_type} {self.amount} {self.currency} ({self.status})'
