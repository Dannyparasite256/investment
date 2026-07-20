"""Unified email + optional SMS + webhook fan-out for platform events."""
import hashlib
import hmac
import json
import logging
from urllib import request as urlrequest

from django.conf import settings
from django.core.mail import send_mail

from notifications.models import Notification, notify

logger = logging.getLogger('core')


def send_platform_email(user, subject, body, *, action_url='', action_label=''):
    if not user or not getattr(user, 'email', None):
        return False
    try:
        from core.mail import send_action_email, site_url
        paragraphs = [p.strip() for p in body.replace('\r\n', '\n').split('\n\n') if p.strip()]
        if not paragraphs:
            paragraphs = [body.strip() or subject]
        # Prefer explicit CTA; fall back to site home for engagement
        url = action_url or site_url()
        if url and url.startswith('/'):
            base = site_url()
            url = f'{base}{url}' if base else url
        label = action_label or (f'Open {getattr(settings, "SITE_NAME", "platform")}' if url else '')
        return send_action_email(
            user,
            subject=subject,
            heading=subject.split('—')[0].strip() if '—' in subject else subject,
            paragraphs=paragraphs,
            action_url=url,
            action_label=label,
            badge='Update',
            fail_silently=True,
        )
    except Exception as exc:
        logger.warning('Email failed for %s: %s', user.email, exc)
        try:
            send_mail(
                subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True,
            )
            return True
        except Exception:
            return False


def send_sms(phone: str, message: str):
    """Optional SMS via Twilio-style env config. No-op if not configured."""
    account = getattr(settings, 'TWILIO_ACCOUNT_SID', '') or ''
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '') or ''
    from_num = getattr(settings, 'TWILIO_FROM_NUMBER', '') or ''
    if not (account and token and from_num and phone):
        logger.debug('SMS skipped (not configured or no phone)')
        return False
    try:
        # Lazy optional dependency
        from twilio.rest import Client  # type: ignore
        client = Client(account, token)
        client.messages.create(body=message[:500], from_=from_num, to=phone)
        return True
    except Exception as exc:
        logger.warning('SMS failed: %s', exc)
        return False


def dispatch_webhooks(event: str, payload: dict):
    try:
        from core.platform_models import WebhookEndpoint
    except Exception:
        return
    for ep in WebhookEndpoint.objects.filter(is_active=True):
        if event not in ep.event_list():
            continue
        body = json.dumps({'event': event, 'data': payload}).encode('utf-8')
        headers = {'Content-Type': 'application/json', 'User-Agent': 'CryptoInvest-Webhook/1.0'}
        if ep.secret:
            sig = hmac.new(ep.secret.encode(), body, hashlib.sha256).hexdigest()
            headers['X-Signature'] = sig
        try:
            req = urlrequest.Request(ep.url, data=body, headers=headers, method='POST')
            urlrequest.urlopen(req, timeout=8)
        except Exception as exc:
            logger.warning('Webhook %s failed: %s', ep.url, exc)


def alert_user(
    user,
    title,
    message,
    *,
    level=Notification.Level.INFO,
    category=Notification.Category.SYSTEM,
    link='',
    email=True,
    sms=False,
    event_name='',
    event_payload=None,
    action_label='',
):
    """In-app notify + optional branded email/SMS + webhooks."""
    n = notify(user, title, message, level=level, category=category, link=link)
    if email:
        send_platform_email(
            user,
            f'{settings.SITE_NAME}: {title}',
            message,
            action_url=link or '',
            action_label=action_label or ('Open app' if link else ''),
        )
    if sms and getattr(user, 'phone', None):
        send_sms(user.phone, f'{title}: {message}'[:160])
    if event_name:
        dispatch_webhooks(event_name, event_payload or {'user': user.email, 'title': title})
    return n
