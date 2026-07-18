from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from wallets.forms import WalletAddressForm
from wallets.models import Cryptocurrency, UserWalletAddress, Wallet, WalletLedger


@login_required
def wallet_overview(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    ledger = WalletLedger.objects.filter(wallet=wallet)[:30]
    addresses = UserWalletAddress.objects.filter(user=request.user).select_related('cryptocurrency')
    cryptos = Cryptocurrency.objects.filter(is_active=True)
    return render(request, 'wallets/overview.html', {
        'wallet': wallet,
        'ledger': ledger,
        'addresses': addresses,
        'cryptos': cryptos,
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
