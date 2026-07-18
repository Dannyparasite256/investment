"""User-facing feature views: portfolio, VIP, watchlist, alerts, tour, language, affiliate."""
import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.models import ActivityEvent
from core.models import SiteConfiguration
from core.platform_models import (
    PriceAlert,
    TradingSignal,
    WatchlistItem,
)
from core.portfolio import chart_series, compute_equity, record_snapshot
from core.vip import get_user_tier, refresh_user_vip_context
from markets.pairs import FOREX_CATEGORIES, all_pairs


@login_required
def portfolio_performance(request):
    days = int(request.GET.get('days') or 30)
    record_snapshot(request.user)
    labels, equity, profit = chart_series(request.user, days=days)
    equity_now = compute_equity(request.user)
    vip = refresh_user_vip_context(request.user)
    return render(request, 'core/portfolio.html', {
        'days': days,
        'equity_now': equity_now,
        'vip': vip,
        'chart_labels': json.dumps(labels),
        'chart_equity': json.dumps(equity),
        'chart_profit': json.dumps(profit),
        'disclaimer': SiteConfiguration.get_solo().risk_disclaimer,
    })


@login_required
def vip_status(request):
    from core.platform_models import VIPTier
    from core.vip import decorate_tier, refresh_user_vip_context

    ctx = refresh_user_vip_context(request.user)
    tiers = [decorate_tier(t) for t in VIPTier.objects.filter(is_active=True)]
    return render(request, 'core/vip_status.html', {
        **ctx,
        'tiers': tiers,
        'progress_pct': ctx.get('vip_progress_pct', 100),
        'remaining': ctx.get('vip_remaining', 0),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def watchlist_view(request):
    if request.method == 'POST':
        symbol = (request.POST.get('symbol') or '').strip()
        label = (request.POST.get('label') or '').strip()
        if symbol:
            WatchlistItem.objects.get_or_create(
                user=request.user, symbol=symbol,
                defaults={'label': label or symbol},
            )
            messages.success(request, 'Added to watchlist.')
        return redirect('core:watchlist')
    items = WatchlistItem.objects.filter(user=request.user)
    pairs = all_pairs()
    return render(request, 'core/watchlist.html', {'items': items, 'pairs': pairs})


@login_required
@require_POST
def watchlist_delete(request, pk):
    WatchlistItem.objects.filter(pk=pk, user=request.user).delete()
    messages.info(request, 'Removed from watchlist.')
    return redirect('core:watchlist')


@login_required
@require_http_methods(['GET', 'POST'])
def price_alerts_view(request):
    if request.method == 'POST':
        PriceAlert.objects.create(
            user=request.user,
            symbol=request.POST.get('symbol', 'FX:EURUSD'),
            label=request.POST.get('label', ''),
            target_price=Decimal(request.POST.get('target_price') or '0'),
            direction=request.POST.get('direction', 'above'),
        )
        messages.success(request, 'Price alert created.')
        return redirect('core:alerts')
    alerts = PriceAlert.objects.filter(user=request.user)
    return render(request, 'core/alerts.html', {
        'alerts': alerts,
        'pairs': all_pairs(),
    })


@login_required
@require_POST
def alert_delete(request, pk):
    PriceAlert.objects.filter(pk=pk, user=request.user).delete()
    return redirect('core:alerts')


@login_required
def activity_timeline(request):
    events = ActivityEvent.objects.filter(user=request.user)[:100]
    return render(request, 'core/activity.html', {'events': events})


@login_required
def signals_list(request):
    signals = TradingSignal.objects.filter(is_published=True)[:50]
    return render(request, 'core/signals.html', {
        'signals': signals,
        'disclaimer': SiteConfiguration.get_solo().risk_disclaimer,
    })


@login_required
@require_POST
def complete_tour(request):
    request.user.tour_completed = True
    request.user.save(update_fields=['tour_completed'])
    return JsonResponse({'ok': True})


@require_GET
def set_language(request):
    lang = request.GET.get('lang', 'en')
    allowed = {c[0] for c in getattr(__import__('django.conf', fromlist=['settings']).settings, 'LANGUAGES', [('en', 'English')])}
    if lang not in allowed:
        lang = 'en'
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    response = redirect(next_url)
    response.set_cookie('django_language', lang, max_age=365 * 24 * 3600, samesite='Lax')
    if request.user.is_authenticated:
        request.user.preferred_language = lang
        request.user.save(update_fields=['preferred_language'])
    return response


@login_required
def affiliate_landing_preview(request):
    """Affiliate-style landing content for the user's referral link."""
    link = request.build_absolute_uri(f"/accounts/register/?ref={request.user.referral_code}")
    return render(request, 'core/affiliate.html', {
        'referral_link': link,
        'code': request.user.referral_code,
    })


def manifest_json(request):
    """PWA web app manifest."""
    from django.conf import settings as dj
    data = {
        'name': getattr(dj, 'SITE_NAME', 'CryptoInvest'),
        'short_name': 'CryptoInvest',
        'start_url': '/dashboard/',
        'display': 'standalone',
        'background_color': '#060816',
        'theme_color': '#7C3AED',
        'description': 'Premium cryptocurrency investment platform',
        'icons': [
            {'src': '/static/img/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
            {'src': '/static/img/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
        ],
    }
    return JsonResponse(data)


def service_worker(request):
    js = """
const CACHE = 'ci-shell-v1';
const ASSETS = ['/dashboard/', '/static/css/app.css', '/static/js/app.js'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request)).then(r => r || caches.match('/dashboard/'))
  );
});
"""
    return HttpResponse(js, content_type='application/javascript')
