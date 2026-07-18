from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from investments.forms import InvestForm
from investments.models import Earning, Investment, InvestmentPlan
from investments.services import create_investment, manual_reinvest
from wallets.models import Wallet


def plan_list(request):
    plans = InvestmentPlan.objects.filter(
        status__in=[InvestmentPlan.Status.ACTIVE, InvestmentPlan.Status.COMING_SOON]
    )
    featured = plans.filter(is_featured=True)
    return render(request, 'investments/plan_list.html', {
        'plans': plans,
        'featured': featured,
    })


def plan_detail(request, slug):
    plan = get_object_or_404(InvestmentPlan, slug=slug)
    form = InvestForm(plan=plan) if request.user.is_authenticated else None
    wallet = None
    if request.user.is_authenticated:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
    return render(request, 'investments/plan_detail.html', {
        'plan': plan,
        'form': form,
        'wallet': wallet,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def invest(request, slug):
    plan = get_object_or_404(InvestmentPlan, slug=slug, status=InvestmentPlan.Status.ACTIVE)
    form = InvestForm(plan=plan, data=request.POST or None)
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    if request.method == 'POST' and form.is_valid():
        try:
            inv = create_investment(
                user=request.user,
                plan=plan,
                amount=form.cleaned_data['amount'],
                auto_reinvest=form.cleaned_data.get('auto_reinvest', False),
                duration_days=form.cleaned_data.get('duration_days') or None,
                request=request,
            )
            messages.success(request, f'Successfully invested in {plan.name}!')
            return redirect('investments:detail', pk=inv.pk)
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'investments/invest.html', {
        'plan': plan,
        'form': form,
        'wallet': wallet,
    })


@login_required
def my_investments(request):
    status = request.GET.get('status', '')
    qs = Investment.objects.filter(user=request.user).select_related('plan')
    if status:
        qs = qs.filter(status=status)
    page = Paginator(qs, 12).get_page(request.GET.get('page'))
    return render(request, 'investments/my_investments.html', {
        'page': page,
        'status': status,
    })


@login_required
def investment_detail(request, pk):
    inv = get_object_or_404(Investment, pk=pk, user=request.user)
    earnings = inv.earnings.all()[:50]
    return render(request, 'investments/detail.html', {
        'inv': inv,
        'earnings': earnings,
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
    return render(request, 'investments/earnings.html', {'page': page})


def calculator(request):
    plans = InvestmentPlan.objects.filter(status=InvestmentPlan.Status.ACTIVE)
    return render(request, 'investments/calculator.html', {'plans': plans})
