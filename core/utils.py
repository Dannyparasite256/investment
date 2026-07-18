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


def format_money(value, places=2, strip_trailing_zeros=False):
    """
    Format a number with thousands separators (commas).
    Examples: 1234.5 → 1,234.50 ;  64424 → 64,424.00 ; UGX style places=0 → 5,290,075,005
    """
    if value is None or value == '':
        value = 0
    try:
        amount = Decimal(str(value).replace(',', '').strip())
    except Exception:
        return str(value)

    places = int(places) if places is not None else 2
    places = max(0, min(12, places))

    if places == 0:
        # half-up style for whole units (UGX etc.)
        from decimal import ROUND_HALF_UP
        amount = amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        neg = amount < 0
        n = abs(int(amount))
        s = f'{n:,}'
        return f'-{s}' if neg else s

    amount = quantize_amount(amount, places)
    neg = amount < 0
    amount = abs(amount)
    raw = f'{amount:.{places}f}'
    whole, _, frac = raw.partition('.')
    whole = f'{int(whole):,}'
    if strip_trailing_zeros:
        frac = frac.rstrip('0')
        out = f'{whole}.{frac}' if frac else whole
    else:
        out = f'{whole}.{frac}'
    return f'-{out}' if neg else out


def format_crypto(amount, symbol='USDT', places=8):
    amount = quantize_amount(amount, places)
    body = format_money(amount, places, strip_trailing_zeros=True)
    return f'{body} {symbol}'
