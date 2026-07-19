"""Render offline crypto brand badges in Django templates."""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

BRAND = {
    'BTC': ('#F7931A', '₿'),
    'ETH': ('#627EEA', 'Ξ'),
    'USDT': ('#26A17B', '₮'),
    'USDC': ('#2775CA', '$'),
    'BNB': ('#F3BA2F', 'B'),
    'LTC': ('#345D9D', 'Ł'),
    'TRX': ('#FF0013', 'T'),
    'XRP': ('#23292F', 'X'),
    'SOL': ('#9945FF', 'S'),
    'DOGE': ('#C2A633', 'Ð'),
    'MATIC': ('#8247E5', 'M'),
    'POL': ('#8247E5', 'P'),
    'AVAX': ('#E84142', 'A'),
    'ADA': ('#0033AD', '₳'),
    'DOT': ('#E6007A', '●'),
    'LINK': ('#2A5ADA', '⬡'),
    'DAI': ('#F5AC37', '◈'),
    'BUSD': ('#F0B90B', 'B'),
    'TON': ('#0098EA', '◆'),
    'USD': ('#16A34A', '$'),
    'EUR': ('#2563EB', '€'),
    'GBP': ('#7C3AED', '£'),
    'UGX': ('#DC2626', 'U'),
}


def _base(symbol: str) -> str:
    if not symbol:
        return ''
    upper = str(symbol).strip().upper()
    for key in sorted(BRAND.keys(), key=len, reverse=True):
        if upper == key or upper.startswith(f'{key}_') or upper.startswith(f'{key}-') or upper.startswith(f'{key} '):
            return key
    return upper.split('_')[0].split('-')[0].split()[0]


def _brand(symbol: str):
    base = _base(symbol)
    if base in BRAND:
        return base, BRAND[base][0], BRAND[base][1]
    letter = (base[:1] or '?').upper()
    return base, '#64748B', letter


@register.simple_tag
def crypto_icon(symbol, size='sm'):
    """Colored circular crypto badge (offline). size: xs|sm|md|lg"""
    if not symbol:
        return ''
    base, color, letter = _brand(str(symbol))
    size = size if size in ('xs', 'sm', 'md', 'lg') else 'sm'
    return format_html(
        '<span class="ci-crypto-icon ci-crypto-{}" style="background:{}" title="{}" aria-label="{}">'
        '<span class="ci-crypto-letter">{}</span></span>',
        size,
        color,
        str(symbol),
        str(symbol),
        letter,
    )


@register.simple_tag
def crypto_label(symbol, size='sm', network=''):
    """Icon + symbol text row."""
    if not symbol:
        return mark_safe('—')
    icon = crypto_icon(symbol, size=size)
    if network:
        return format_html(
            '<span class="ci-crypto-label">{} <span class="ci-crypto-meta">'
            '<span class="ci-crypto-sym">{}</span>'
            '<span class="ci-crypto-net">{}</span></span></span>',
            icon,
            str(symbol),
            str(network),
        )
    return format_html(
        '<span class="ci-crypto-label">{} <span class="ci-crypto-sym">{}</span></span>',
        icon,
        str(symbol),
    )
