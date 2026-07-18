from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from investments.forms import InvestForm
from investments.models import Earning, Investment, InvestmentPlan
from investments.services import create_investment, manual_reinvest
from wallets.display import (
    format_amount_for_code,
    get_currency_meta,
    get_default_display_code,
)
from wallets.models import Wallet


def _user_currency(user, request=None) -> str:
    if user is not None and getattr(user, 'is_authenticated', False):
        return get_default_display_code(user, request=request)
    if request is not None:
        cookie = (request.COOKIES.get('display_currency') or '').strip()
        if cookie:
            return cookie.upper() if len(cookie) <= 12 else cookie
    return 'USD'


def _invest_display_context(user, plan=None, wallet=None, request=None):
    """Amounts formatted in the user's permanent display currency."""
    code = _user_currency(user, request=request)
    meta = get_currency_meta(code)
    ctx = {
        'display_currency': code,
        'currency_symbol': meta['symbol'],
        'currency_decimals': meta['decimals'],
        'currency_meta': meta,
    }
    if plan is not None:
        ctx['min_display'] = format_amount_for_code(plan.min_deposit, code)
        ctx['max_display'] = format_amount_for_code(plan.max_deposit, code)
    if wallet is not None:
        ctx['available_display'] = format_amount_for_code(wallet.available_balance, code)
    return ctx


def _attach_plan_display(plans, code: str):
    """Attach min/max display payloads on each plan for templates."""
    for p in plans:
        p.min_display = format_amount_for_code(p.min_deposit, code)
        p.max_display = format_amount_for_code(p.max_deposit, code)
    return plans


def plan_list(request):
    plans = list(InvestmentPlan.objects.filter(
        status__in=[InvestmentPlan.Status.ACTIVE, InvestmentPlan.Status.COMING_SOON]
    ))
    code = _user_currency(request.user, request=request)
    _attach_plan_display(plans, code)
    featured = [p for p in plans if p.is_featured]
    return render(request, 'investments/plan_list.html', {
        'plans': plans,
        'featured': featured,
        'currency_symbol': get_currency_meta(code)['symbol'],
        'display_currency': code,
    })


def plan_detail(request, slug):
    plan = get_object_or_404(InvestmentPlan, slug=slug)
    code = _user_currency(request.user, request=request)
    form = InvestForm(plan=plan, currency_code=code) if request.user.is_authenticated else None
    wallet = None
    if request.user.is_authenticated:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
    ctx = {
        'plan': plan,
        'form': form,
        'wallet': wallet,
    }
    ctx.update(_invest_display_context(request.user, plan=plan, wallet=wallet, request=request))
    return render(request, 'investments/plan_detail.html', ctx)


@login_required
@require_http_methods(['GET', 'POST'])
def invest(request, slug):
    plan = get_object_or_404(InvestmentPlan, slug=slug, status=InvestmentPlan.Status.ACTIVE)
    code = _user_currency(request.user, request=request)
    form = InvestForm(plan=plan, currency_code=code, data=request.POST or None)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    if request.method == 'POST' and form.is_valid():
        try:
            inv = create_investment(
                user=request.user,
                plan=plan,
                amount=form.cleaned_data['amount'],  # platform USD-equivalent
                auto_reinvest=form.cleaned_data.get('auto_reinvest', False),
                duration_days=form.cleaned_data.get('duration_days') or None,
                request=request,
            )
            messages.success(request, f'Successfully invested in {plan.name}!')
            return redirect('investments:detail', pk=inv.pk)
        except ValueError as exc:
            messages.error(request, str(exc))
    ctx = {
        'plan': plan,
        'form': form,
        'wallet': wallet,
    }
    ctx.update(_invest_display_context(request.user, plan=plan, wallet=wallet, request=request))
    return render(request, 'investments/invest.html', ctx)


@login_required
def my_investments(request):
    status = request.GET.get('status', '')
    qs = Investment.objects.filter(user=request.user).select_related('plan')
    if status:
        qs = qs.filter(status=status)
    page = Paginator(qs, 12).get_page(request.GET.get('page'))
    code = _user_currency(request.user, request=request)
    # Attach display payloads for template (avoid heavy logic in HTML)
    for inv in page:
        inv.amount_display = format_amount_for_code(inv.amount, code)
        inv.earned_display = format_amount_for_code(inv.total_earned, code)
    return render(request, 'investments/my_investments.html', {
        'page': page,
        'status': status,
        'display_currency': code,
        'currency_symbol': get_currency_meta(code)['symbol'],
    })


@login_required
def investment_detail(request, pk):
    inv = get_object_or_404(Investment, pk=pk, user=request.user)
    earnings = inv.earnings.all()[:50]
    code = _user_currency(request.user, request=request)
    for e in earnings:
        e.amount_display = format_amount_for_code(e.amount, code)
    return render(request, 'investments/detail.html', {
        'inv': inv,
        'earnings': earnings,
        'amount_display': format_amount_for_code(inv.amount, code),
        'earned_display': format_amount_for_code(inv.total_earned, code),
        'display_currency': code,
        'currency_symbol': get_currency_meta(code)['symbol'],
    })


@login_required
@require_POST
def reinvest_view(request, pk):
    inv = get_object_or_404(Investment, pk=pk, user=request.user)
    try:
        new_inv = manual_reinvest(request.user, inv, request=request)
        messages.success(request, 'Reinvestment created successfully.')
        return redirect('investments:detail', pk=new_inv.pk)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('investments:detail', pk=pk)


@login_required
def earnings_history(request):
    qs = Earning.objects.filter(user=request.user).select_related('investment', 'investment__plan')
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    code = _user_currency(request.user, request=request)
    for e in page:
        e.amount_display = format_amount_for_code(e.amount, code)
    return render(request, 'investments/earnings.html', {
        'page': page,
        'display_currency': code,
        'currency_symbol': get_currency_meta(code)['symbol'],
    })


def calculator(request):
    plans = InvestmentPlan.objects.filter(status=InvestmentPlan.Status.ACTIVE)
    code = _user_currency(request.user, request=request)
    meta = get_currency_meta(code)
    plans_js = []
    for p in plans:
        min_p = format_amount_for_code(p.min_deposit, code)
        max_p = format_amount_for_code(p.max_deposit, code)
        plans_js.append({
            'pk': str(p.pk),
            'name': p.name,
            'rate': str(p.profit_rate_percent),
            'periods': p.periods_count,
            'freq': p.get_payout_frequency_display(),
            'min_value': min_p['value'],
            'max_value': max_p['value'],
            'min_label': min_p['label'],
            'max_label': max_p['label'],
        })
    default_amount = plans_js[0]['min_value'] if plans_js else '1000'
    return render(request, 'investments/calculator.html', {
        'plans': plans,
        'plans_js': plans_js,
        'display_currency': code,
        'currency_symbol': meta['symbol'],
        'currency_decimals': meta['decimals'],
        'default_amount': default_amount,
    })
