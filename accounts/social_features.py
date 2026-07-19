"""Helpers for Google/X social features: badges, alerts, shares, digests."""
from __future__ import annotations

import logging
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger('accounts')


def mark_google_verified(user) -> None:
    """Google OAuth means the email was verified by Google."""
    fields = []
    if not user.email_verified:
        user.email_verified = True
        fields.append('email_verified')
    if not user.google_verified:
        user.google_verified = True
        fields.append('google_verified')
    if fields:
        user.save(update_fields=fields)


def set_login_method(user, method: str) -> None:
    method = (method or 'password')[:20]
    user.last_login_method = method
    user.save(update_fields=['last_login_method'])


def social_risk_signals(user) -> dict:
    """Soft identity signals for staff (not legal KYC)."""
    from accounts.models import SocialAccount

    accounts = list(user.social_accounts.all())
    by_provider = {a.provider: a for a in accounts}
    google = by_provider.get('google')
    x = by_provider.get('x')
    score = 0
    notes = []
    if user.google_verified or (google and user.email_verified):
        score += 35
        notes.append('Google-linked verified email')
    if x:
        score += 20
        notes.append(f'X linked (@{x.username or x.provider_user_id})')
    if user.profile_picture or user.avatar_url:
        score += 10
        notes.append('Has profile photo')
    if user.date_joined:
        days = (timezone.now() - user.date_joined).days
        if days >= 30:
            score += 15
            notes.append(f'Account age {days}d')
        elif days >= 7:
            score += 8
            notes.append(f'Account age {days}d')
    if user.is_kyc_verified:
        score += 30
        notes.append('KYC verified')
    return {
        'score': min(100, score),
        'notes': notes,
        'google_linked': bool(google),
        'x_linked': bool(x),
        'google_verified': bool(user.google_verified or user.email_verified),
        'x_handle': (x.username if x else '') or '',
    }


def send_login_alert_email(user, entry) -> None:
    """Email user about a successful login (especially new IP / suspicious)."""
    if not user or not getattr(user, 'login_alert_emails', True):
        return
    if not user.email or user.email.endswith(('@users.noreply.x.com', '@oauth.local')):
        return
    try:
        method = getattr(entry, 'auth_method', '') or user.last_login_method or 'password'
        loc = getattr(entry, 'location_display', None) or entry.ip_address or 'Unknown'
        subject = f'New login to {settings.SITE_NAME}'
        if entry.is_suspicious:
            subject = f'Security alert: suspicious login — {settings.SITE_NAME}'
        body = (
            f'Hi {user.get_full_name() or user.email},\n\n'
            f'We detected a login to your {settings.SITE_NAME} account.\n\n'
            f'Time: {timezone.localtime(entry.created_at):%Y-%m-%d %H:%M %Z}\n'
            f'Method: {method}\n'
            f'IP: {entry.ip_address or "—"}\n'
            f'Location: {loc}\n'
            f'Device: {(entry.user_agent or "")[:120]}\n'
        )
        if entry.is_suspicious:
            body += f'\nFlagged: {entry.suspicion_reason or "unusual activity"}\n'
            body += 'If this was not you, change your password and enable 2FA immediately.\n'
        body += f'\n— {settings.SITE_NAME}\n{settings.SITE_URL}\n'
        send_mail(
            subject, body, settings.DEFAULT_FROM_EMAIL, [user.email],
            fail_silently=True,
        )
    except Exception as exc:
        logger.info('Login alert email failed: %s', exc)


def x_share_intent_url(text: str, url: str = '') -> str:
    """Pre-filled X/Twitter intent URL (user must post manually)."""
    payload = text.strip()
    if url:
        payload = f'{payload} {url}'.strip()
    return 'https://twitter.com/intent/tweet?text=' + quote(payload)


def referral_share_text(user, request=None) -> tuple[str, str, str]:
    """Return (text, link, x_intent_url)."""
    site = getattr(settings, 'SITE_URL', '') or ''
    path = reverse('accounts:register') + f'?ref={user.referral_code}'
    if request is not None:
        link = request.build_absolute_uri(path)
    else:
        link = site.rstrip('/') + path
    text = (
        f'Join me on {settings.SITE_NAME} — invest smarter. '
        f'Use my code {user.referral_code}'
    )
    return text, link, x_share_intent_url(text, link)


def send_invite_email(from_user, to_email: str, personal_note: str = '') -> None:
    to_email = (to_email or '').strip().lower()
    if not to_email or '@' not in to_email:
        raise ValueError('Enter a valid email address.')
    _, link, _ = referral_share_text(from_user)
    note = (personal_note or '').strip()
    body = (
        f'{from_user.get_full_name() or from_user.email} invited you to {settings.SITE_NAME}.\n\n'
    )
    if note:
        body += f'Message: {note}\n\n'
    body += (
        f'Sign up with referral code {from_user.referral_code}:\n{link}\n\n'
        f'— {settings.SITE_NAME}\n'
    )
    send_mail(
        f'You are invited to {settings.SITE_NAME}',
        body,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=False,
    )


def send_weekly_digest(user) -> bool:
    """Simple portfolio digest email."""
    if not getattr(user, 'weekly_digest_emails', True):
        return False
    if not user.email or user.email.endswith(('@users.noreply.x.com', '@oauth.local')):
        return False
    try:
        from wallets.models import Wallet
        wallet, _ = Wallet.objects.get_or_create(user=user)
        subject = f'Your weekly summary — {settings.SITE_NAME}'
        body = (
            f'Hi {user.get_full_name() or user.email},\n\n'
            f'Weekly snapshot:\n'
            f'• Available: {wallet.available_balance}\n'
            f'• Total balance: {wallet.balance}\n'
            f'• Profit: {wallet.total_profit}\n'
            f'• Invested: {wallet.total_invested}\n'
            f'• Referral earnings: {user.referral_earnings}\n\n'
            f'Dashboard: {settings.SITE_URL.rstrip("/")}/dashboard/\n\n'
            f'— {settings.SITE_NAME}\n'
        )
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return True
    except Exception as exc:
        logger.info('Weekly digest failed for %s: %s', user.pk, exc)
        return False


def send_price_alert_email(user, alert, price) -> bool:
    if not getattr(user, 'email_alerts', True):
        return False
    if not user.email or user.email.endswith(('@users.noreply.x.com', '@oauth.local')):
        return False
    try:
        subject = f'Price alert: {alert.symbol} — {settings.SITE_NAME}'
        body = (
            f'Your alert for {alert.symbol} ({alert.label or alert.direction}) '
            f'hit target {alert.target_price}.\n'
            f'Last price seen: {price}\n\n'
            f'Manage alerts: {settings.SITE_URL.rstrip("/")}/alerts/\n'
        )
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
        return True
    except Exception as exc:
        logger.info('Price alert email failed: %s', exc)
        return False
