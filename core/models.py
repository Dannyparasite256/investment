"""Core shared models: audit logs, site settings, currency rates."""
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class AuditLog(TimeStampedModel):
    class Action(models.TextChoices):
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        REGISTER = 'register', 'Register'
        PASSWORD_CHANGE = 'password_change', 'Password Change'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
        EMAIL_VERIFY = 'email_verify', 'Email Verify'
        TWO_FA_ENABLE = '2fa_enable', '2FA Enable'
        TWO_FA_DISABLE = '2fa_disable', '2FA Disable'
        KYC_SUBMIT = 'kyc_submit', 'KYC Submit'
        KYC_APPROVE = 'kyc_approve', 'KYC Approve'
        KYC_REJECT = 'kyc_reject', 'KYC Reject'
        DEPOSIT_CREATE = 'deposit_create', 'Deposit Create'
        DEPOSIT_APPROVE = 'deposit_approve', 'Deposit Approve'
        DEPOSIT_REJECT = 'deposit_reject', 'Deposit Reject'
        WITHDRAW_CREATE = 'withdraw_create', 'Withdraw Create'
        WITHDRAW_APPROVE = 'withdraw_approve', 'Withdraw Approve'
        WITHDRAW_REJECT = 'withdraw_reject', 'Withdraw Reject'
        WITHDRAW_PAID = 'withdraw_paid', 'Withdraw Paid'
        INVEST_CREATE = 'invest_create', 'Invest Create'
        INVEST_COMPLETE = 'invest_complete', 'Invest Complete'
        PROFILE_UPDATE = 'profile_update', 'Profile Update'
        USER_SUSPEND = 'user_suspend', 'User Suspend'
        USER_ACTIVATE = 'user_activate', 'User Activate'
        ADMIN_ACTION = 'admin_action', 'Admin Action'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs',
    )
    action = models.CharField(max_length=32, choices=Action.choices, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    path = models.CharField(max_length=512, blank=True)
    method = models.CharField(max_length=10, blank=True)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    message = models.TextField(blank=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'action']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        user = self.user.email if self.user else 'anonymous'
        return f'{self.action} by {user} at {self.created_at}'


class SiteConfiguration(TimeStampedModel):
    site_name = models.CharField(max_length=100, default='CryptoInvest')
    support_email = models.EmailField(default='support@cryptoinvest.local')
    min_withdrawal = models.DecimalField(max_digits=18, decimal_places=8, default=10)
    max_withdrawal = models.DecimalField(max_digits=18, decimal_places=8, default=100000)
    referral_bonus_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(
        blank=True,
        default='We are performing scheduled maintenance. Please check back soon.',
    )
    announcement = models.TextField(blank=True)
    deposit_instructions = models.TextField(
        blank=True,
        default='Send the exact amount to the provided wallet address and submit your transaction hash.',
    )
    default_language = models.CharField(max_length=10, default='en')
    session_timeout_minutes = models.PositiveIntegerField(default=60)
    withdrawal_sla_hours = models.PositiveIntegerField(
        default=24,
        help_text='Target hours to process withdrawals',
    )
    require_captcha_register = models.BooleanField(default=False)
    live_chat_embed = models.TextField(
        blank=True,
        help_text='Optional Crisp/Intercom embed snippet',
    )
    risk_disclaimer = models.TextField(
        blank=True,
        default=(
            'Cryptocurrency and investment products involve significant risk. '
            'Past or projected returns are not guaranteed. Only invest what you can afford to lose.'
        ),
    )
    captcha_site_key = models.CharField(max_length=200, blank=True)
    captcha_secret_key = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Site Configuration'
        verbose_name_plural = 'Site Configuration'

    def __str__(self):
        return self.site_name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class CurrencyRate(TimeStampedModel):
    """Simple fiat/crypto conversion rates (admin-managed)."""

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    rate_to_usd = models.DecimalField(max_digits=24, decimal_places=12, default=Decimal('1'))
    is_active = models.BooleanField(default=True)
    symbol = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} = {self.rate_to_usd} USD'

    def convert(self, amount_usd):
        if not self.rate_to_usd:
            return Decimal('0')
        return Decimal(str(amount_usd)) / self.rate_to_usd
