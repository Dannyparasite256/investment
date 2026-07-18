"""Landing page, dashboard, theme toggle."""
import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from investments.models import Earning, Investment, InvestmentPlan
from notifications.models import Notification
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.models import Wallet, WalletLedger


def home(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    plans = InvestmentPlan.objects.filter(status=InvestmentPlan.Status.ACTIVE)[:6]
    return render(request, 'core/home.html', {'plans': plans})


@login_required
def dashboard(request):
    user = request.user
    from wallets.display import (
        convert_from_usd,
        format_amount_for_code,
        get_currency_meta,
        get_default_display_code,
        user_display_context,
    )

    # Soft-refresh live prices (free APIs, cached ~2 min)
    try:
        from core.price_feed import ensure_fresh_prices, get_ticker_snapshot
        ensure_fresh_prices()
        market_ticker = get_ticker_snapshot()
    except Exception:
        market_ticker = {}
    wallet, _ = Wallet.objects.get_or_create(user=user)

    # Permanent display currency for this user (DB / session / cookie)
    display_code = get_default_display_code(user, request=request)
    currency_meta = get_currency_meta(display_code)

    active_investments = Investment.objects.filter(user=user, status=Investment.Status.ACTIVE)
    active_count = active_investments.count()
    # Platform USD-equivalent capital (source of truth)
    active_value_usd = active_investments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    active_capital_display = format_amount_for_code(active_value_usd, display_code)

    pending_qs = Deposit.objects.filter(
        user=user,
        status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION],
    ).select_related('cryptocurrency')
    pending_deposits_count = pending_qs.count()
    # Convert pending deposits to platform USD, then to display currency
    pending_usd = Decimal('0')
    for dep in pending_qs:
        if getattr(dep, 'credit_amount', None) is not None:
            pending_usd += Decimal(str(dep.credit_amount))
            continue
        amt = Decimal(str(dep.amount or 0))
        price = getattr(getattr(dep, 'cryptocurrency', None), 'usd_price', None) or Decimal('0')
        pending_usd += (amt * Decimal(str(price))) if price and price > 0 else amt
    pending_deposits_display = format_amount_for_code(pending_usd, display_code)

    pending_withdrawals = Withdrawal.objects.filter(
        user=user,
        status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.PROCESSING],
    ).aggregate(total=Sum('amount'), count=Count('id'))
    pending_wd_usd = pending_withdrawals['total'] or Decimal('0')
    pending_withdrawals_display = format_amount_for_code(pending_wd_usd, display_code)

    recent_tx = Transaction.objects.filter(user=user)[:10]
    # Attach display amounts for list rows (platform USD → selected currency)
    for tx in recent_tx:
        # Deposit rows may store crypto units; investment/profit/withdrawal are platform USD
        if tx.tx_type == Transaction.TxType.DEPOSIT and tx.currency and tx.currency.upper() not in ('USD', ''):
            # Prefer metadata platform credit when present
            meta = tx.metadata or {}
            if meta.get('platform_credit') is not None:
                tx.amount_display = format_amount_for_code(meta.get('platform_credit'), display_code)
            else:
                tx.amount_display = format_amount_for_code(tx.amount, display_code)
        else:
            tx.amount_display = format_amount_for_code(tx.amount, display_code)

    recent_earnings = Earning.objects.filter(user=user).select_related('investment__plan')[:8]
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    plans = InvestmentPlan.objects.filter(status=InvestmentPlan.Status.ACTIVE, is_featured=True)[:3]
    addresses = user.wallet_addresses.select_related('cryptocurrency')[:5]

    # Chart data in display currency so it matches the rest of the UI
    chart_earnings = list(
        Earning.objects.filter(user=user)
        .order_by('created_at')
        .values_list('created_at', 'amount')[:30]
    )
    chart_labels = [e[0].strftime('%b %d') for e in chart_earnings]
    chart_values = [float(convert_from_usd(e[1], display_code)) for e in chart_earnings]

    # Portfolio composition (relative shares — use USD for proportions)
    portfolio_labels = ['Available', 'Active Investments', 'Locked']
    portfolio_values = [
        float(wallet.available_balance),
        float(active_value_usd),
        float(wallet.locked_balance),
    ]

    active_list = list(active_investments.select_related('plan')[:5])
    for inv in active_list:
        inv.amount_display = format_amount_for_code(inv.amount, display_code)
        inv.earned_display = format_amount_for_code(inv.total_earned, display_code)

    context = {
        'wallet': wallet,
        'total_portfolio': wallet.balance + active_value_usd,
        'available_balance': wallet.available_balance,
        'active_investments_count': active_count,
        # Raw platform total kept for debugging/API parity; UI must use *_display
        'active_investments_value': active_value_usd,
        'active_capital_display': active_capital_display,
        'pending_deposits_total': pending_usd,
        'pending_deposits_display': pending_deposits_display,
        'pending_deposits_count': pending_deposits_count,
        'pending_withdrawals_total': pending_wd_usd,
        'pending_withdrawals_display': pending_withdrawals_display,
        'pending_withdrawals_count': pending_withdrawals['count'] or 0,
        'total_profit': wallet.total_profit,
        'referral_earnings': user.referral_earnings,
        'recent_tx': recent_tx,
        'recent_earnings': recent_earnings,
        'notifications': notifications,
        'plans': plans,
        'addresses': addresses,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'portfolio_labels': json.dumps(portfolio_labels),
        'portfolio_values': json.dumps(portfolio_values),
        'active_investments_list': active_list,
        'market_ticker': market_ticker,
        'display_currency': display_code,
        'currency_symbol': currency_meta['symbol'],
        'currency_decimals': currency_meta['decimals'],
    }
    # Portfolio equity curve + VIP
    try:
        from core.portfolio import chart_series, record_snapshot
        from core.vip import refresh_user_vip_context
        record_snapshot(user)
        elabels, eequity, eprofit = chart_series(user, days=30)
        # Convert equity series to display currency for the chart
        eequity_disp = [float(convert_from_usd(v, display_code)) for v in eequity]
        context['equity_labels'] = json.dumps(elabels)
        context['equity_values'] = json.dumps(eequity_disp)
        context['vip_ctx'] = refresh_user_vip_context(user)
    except Exception:
        context['equity_labels'] = '[]'
        context['equity_values'] = '[]'
        context['vip_ctx'] = {}
    # Pending deposit proof of status
    context['pending_deposit_list'] = pending_qs[:5]
    try:
        context.update(user_display_context(user, request=request))
        # Keep explicit display code from permanent preference (context already matches)
        context['display_currency'] = display_code
        context['currency_symbol'] = currency_meta['symbol']
    except Exception:
        pass
    return render(request, 'dashboard/index.html', context)


