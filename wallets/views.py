from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from wallets.forms import WalletAddressForm
from wallets.models import Cryptocurrency, UserWalletAddress, Wallet, WalletLedger


@login_required
def wallet_overview(request):
    from wallets.display import format_amount_for_code, get_currency_meta, user_display_context

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    ctx = user_display_context(request.user, request=request)
    code = ctx['display_currency']
    meta = get_currency_meta(code)
    ledger = list(WalletLedger.objects.filter(wallet=wallet)[:30])
    for e in ledger:
        e.amount_display = format_amount_for_code(e.amount, code)
        e.balance_display = format_amount_for_code(e.balance_after, code)
    addresses = UserWalletAddress.objects.filter(user=request.user).select_related('cryptocurrency')
    cryptos = Cryptocurrency.objects.filter(is_active=True)
    return render(request, 'wallets/overview.html', {
        'wallet': wallet,
        'ledger': ledger,
        'addresses': addresses,
        'cryptos': cryptos,
        'display_currency': code,
        'currency_symbol': meta['symbol'],
        'display_options': ctx.get('display_options') or [],
        'bal_display': ctx.get('bal_display') or format_amount_for_code(wallet.balance, code),
        'available_display': ctx.get('available_display') or format_amount_for_code(wallet.available_balance, code),
        'locked_display': ctx.get('locked_display') or format_amount_for_code(wallet.locked_balance, code),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def address_create(request):
    form = WalletAddressForm(request.POST or None)
    form.fields['cryptocurrency'].queryset = Cryptocurrency.objects.filter(is_active=True)
    if request.method == 'POST' and form.is_valid():
        addr = form.save(commit=False)
        addr.user = request.user
        addr.save()
        messages.success(request, 'Wallet address saved.')
        return redirect('wallets:overview')
    return render(request, 'wallets/address_form.html', {'form': form})


@login_required
@require_POST
def address_delete(request, pk):
    addr = get_object_or_404(UserWalletAddress, pk=pk, user=request.user)
    addr.delete()
    messages.success(request, 'Address removed.')
    return redirect('wallets:overview')
