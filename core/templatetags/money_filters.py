"""Money + datetime formatting filters (global builtins)."""
from django import template
from django.utils import timezone as dj_tz

from core.datetime_display import format_datetime, format_datetime_location
from core.utils import format_money

register = template.Library()


def _places_from_arg(arg, default=2):
    if arg is None or arg == '':
        return default
    try:
        return int(arg)
    except (TypeError, ValueError):
        return default


@register.filter(name='money')
def money(value, places=2):
    """
    {{ amount|money }} → 1,234.56
    {{ amount|money:0 }} → 1,235
    {{ amount|money:4 }} → 1,234.5678
    """
    return format_money(value, _places_from_arg(places, 2), strip_trailing_zeros=False)


@register.filter(name='money_trim')
def money_trim(value, places=8):
    """Crypto-style: commas + trim trailing zeros. {{ amount|money_trim:8 }}"""
    return format_money(value, _places_from_arg(places, 8), strip_trailing_zeros=True)


@register.filter(name='money_crypto')
def money_crypto(value, symbol_and_places='USDT,8'):
    """
    {{ amount|money_crypto:"BTC,8" }} → 1.23456789 BTC
    """
    symbol = 'USDT'
    places = 8
    if symbol_and_places:
        parts = str(symbol_and_places).split(',')
        if parts:
            symbol = parts[0].strip() or symbol
        if len(parts) > 1:
            places = _places_from_arg(parts[1], 8)
    body = format_money(value, places, strip_trailing_zeros=True)
    return f'{body} {symbol}'.strip()


@register.filter(name='intcomma_dec')
def intcomma_dec(value, places=2):
    """Alias of money for readability."""
    return money(value, places)


def _tz_from_context(context=None):
    # filters don't get context unless takes_context — keep simple
    return None


@register.filter(name='when')
def when(value, mode='default'):
    """
    Accurate local date + time + timezone.
      {{ dt|when }}           → 18 Jul 2026 · 16:45 EAT
      {{ dt|when:"full" }}    → Sat, 18 Jul 2026 · 16:45:12 EAT
      {{ dt|when:"date" }}    → 18 Jul 2026
      {{ dt|when:"time" }}    → 16:45 EAT
    Uses the active timezone (browser/user preferred via TimezoneMiddleware).
    """
    if value is None:
        return '—'
    mode = (mode or 'default').lower()
    if mode == 'date':
        local = value
        if dj_tz.is_naive(local):
            local = dj_tz.make_aware(local, dj_tz.get_default_timezone())
        local = local.astimezone(dj_tz.get_current_timezone())
        return local.strftime('%d %b %Y')
    if mode == 'time':
        return format_datetime(value, with_seconds=False, with_tz=True, with_weekday=False).split('·')[-1].strip()
    if mode == 'full':
        return format_datetime(value, with_seconds=True, with_tz=True, with_weekday=True)
    return format_datetime(value, with_seconds=False, with_tz=True, with_weekday=False)


@register.filter(name='when_at')
def when_at(value, location=''):
    """
    Date/time + access location.
      {{ login.created_at|when_at:login.location_display }}
    """
    return format_datetime_location(value, location or '')


@register.simple_tag(takes_context=True)
def now_local(context, fmt='full'):
    """Current time in the user's timezone."""
    return when(dj_tz.now(), fmt)
