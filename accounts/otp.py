"""
Free email OTP for login step-up and withdrawal confirmation.

Codes are hashed in cache (not stored plain). Uses Django's email backend
(Gmail / Brevo SMTP, etc.) — no paid SMS required.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger('accounts')

PURPOSE_LOGIN = 'login'
PURPOSE_WITHDRAW = 'withdraw'
PURPOSE_PASSWORD_RESET = 'password_reset'

VALID_PURPOSES = frozenset({PURPOSE_LOGIN, PURPOSE_WITHDRAW, PURPOSE_PASSWORD_RESET})


@dataclass
class OtpResult:
    ok: bool
    message: str = ''
    code: str = ''  # only populated when DEBUG and tests need it — never log in prod paths


def _ttl_seconds() -> int:
    return int(getattr(settings, 'EMAIL_OTP_TTL_MINUTES', 10)) * 60


def _max_attempts() -> int:
    return int(getattr(settings, 'EMAIL_OTP_MAX_ATTEMPTS', 5))


def _resend_cooldown() -> int:
    return int(getattr(settings, 'EMAIL_OTP_RESEND_SECONDS', 60))


def _cache_key(purpose: str, user_id: int) -> str:
    return f'email_otp:{purpose}:{user_id}'


def _send_key(purpose: str, user_id: int) -> str:
    return f'email_otp_send:{purpose}:{user_id}'


def _hash_code(code: str, purpose: str, user_id: int) -> str:
    raw = f'{settings.SECRET_KEY}|otp|{purpose}|{user_id}|{code.strip()}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def generate_code() -> str:
    return f'{secrets.randbelow(1_000_000):06d}'


def _purpose_labels(purpose: str) -> tuple[str, str]:
    if purpose == PURPOSE_WITHDRAW:
        return (
            f'Withdrawal verification code — {settings.SITE_NAME}',
            'withdrawal confirmation',
        )
    if purpose == PURPOSE_PASSWORD_RESET:
        return (
            f'Password reset code — {settings.SITE_NAME}',
            'password reset',
        )
    return (
        f'Login verification code — {settings.SITE_NAME}',
        'login verification',
    )


def send_email_otp(
    user,
    purpose: str,
    *,
    force: bool = False,
    extra_body: str = '',
    action_url: str = '',
    action_label: str = '',
) -> OtpResult:
    """
    Generate a 6-digit code, store hash in cache, email the user (branded HTML).
    Rate-limited per user+purpose unless force=True.
    action_url / action_label: optional CTA button (e.g. password reset link).
    extra_body: optional plain note (legacy); prefer action_url for links.
    """
    if purpose not in VALID_PURPOSES:
        return OtpResult(False, 'Invalid OTP purpose.')

    if not user or not getattr(user, 'email', None):
        return OtpResult(False, 'No email address on this account.')

    send_key = _send_key(purpose, user.pk)
    if not force and cache.get(send_key):
        wait = _resend_cooldown()
        return OtpResult(False, f'Please wait {wait} seconds before requesting a new code.')

    code = generate_code()
    ttl = _ttl_seconds()
    cache.set(
        _cache_key(purpose, user.pk),
        {
            'hash': _hash_code(code, purpose, user.pk),
            'attempts': 0,
            'created': timezone.now().isoformat(),
        },
        timeout=ttl,
    )
    cache.set(send_key, 1, timeout=_resend_cooldown())

    subject, label = _purpose_labels(purpose)
    minutes = max(1, ttl // 60)

    headings = {
        PURPOSE_LOGIN: 'Confirm it’s you',
        PURPOSE_WITHDRAW: 'Confirm your withdrawal',
        PURPOSE_PASSWORD_RESET: 'Reset your password',
    }
    badges = {
        PURPOSE_LOGIN: 'Login security',
        PURPOSE_WITHDRAW: 'Withdrawal security',
        PURPOSE_PASSWORD_RESET: 'Password reset',
    }
    intros = {
        PURPOSE_LOGIN: (
            'Enter this code on the login screen to finish signing in. '
            'If you did not try to log in, change your password immediately.'
        ),
        PURPOSE_WITHDRAW: (
            'Enter this code on the withdrawal page to authorize cashing out. '
            'If you did not start a withdrawal, secure your account now.'
        ),
        PURPOSE_PASSWORD_RESET: (
            'Enter this code to choose a new password. '
            'You can also use the button below if you prefer a one-click reset link.'
        ),
    }
    # Parse legacy "Or open this link" from extra_body if action_url not set
    if not action_url and extra_body:
        for line in extra_body.splitlines():
            line = line.strip()
            if line.startswith('http://') or line.startswith('https://'):
                action_url = line
                action_label = action_label or 'Reset password securely'
                break

    if purpose == PURPOSE_PASSWORD_RESET and action_url and not action_label:
        action_label = 'Reset password securely'
    elif purpose == PURPOSE_LOGIN and action_url and not action_label:
        action_label = 'Open login'
    elif action_url and not action_label:
        action_label = 'Open platform'

    try:
        from core.mail import send_otp_email
        send_otp_email(
            user,
            subject=subject,
            code=code,
            purpose_label=label,
            minutes=minutes,
            heading=headings.get(purpose, 'Your verification code'),
            intro=intros.get(purpose, ''),
            badge=badges.get(purpose, 'Security code'),
            action_url=action_url,
            action_label=action_label,
        )
    except Exception as exc:
        logger.exception('Failed to send email OTP purpose=%s user=%s', purpose, user.pk)
        cache.delete(_cache_key(purpose, user.pk))
        return OtpResult(False, f'Could not send email: {exc}')

    logger.info('Email OTP sent purpose=%s user=%s', purpose, user.email)
    result = OtpResult(True, f'We sent a 6-digit code to {user.email}.')
    # Dev / misconfigured SMTP: console backend never reaches the inbox
    console = 'console' in (getattr(settings, 'EMAIL_BACKEND', '') or '').lower()
    if console:
        logger.warning(
            'EMAIL_BACKEND is console — OTP was NOT emailed. Code for %s: %s',
            user.email, code,
        )
        if getattr(settings, 'DEBUG', False):
            result.message = (
                f'DEV MODE (email console): code for {user.email} is {code}. '
                f'Set real SMTP in .env to send real emails.'
            )
            result.code = code
    elif getattr(settings, 'DEBUG', False) and getattr(settings, 'EMAIL_OTP_RETURN_CODE_IN_DEBUG', False):
        result.code = code
    return result


def verify_email_otp(user, purpose: str, code: str) -> OtpResult:
    """Validate a submitted code. Consumes the OTP on success."""
    if purpose not in VALID_PURPOSES:
        return OtpResult(False, 'Invalid OTP purpose.')
    code = (code or '').strip().replace(' ', '')
    if not code.isdigit() or len(code) != 6:
        return OtpResult(False, 'Enter the 6-digit code from your email.')

    key = _cache_key(purpose, user.pk)
    payload = cache.get(key)
    if not payload:
        return OtpResult(False, 'Code expired or not sent. Request a new one.')

    attempts = int(payload.get('attempts') or 0) + 1
    if attempts > _max_attempts():
        cache.delete(key)
        return OtpResult(False, 'Too many attempts. Request a new code.')

    expected = payload.get('hash') or ''
    if not hmac_compare(expected, _hash_code(code, purpose, user.pk)):
        payload['attempts'] = attempts
        # keep remaining TTL approximately
        cache.set(key, payload, timeout=_ttl_seconds())
        left = _max_attempts() - attempts
        return OtpResult(False, f'Incorrect code. {left} attempt(s) left.')

    cache.delete(key)
    cache.delete(_send_key(purpose, user.pk))
    return OtpResult(True, 'Code verified.')


def hmac_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(str(a), str(b))


def clear_email_otp(user, purpose: str) -> None:
    cache.delete(_cache_key(purpose, user.pk))
    cache.delete(_send_key(purpose, user.pk))


def login_otp_required(user) -> bool:
    """
    Email OTP after password when:
    - settings.EMAIL_OTP_LOGIN_REQUIRED is True, and
    - user.email_otp_login is True, and
    - TOTP 2FA is not enabled (TOTP takes precedence for the primary step-up).
    """
    if not getattr(settings, 'EMAIL_OTP_LOGIN_REQUIRED', True):
        return False
    if getattr(user, 'two_factor_enabled', False):
        return False
    return bool(getattr(user, 'email_otp_login', True))


def user_needs_step_up(user) -> str:
    """
    Return 'totp', 'email', or '' for post-password login challenge.
    """
    if getattr(user, 'two_factor_enabled', False):
        return 'totp'
    if login_otp_required(user):
        return 'email'
    return ''