@require_POST
def set_theme(request):
    theme = request.POST.get('theme', 'dark')
    if theme not in ('dark', 'light'):
        theme = 'dark'
    response = HttpResponse(status=204)
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=204)
    else:
        response = redirect(request.META.get('HTTP_REFERER', '/'))
    response.set_cookie('theme', theme, max_age=365 * 24 * 3600, samesite='Lax')
    if request.user.is_authenticated:
        request.user.preferred_theme = theme
        request.user.save(update_fields=['preferred_theme'])
    return response


def _wants_json(request) -> bool:
    accept = (request.headers.get('Accept') or '').lower()
    if 'application/json' in accept:
        return True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    if request.GET.get('format') == 'json' or request.POST.get('format') == 'json':
        return True
    return False


@login_required
@require_POST
def set_display_currency(request):
    """
    Permanently switch display currency (DB + session + cookie).
    HTML form → redirect. AJAX/fetch (JSON Accept) → live balance payload.
    """
    from django.contrib import messages as dj_messages
    from django.urls import reverse
    from wallets.display import (
        build_balance_api_payload,
        persist_display_currency,
        resolve_currency_code,
    )

    wants_json = _wants_json(request)
    code = (request.POST.get('currency') or '').strip()[:20]
    if not code:
        if wants_json:
            return JsonResponse({'ok': False, 'error': 'Please choose a display currency.'}, status=400)
        dj_messages.error(request, 'Please choose a display currency.')
        return redirect(request.META.get('HTTP_REFERER') or reverse('core:dashboard'))

    resolved = resolve_currency_code(request.user, code, request=request)
    if resolved is None:
        if wants_json:
            return JsonResponse({'ok': False, 'error': 'Invalid display currency.'}, status=400)
        dj_messages.error(request, 'Invalid display currency.')
        return redirect(request.META.get('HTTP_REFERER') or reverse('core:dashboard'))

    if wants_json:
        try:
            persist_display_currency(request.user, resolved, request=request, response=None)
            payload = build_balance_api_payload(request.user, resolved)
            payload['currency'] = resolved
            payload['message'] = f'Display currency saved as {resolved}. This stays after refresh.'
            payload['saved'] = True
            payload['permanent'] = True
            response = JsonResponse(payload)
            # Cookie must be set on the HTTP response the browser receives
            persist_display_currency(request.user, resolved, request=request, response=response)
            return response
        except ValueError as exc:
            return JsonResponse({'ok': False, 'error': str(exc)}, status=400)

    try:
        persist_display_currency(request.user, resolved, request=request, response=None)
    except ValueError:
        dj_messages.error(request, 'Invalid display currency.')
        return redirect(request.META.get('HTTP_REFERER') or reverse('core:dashboard'))

    dj_messages.success(request, f'Display currency saved as {resolved}. It will stay after you refresh.')
    from django.utils.http import url_has_allowed_host_and_scheme
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('core:dashboard')
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = reverse('core:dashboard')
    response = redirect(next_url)
    persist_display_currency(request.user, resolved, request=request, response=response)
    return response


@login_required
@require_GET
def dashboard_stats_api(request):
    """
    Live balances in the selected (or preferred) display currency.

    GET /dashboard/stats/
    GET /dashboard/stats/?currency=ETH
    """
    from wallets.display import build_balance_api_payload

    currency = request.GET.get('currency')
    payload = build_balance_api_payload(request.user, currency)
    status = 200 if payload.get('ok') else 400
    return JsonResponse(payload, status=status)


@login_required
@require_GET
def balances_api(request):
    """
    Clean balance API for the app UI.

    GET /api/balances/              → preferred currency
    GET /api/balances/?currency=BTC → convert without saving preference
    """
    from wallets.display import build_balance_api_payload

    payload = build_balance_api_payload(request.user, request.GET.get('currency'))
    status = 200 if payload.get('ok') else 400
    return JsonResponse(payload, status=status)
