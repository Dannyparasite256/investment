"""
Branded HTML email helpers for CryptoInvest.

Matches site fonts (Inter / Manrope) and indigo–violet gradient buttons.
Always send multipart: plain text + HTML.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from html import escape
from typing import Iterable, Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger('core')


def site_name() -> str:
    return getattr(settings, 'SITE_NAME', 'CryptoInvest') or 'CryptoInvest'


def site_url() -> str:
    return (getattr(settings, 'SITE_URL', '') or '').rstrip('/')


def _base_context(**extra):
    ctx = {
        'site_name': site_name(),
        'site_url': site_url(),
        'year': timezone.now().year if timezone.is_aware(timezone.now()) else datetime.utcnow().year,
    }
    ctx.update(extra)
    return ctx


def _plain_from_html(html: str) -> str:
    """Rough plain-text fallback when no explicit text is provided."""
    text = re.sub(r'(?is)<(script|style).*?>.*?</\1>', '', html)
    text = re.sub(r'(?i)<br\s*/?>', '\n', text)
    text = re.sub(r'(?i)</p>', '\n\n', text)
    text = re.sub(r'(?i)</tr>', '\n', text)
    text = re.sub(r'(?i)</h[1-6]>', '\n\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def send_branded_email(
    *,
    to: str | list[str],
    subject: str,
    text_body: str,
    html_body: str,
    fail_silently: bool = False,
) -> bool:
    recipients = [to] if isinstance(to, str) else list(to)
    recipients = [r for r in recipients if r]
    if not recipients:
        return False
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.exception('Branded email failed to %s: %s', recipients, exc)
        if not fail_silently:
            raise
        return False


def render_otp_email(
    *,
    name: str,
    code: str,
    purpose_label: str,
    minutes: int,
    heading: str = '',
    intro: str = '',
    badge: str = 'Security code',
    action_url: str = '',
    action_label: str = '',
    subject_line: str = '',
) -> tuple[str, str]:
    """Return (html, plain_text) for OTP-style emails."""
    ctx = _base_context(
        name=name or 'there',
        code=code,
        purpose_label=purpose_label,
        minutes=minutes,
        heading=heading or f'Your {purpose_label} code',
        intro=intro or (
            f'Use this one-time code for {purpose_label}. '
            f'For your security, never share it with anyone — including support staff.'
        ),
        badge=badge,
        action_url=action_url,
        action_label=action_label,
        subject_line=subject_line or f'{purpose_label.title()} code',
        preheader=f'Your code is {code}. Expires in {minutes} minutes.',
    )
    html = render_to_string('emails/otp.html', ctx)
    plain = (
        f'Hi {ctx["name"]},\n\n'
        f'Your {purpose_label} code is: {code}\n\n'
        f'This code expires in {minutes} minutes.\n'
    )
    if action_url:
        plain += f'\n{action_label or "Open link"}:\n{action_url}\n'
    plain += (
        f'\nIf you did not request this, ignore this email and secure your account.\n'
        f'\n— {site_name()}\n'
    )
    return html, plain


def render_action_email(
    *,
    name: str,
    heading: str,
    paragraphs: Iterable[str],
    action_url: str = '',
    action_label: str = 'Continue',
    badge: str = '',
    secondary_note: str = '',
    preheader: str = '',
    subject_line: str = '',
) -> tuple[str, str]:
    paras = [p for p in paragraphs if p]
    ctx = _base_context(
        name=name or 'there',
        heading=heading,
        paragraphs=paras,
        action_url=action_url,
        action_label=action_label,
        badge=badge,
        secondary_note=secondary_note,
        preheader=preheader or heading,
        subject_line=subject_line or heading,
    )
    html = render_to_string('emails/action.html', ctx)
    plain_parts = [f'Hi {ctx["name"]},', ''] + paras + ['']
    if action_url:
        plain_parts.append(f'{action_label}: {action_url}')
        plain_parts.append('')
    if secondary_note:
        plain_parts.append(secondary_note)
        plain_parts.append('')
    plain_parts.append(f'— {site_name()}')
    return html, '\n'.join(plain_parts)


def send_otp_email(
    user,
    *,
    subject: str,
    code: str,
    purpose_label: str,
    minutes: int,
    heading: str = '',
    intro: str = '',
    badge: str = 'Security code',
    action_url: str = '',
    action_label: str = '',
) -> None:
    name = ''
    if hasattr(user, 'get_full_name'):
        name = (user.get_full_name() or '').strip()
    if not name:
        name = getattr(user, 'email', '') or 'there'
    html, plain = render_otp_email(
        name=name,
        code=code,
        purpose_label=purpose_label,
        minutes=minutes,
        heading=heading,
        intro=intro,
        badge=badge,
        action_url=action_url,
        action_label=action_label,
        subject_line=subject,
    )
    send_branded_email(to=user.email, subject=subject, text_body=plain, html_body=html)


def send_action_email(
    user,
    *,
    subject: str,
    heading: str,
    paragraphs: list[str],
    action_url: str = '',
    action_label: str = 'Continue',
    badge: str = '',
    secondary_note: str = '',
    fail_silently: bool = False,
) -> bool:
    name = ''
    if user and hasattr(user, 'get_full_name'):
        name = (user.get_full_name() or '').strip()
    if not name and user:
        name = getattr(user, 'email', '') or 'there'
    to = getattr(user, 'email', None) if user else None
    if not to:
        return False
    html, plain = render_action_email(
        name=name,
        heading=heading,
        paragraphs=paragraphs,
        action_url=action_url,
        action_label=action_label,
        badge=badge,
        secondary_note=secondary_note,
        preheader=heading,
        subject_line=subject,
    )
    return send_branded_email(
        to=to, subject=subject, text_body=plain, html_body=html, fail_silently=fail_silently,
    )


def wrap_plain_as_branded(subject: str, body: str, *, name: str = 'there', action_url: str = '', action_label: str = '') -> tuple[str, str]:
    """Turn a plain-text body into branded HTML + text."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', body.strip()) if p.strip()]
    if not paragraphs:
        paragraphs = [body.strip()]
    return render_action_email(
        name=name,
        heading=subject.split('—')[0].strip() if '—' in subject else subject,
        paragraphs=paragraphs,
        action_url=action_url,
        action_label=action_label or 'Open platform',
        badge='Notification',
        subject_line=subject,
    )
