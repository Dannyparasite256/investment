"""Render offline crypto brand badges in Django templates."""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# ASCII letters only — guaranteed to render on all devices
BRAND = {
    'BTC': ('#F7931A', 'B'),
    'ETH': ('#627EEA', 'E'),
    'USDT': ('#26A17B', 'T'),
    'USDC': ('#2775CA', 'C'),
    'BNB': ('#F3BA2F', 'N'),
    'LTC': ('#345D9D', 'L'),
    'TRX': ('#FF0013', 'R'),
    'XRP': ('#23292F', 'X'),
    'SOL': ('#9945FF', 'S'),
    'DOGE': ('#C2A633', 'D'),
    'MATIC': ('#8247E5', 'M'),
    'POL': ('#8247E5', 'P'),
    'AVAX': ('#E84142', 'A'),
    'ADA': ('#0033AD', 'A'),
    'DOT': ('#E6007A', 'D'),
    'LINK': ('#2A5ADA', 'K'),
    'DAI': ('#F5AC37', 'D'),
    'BUSD': ('#F0B90B', 'B'),
    'TON': ('#0098EA', 'T'),
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


_SIZE_PX = {'xs': 20, 'sm': 26, 'md': 32, 'lg': 40}


@register.simple_tag
def crypto_icon(symbol, size='sm'):
    """Colored circular crypto badge (offline). size: xs|sm|md|lg"""
    if not symbol:
        return ''
    base, color, letter = _brand(str(symbol))
    size = size if size in _SIZE_PX else 'sm'
    px = _SIZE_PX[size]
    font = max(10, int(px * 0.48))
    return format_html(
        '<span class="ci-crypto-icon" title="{}" aria-label="{}" '
        'style="display:inline-flex;align-items:center;justify-content:center;'
        'width:{}px;height:{}px;min-width:{}px;min-height:{}px;border-radius:50%;'
        'background:{};color:#fff;font-weight:800;font-size:{}px;line-height:1;'
        'box-shadow:0 2px 6px rgba(0,0,0,.35);border:2px solid rgba(255,255,255,.25);'
        'vertical-align:middle;box-sizing:border-box;flex-shrink:0">{}</span>',
        str(symbol),
        str(symbol),
        px,
        px,
        px,
        px,
        color,
        font,
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
