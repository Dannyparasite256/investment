"""Forex & market chart views."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET

from markets.pairs import CHART_STYLES, FOREX_CATEGORIES, INTERVALS, all_pairs, default_pair, find_pair


@login_required
@require_GET
def market_overview(request):
    """All forex categories with quick-open chart links."""
    return render(request, 'markets/overview.html', {
        'categories': FOREX_CATEGORIES,
        'chart_styles': CHART_STYLES,
        'default_symbol': default_pair()['symbol'],
    })


@login_required
@require_GET
def market_chart(request):
    """
    Full TradingView advanced chart.

    Query params:
      symbol  — e.g. FX:EURUSD
      style   — candlestick / bars / line / area / heikin / hollow
      interval — 1, 5, 15, 60, D, …
    """
    symbol = request.GET.get('symbol') or default_pair()['symbol']
    style = request.GET.get('style') or '1'
    interval = request.GET.get('interval') or '60'

    valid_styles = {s['id'] for s in CHART_STYLES}
    valid_intervals = {i['id'] for i in INTERVALS}
    if style not in valid_styles:
        style = '1'
    if interval not in valid_intervals:
        interval = '60'

    pair = find_pair(symbol) or {
        'symbol': symbol,
        'name': symbol.replace('FX:', '').replace('BINANCE:', ''),
        'base': '',
        'quote': '',
        'category': 'custom',
        'category_label': 'Custom',
    }

    # Theme from cookie
    theme = request.COOKIES.get('theme', getattr(request, 'theme', 'dark'))
    if theme not in ('dark', 'light'):
        theme = 'dark'

    return render(request, 'markets/chart.html', {
        'pair': pair,
        'symbol': symbol,
        'style': style,
        'interval': interval,
        'chart_styles': CHART_STYLES,
        'intervals': INTERVALS,
        'categories': FOREX_CATEGORIES,
        'all_pairs': all_pairs(),
        'tv_theme': 'dark' if theme == 'dark' else 'light',
    })
