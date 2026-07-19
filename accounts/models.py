"""Custom user model, KYC, profile, and security models."""
import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from core.models import TimeStampedModel, UUIDModel

# Re-export security models for migrations convenience
from accounts.security_models import AdminActivityLog, LoginHistory, UserSuspension  # noqa: E402,F401


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Email-based user with referral, KYC, and role flags."""

    class Role(models.TextChoices):
        USER = 'user', 'User'
        SUPPORT = 'support', 'Support Agent'
        MANAGER = 'manager', 'Manager'
        ADMIN = 'admin', 'Administrator'

    username = None
    email = models.EmailField('email address', unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/%Y/%m/', blank=True, null=True)
    avatar_url = models.URLField(
        blank=True,
        max_length=500,
        help_text='Remote avatar from Google/X when no uploaded picture is set',
    )
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=16, unique=True, blank=True)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals',
    )
    referral_earnings = models.DecimalField(max_digits=18, decimal_places=8, default=0)
    is_kyc_verified = models.BooleanField(default=False)
    preferred_theme = models.CharField(
        max_length=10, choices=[('dark', 'Dark'), ('light', 'Light')], default='dark',
    )
    preferred_ui_theme = models.CharField(
        max_length=16,
        choices=[
            ('classic', 'Default Theme'),
            ('premium', 'Premium Investment Theme'),
        ],
        default='classic',
        help_text='Visual design system: classic glass or premium investment UI',
    )
    preferred_language = models.CharField(max_length=10, default='en')
    preferred_timezone = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text='IANA timezone e.g. Africa/Kampala, detected from browser or login location',
    )
    preferred_currency = models.CharField(
        max_length=20,
        default='',
        blank=True,
        help_text='Display crypto symbol (e.g. BTC, USDT_TRC20). Empty = last deposit crypto. Not USD by default.',
    )
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER, db_index=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    notes_internal = models.TextField(blank=True, help_text='Internal admin notes')
    risk_score = models.PositiveSmallIntegerField(default=0, db_index=True)
    tour_completed = models.BooleanField(default=False)
    kyc_expires_at = models.DateField(null=True, blank=True)
    country_code = models.CharField(max_length=2, blank=True, help_text='ISO country code')
    sms_alerts = models.BooleanField(default=False)
    email_alerts = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']
        permissions = [
            ('access_staff_panel', 'Can access custom staff panel'),
            ('approve_deposits', 'Can approve deposits'),
            ('approve_withdrawals', 'Can approve withdrawals'),
            ('manage_kyc', 'Can manage KYC'),
            ('view_reports', 'Can view reports'),
        ]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_referral_code():
        return secrets.token_hex(4).upper()

    def get_full_name(self):
        name = f'{self.first_name} {self.last_name}'.strip()
        return name or self.email

    def generate_email_token(self):
        self.email_verification_token = secrets.token_urlsafe(32)
        self.save(update_fields=['email_verification_token'])
        return self.email_verification_token

    @property
    def display_name(self):
        return self.get_full_name()

    @property
    def avatar_display_url(self):
        """
        Best available photo URL for templates.

        Prefer a real file on disk; if missing (common before media mapping),
        fall back to the remote Google/X avatar URL which loads without /media/.
        """
        import os

        remote = (self.avatar_url or '').strip()
        if self.profile_picture and self.profile_picture.name:
            try:
                path = self.profile_picture.path
                if path and os.path.isfile(path):
                    return self.profile_picture.url
            except Exception:
                pass
            # File record exists but path may be unavailable — try remote first
            if remote:
                return remote
            try:
                return self.profile_picture.url
            except Exception:
                pass
        return remote

    @property
    def is_platform_staff(self):
        return self.is_staff or self.role in (
            self.Role.SUPPORT, self.Role.MANAGER, self.Role.ADMIN,
        ) or self.is_superuser


class KYCDocument(UUIDModel, TimeStampedModel):
    class DocumentType(models.TextChoices):
        PASSPORT = 'passport', 'Passport'
        NATIONAL_ID = 'national_id', 'National ID'
        DRIVERS_LICENSE = 'drivers_license', "Driver's License"
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        UNDER_REVIEW = 'under_review', 'Under Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(max_length=32, choices=DocumentType.choices)
    document_number = models.CharField(max_length=100, blank=True)
    front_image = models.ImageField(upload_to='kyc/%Y/%m/')
    back_image = models.ImageField(upload_to='kyc/%Y/%m/', blank=True, null=True)
    selfie_image = models.ImageField(upload_to='kyc/%Y/%m/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kyc_reviews',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'KYC Document'
        verbose_name_plural = 'KYC Documents'

    def __str__(self):
        return f'KYC {self.user.email} — {self.status}'

    def approve(self, admin_user, valid_days=365):
        self.status = self.Status.APPROVED
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.save()
        self.user.is_kyc_verified = True
        self.user.kyc_expires_at = (timezone.now() + timedelta(days=valid_days)).date()
        self.user.save(update_fields=['is_kyc_verified', 'kyc_expires_at'])

    def reject(self, admin_user, reason=''):
        self.status = self.Status.REJECTED
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()


class PasswordResetToken(UUIDModel, TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()

    @classmethod
    def create_for_user(cls, user, hours=24):
        return cls.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
            expires_at=timezone.now() + timedelta(hours=hours),
        )


class ActivityEvent(UUIDModel, TimeStampedModel):
    """User activity timeline (deposits, investments, logins, etc.)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_events')
    event_type = models.CharField(max_length=50, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f'{self.event_type}: {self.title}'


class SocialAccount(UUIDModel, TimeStampedModel):
    """Linked OAuth identity (Google, X/Twitter, …)."""

    class Provider(models.TextChoices):
        GOOGLE = 'google', 'Google'
        X = 'x', 'X (Twitter)'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    provider = models.CharField(max_length=20, choices=Provider.choices, db_index=True)
    provider_user_id = models.CharField(max_length=128, db_index=True)
    email = models.EmailField(blank=True)
    username = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=200, blank=True)
    avatar_url = models.URLField(blank=True, max_length=500)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('provider', 'provider_user_id')]
        indexes = [models.Index(fields=['user', 'provider'])]

    def __str__(self):
        return f'{self.provider}:{self.provider_user_id} → {self.user.email}'

