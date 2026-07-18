"""Deposit, withdrawal, and history views."""
import base64
import io
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django_ratelimit.decorators import ratelimit

from core.models import AuditLog
from core.utils import create_audit_log
from notifications.models import Notification, notify
from transactions.forms import DepositForm, WithdrawalForm
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.models import Cryptocurrency, UserWalletAddress, Wallet

logger = logging.getLogger('transactions')


def _qr_data_uri(text: str) -> str:
    """Build a data-URI PNG QR code for a wallet address."""
    if not text:
        return ''
    try:
        import qrcode
        img = qrcode.make(text)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception as exc:
        logger.warning('QR generation failed: %s', exc)
        return ''


def _crypto_payload(crypto: Cryptocurrency) -> dict:
    address = (crypto.deposit_address or '').strip()
    qr = ''
    if crypto.qr_code:
        try:
            qr = crypto.qr_code.url
        except ValueError:
            qr = ''
    if not qr and address:
        qr = _qr_data_uri(address)
    return {
        'id': crypto.pk,
        'symbol': crypto.symbol,
        'name': crypto.name,
        'network': crypto.network,
        'network_label': crypto.get_network_display(),
        'deposit_address': address,
        'min_deposit': str(crypto.min_deposit),
        'usd_price': str(crypto.usd_price or 1),
        'qr': qr,
    }


@login_required
@ratelimit(key='user', rate='20/h', method='POST', block=True)
@require_http_methods(['GET', 'POST'])
def deposit_create(request):
    form = DepositForm(request.POST or None, request.FILES or None)
    cryptos = list(Cryptocurrency.objects.filter(is_active=True))
    cryptos_data = [_crypto_payload(c) for c in cryptos]
    if request.method == 'POST':
        if form.is_valid():
            try:
                deposit = form.save(commit=False)
                deposit.user = request.user
                deposit.network = deposit.cryptocurrency.network
                deposit.deposit_address = deposit.cryptocurrency.deposit_address
                deposit.status = Deposit.Status.PENDING
                promo = (form.cleaned_data.get('promo_code') or '').strip().upper()
                deposit.promo_code = promo
                deposit.save()
                # Do NOT overwrite a permanent display currency (e.g. UGX).
                # Only seed preferred_currency when the user has never chosen one.
                if not (request.user.preferred_currency or '').strip():
                    request.user.preferred_currency = deposit.cryptocurrency.symbol
                    request.user.save(update_fields=['preferred_currency'])
                try:
                    from accounts.models import ActivityEvent
                    ActivityEvent.objects.create(
                        user=request.user,
                        event_type='deposit_submit',
                        title='Deposit submitted',
                        description=f'{deposit.amount} {deposit.cryptocurrency.symbol} pending approval',
                    )
                except Exception:
                    pass
                Transaction.objects.create(
                    user=request.user,
                    tx_type=Transaction.TxType.DEPOSIT,
                    amount=deposit.amount,
                    fee=deposit.fee or 0,
                    currency=deposit.cryptocurrency.symbol,
                    network=deposit.network,
                    wallet_address=deposit.deposit_address,
                    tx_hash=deposit.transaction_hash,
                    status=Transaction.Status.PENDING,
                    description=f'Deposit {deposit.amount} {deposit.cryptocurrency.symbol}',
                    reference_type='deposit',
                    reference_id=str(deposit.id),
                    metadata={
                        'crypto_amount': str(deposit.amount),
                        'symbol': deposit.cryptocurrency.symbol,
                        'rate_usd': str(deposit.cryptocurrency.usd_price or 1),
                    },
                )
                create_audit_log(
                    request=request,
                    user=request.user,
                    action=AuditLog.Action.DEPOSIT_CREATE,
                    message=f'Deposit created {deposit.amount} {deposit.cryptocurrency.symbol}',
                    object_type='Deposit',
                    object_id=str(deposit.id),
                )
                notify(
                    request.user,
                    'Deposit Submitted',
                    f'Your deposit of {deposit.amount} {deposit.cryptocurrency.symbol} is pending review.',
                    category=Notification.Category.DEPOSIT,
                    link='/transactions/deposits/',
                )
                # Notify staff users
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    for staff in User.objects.filter(is_staff=True, is_active=True)[:20]:
                        if staff.pk != request.user.pk:
                            notify(
                                staff,
                                'New deposit to review',
                                f'{request.user.email}: {deposit.amount} {deposit.cryptocurrency.symbol}',
                                category=Notification.Category.DEPOSIT,
                                link='/staff/deposits/',
                            )
                except Exception:
                    pass
                messages.success(
                    request,
                    f'Deposit of {deposit.amount} {deposit.cryptocurrency.symbol} submitted. '
                    f'Admins can approve it under Staff → Deposits.',
                )
                return redirect('transactions:deposit_list')
            except Exception as exc:
                logger.exception('Deposit create failed: %s', exc)
                messages.error(request, f'Could not save deposit: {exc}')
        else:
            logger.warning('Deposit form invalid: %s', form.errors.as_json())
            messages.error(request, 'Please fix the errors below and submit again.')
    return render(request, 'transactions/deposit_form.html', {
        'form': form,
        'cryptos': cryptos,
        'cryptos_data': cryptos_data,
    })


