"""Real crypto logo badges for Django templates (local SVG files)."""
from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

BRAND = {
    'BTC': ('#F7931A', 'B', 'btc'),
    'ETH': ('#627EEA', 'E', 'eth'),
    'USDT': ('#26A17B', 'T', 'usdt'),
    'USDC': ('#2775CA', 'C', 'usdc'),
    'BNB': ('#F3BA2F', 'N', 'bnb'),
    'LTC': ('#345D9D', 'L', 'ltc'),
    'TRX': ('#FF0013', 'R', 'trx'),
    'XRP': ('#23292F', 'X', 'xrp'),
    'SOL': ('#9945FF', 'S', 'sol'),
    'DOGE': ('#C2A633', 'D', 'doge'),
    'MATIC': ('#8247E5', 'M', 'matic'),
    'POL': ('#8247E5', 'P', 'matic'),
    'AVAX': ('#E84142', 'A', 'avax'),
    'ADA': ('#0033AD', 'A', 'ada'),
    'DOT': ('#E6007A', 'D', 'dot'),
    'LINK': ('#2A5ADA', 'K', 'link'),
    'DAI': ('#F5AC37', 'D', 'dai'),
    'BUSD': ('#F0B90B', 'B', 'bnb'),
    'USD': ('#16A34A', '$', 'usdc'),
    'EUR': ('#2563EB', '€', 'usdc'),
    'GBP': ('#7C3AED', '£', 'usdc'),
    'UGX': ('#DC2626', 'U', 'usdc'),
}

LOCAL_SLUGS = {
    'btc', 'eth', 'usdt', 'usdc', 'bnb', 'ltc', 'trx', 'sol',
    'doge', 'matic', 'avax', 'ada', 'dot', 'link', 'dai', 'xrp',
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
        color, letter, slug = BRAND[base]
        return base, color, letter, slug
    letter = (base[:1] or '?').upper()
    return base, '#64748B', letter, base.lower()


_SIZE_PX = {'xs': 20, 'sm': 26, 'md': 32, 'lg': 40}


def _logo_url(slug: str) -> str:
    if slug not in LOCAL_SLUGS:
        return ''
    try:
        return staticfiles_storage.url(f'img/crypto/{slug}.svg')
    except Exception:
        return f'/static/img/crypto/{slug}.svg'


@register.simple_tag
def crypto_icon(symbol, size='sm'):
    """Real crypto logo badge (local SVG) with letter fallback."""
    if not symbol:
        return ''
    base, color, letter, slug = _brand(str(symbol))
    size = size if size in _SIZE_PX else 'sm'
    px = _SIZE_PX[size]
    font = max(10, int(px * 0.48))
    url = _logo_url(slug)
    if url:
        return format_html(
            '<span class="ci-crypto-icon ci-crypto-logo" title="{}" aria-label="{}" '
            'style="display:inline-flex;align-items:center;justify-content:center;'
            'width:{}px;height:{}px;min-width:{}px;min-height:{}px;border-radius:50%;'
            'overflow:hidden;background:#fff;vertical-align:middle;box-sizing:border-box;'
            'flex-shrink:0;box-shadow:0 2px 6px rgba(0,0,0,.3);'
            'border:1.5px solid rgba(255,255,255,.2)">'
            '<img src="{}" alt="{}" width="{}" height="{}" '
            'style="width:100%;height:100%;object-fit:cover;display:block" loading="lazy" /></span>',
            str(symbol),
            str(symbol),
            px,
            px,
            px,
            px,
            url,
            str(symbol),
            px,
            px,
        )
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
