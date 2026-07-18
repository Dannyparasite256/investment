"""Shared utility helpers."""
import logging
from decimal import Decimal, ROUND_DOWN

from django.contrib.auth import get_user_model

from core.models import AuditLog

logger = logging.getLogger('audit')
User = get_user_model()


def get_client_ip(request):
    if hasattr(request, 'client_ip') and request.client_ip:
        return request.client_ip
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def create_audit_log(
    request=None,
    user=None,
    action=AuditLog.Action.OTHER,
    message='',
    object_type='',
    object_id='',
    extra=None,
):
    """Persist an audit log entry and mirror to file logger."""
    ip = None
    ua = ''
    path = ''
    method = ''
    if request is not None:
        ip = get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')[:500]
        path = request.path[:512]
        method = request.method
        if user is None and getattr(request, 'user', None) and request.user.is_authenticated:
            user = request.user

    log = AuditLog.objects.create(
        user=user if user and getattr(user, 'is_authenticated', False) else None,
        action=action,
        ip_address=ip,
        user_agent=ua,
        path=path,
        method=method,
        object_type=object_type,
        object_id=str(object_id) if object_id else '',
        message=message,
        extra=extra or {},
    )
    logger.info(
        'AUDIT action=%s user=%s ip=%s msg=%s',
        action,
        getattr(user, 'email', 'anon'),
        ip,
        message,
    )
    return log


def quantize_amount(value, places=8):
    """Round decimal amount down to given places."""
    if value is None:
        return Decimal('0')
    q = Decimal('1').scaleb(-places)
    return Decimal(str(value)).quantize(q, rounding=ROUND_DOWN)


def format_crypto(amount, symbol='USDT', places=8):
    amount = quantize_amount(amount, places)
    return f'{amount:.{places}f} {symbol}'.rstrip('0').rstrip('.') + f' {symbol}' if False else f'{amount} {symbol}'