@login_required
def deposit_list(request):
    qs = Deposit.objects.filter(user=request.user).select_related('cryptocurrency')
    page = Paginator(qs, 15).get_page(request.GET.get('page'))
    return render(request, 'transactions/deposit_list.html', {'page': page})


@login_required
def deposit_detail(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk, user=request.user)
    return render(request, 'transactions/deposit_detail.html', {'deposit': deposit})


@login_required
@ratelimit(key='user', rate='10/h', method='POST', block=True)
@require_http_methods(['GET', 'POST'])
def withdraw_create(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    form = WithdrawalForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                w = form.save(commit=False)
                w.user = request.user
                w.fee = form.cleaned_data.get('fee') or 0
                w.net_amount = w.amount - w.fee
                w.network = w.cryptocurrency.network
                w.status = Withdrawal.Status.PENDING
                # Lock funds so available balance decreases
                wallet_locked = Wallet.objects.select_for_update().get(user=request.user)
                wallet_locked.lock_funds(w.amount)
                w.funds_locked = True
                # VIP fee + priority + SLA
                try:
                    from core.models import SiteConfiguration
                    from core.vip import apply_withdrawal_fee, get_user_tier
                    fee, _pct = apply_withdrawal_fee(
                        request.user, w.amount, w.cryptocurrency.withdrawal_fee,
                    )
                    w.fee = fee
                    w.net_amount = w.amount - fee
                    tier = get_user_tier(request.user)
                    w.priority = int(tier.sort_order) if tier else 0
                    hours = SiteConfiguration.get_solo().withdrawal_sla_hours or 24
                    from django.utils import timezone as tz
                    from datetime import timedelta as td
                    w.sla_deadline = tz.now() + td(hours=hours)
                except Exception:
                    pass
                w.save()
                Transaction.objects.create(
                    user=request.user,
                    tx_type=Transaction.TxType.WITHDRAWAL,
                    amount=w.amount,
                    fee=w.fee or 0,
                    currency=w.cryptocurrency.symbol,
                    network=w.network,
                    wallet_address=w.wallet_address,
                    status=Transaction.Status.PENDING,
                    description=f'Withdrawal to {w.wallet_address[:16]}…',
                    reference_type='withdrawal',
                    reference_id=str(w.id),
                )
            create_audit_log(
                request=request,
                user=request.user,
                action=AuditLog.Action.WITHDRAW_CREATE,
                message=f'Withdrawal {w.amount} to {w.wallet_address[:20]}',
                object_type='Withdrawal',
                object_id=str(w.id),
            )
            notify(
                request.user,
                'Withdrawal Requested',
                f'Your withdrawal of {w.amount} is pending approval.',
                category=Notification.Category.WITHDRAWAL,
            )
            messages.success(request, 'Withdrawal request submitted.')
            return redirect('transactions:withdraw_list')
        except ValueError as exc:
            messages.error(request, str(exc))
    return render(request, 'transactions/withdraw_form.html', {'form': form, 'wallet': wallet})


@login_required
def withdraw_list(request):
    qs = Withdrawal.objects.filter(user=request.user).select_related('cryptocurrency')
    page = Paginator(qs, 15).get_page(request.GET.get('page'))
    return render(request, 'transactions/withdraw_list.html', {'page': page})


@login_required
@require_POST
def withdraw_cancel(request, pk):
    w = get_object_or_404(Withdrawal, pk=pk, user=request.user, status=Withdrawal.Status.PENDING)
    with transaction.atomic():
        if w.funds_locked:
            wallet = Wallet.objects.select_for_update().get(user=request.user)
            wallet.unlock_funds(w.amount)
            w.funds_locked = False
        w.status = Withdrawal.Status.CANCELLED
        w.save()
    messages.info(request, 'Withdrawal cancelled and funds unlocked.')
    return redirect('transactions:withdraw_list')


@login_required
def history(request):
    qs = Transaction.objects.filter(user=request.user)
    tx_type = request.GET.get('type')
    if tx_type:
        qs = qs.filter(tx_type=tx_type)
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    if request.headers.get('HX-Request'):
        return render(request, 'transactions/partials/history_table.html', {'page': page})
    return render(request, 'transactions/history.html', {'page': page, 'tx_types': Transaction.TxType.choices})


@login_required
@require_GET
def crypto_deposit_info(request, pk):
    """Return deposit address + QR for selected crypto (HTML or JSON)."""
    crypto = get_object_or_404(Cryptocurrency, pk=pk, is_active=True)
    payload = _crypto_payload(crypto)
    if request.headers.get('Accept', '').find('application/json') != -1 or request.GET.get('format') == 'json':
        return JsonResponse(payload)
    return render(request, 'transactions/partials/crypto_info.html', {
        'crypto': crypto,
        'qr_src': payload['qr'],
        'deposit_address': payload['deposit_address'],
    })


@login_required
@require_GET
def saved_addresses_for_crypto(request, pk):
    """JSON list of user's saved withdrawal addresses for a cryptocurrency."""
    crypto = get_object_or_404(Cryptocurrency, pk=pk, is_active=True)
    addrs = UserWalletAddress.objects.filter(
        user=request.user, cryptocurrency=crypto,
    ).values('id', 'address', 'label', 'is_default')
    return JsonResponse({
        'crypto_id': crypto.pk,
        'symbol': crypto.symbol,
        'network': crypto.network,
        'addresses': list(addrs),
    })
