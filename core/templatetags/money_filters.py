"""Money formatting filters — always use thousands separators (commas)."""
from decimal import Decimal, InvalidOperation

from django import template

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
