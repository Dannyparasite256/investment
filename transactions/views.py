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
    from wallets.display import (
        format_amount_for_code,
        get_currency_meta,
        get_default_display_code,
    )

    # Live rates for accurate conversion
    try:
        from core.price_feed import ensure_fresh_prices
        ensure_fresh_prices()
    except Exception:
        pass

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    display_code = get_default_display_code(request.user, request=request)
    currency_meta = get_currency_meta(display_code)
    form = WithdrawalForm(
        user=request.user,
        currency_code=display_code,
        data=request.POST or None,
    )
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                w = form.save(commit=False)
                w.user = request.user
                # Platform USD amounts from form.clean()
                w.amount = form.cleaned_data['amount']
                w.fee = form.cleaned_data.get('fee') or 0
                w.net_amount = form.cleaned_data.get('net_amount') or (w.amount - w.fee)
                w.network = w.cryptocurrency.network
                w.status = Withdrawal.Status.PENDING
                # Lock platform USD balance
                wallet_locked = Wallet.objects.select_for_update().get(user=request.user)
                wallet_locked.lock_funds(w.amount)
                w.funds_locked = True
                try:
                    from core.models import SiteConfiguration
                    from core.vip import get_user_tier
                    tier = get_user_tier(request.user)
                    w.priority = int(tier.sort_order) if tier else 0
                    hours = SiteConfiguration.get_solo().withdrawal_sla_hours or 24
                    from django.utils import timezone as tz
                    from datetime import timedelta as td
                    w.sla_deadline = tz.now() + td(hours=hours)
                except Exception:
                    pass
                # Snapshot rates / display for ops in admin notes
                disp_amt = form.cleaned_data.get('display_amount')
                disp_cur = form.cleaned_data.get('display_currency') or display_code
                crypto_amt = form.cleaned_data.get('crypto_amount')
                rate = form.cleaned_data.get('rate_usd')
                w.admin_notes = (
                    f'Display: {disp_amt} {disp_cur} · '
                    f'Payout: {crypto_amt} {w.cryptocurrency.symbol} · '
                    f'Rate: 1 {w.cryptocurrency.symbol} = ${rate} · '
                    f'Platform lock: {w.amount} USD'
                )
                w.save()

                display_label = format_amount_for_code(w.amount, disp_cur)['label']
                Transaction.objects.create(
                    user=request.user,
                    tx_type=Transaction.TxType.WITHDRAWAL,
                    amount=w.amount,
                    fee=w.fee or 0,
                    currency=w.cryptocurrency.symbol,
                    network=w.network,
                    wallet_address=w.wallet_address,
                    status=Transaction.Status.PENDING,
                    description=(
                        f'Withdraw {crypto_amt} {w.cryptocurrency.symbol} '
                        f'({display_label}) → {w.wallet_address[:14]}…'
                    ),
                    reference_type='withdrawal',
                    reference_id=str(w.id),
                    metadata={
                        'display_amount': str(disp_amt),
                        'display_currency': disp_cur,
                        'crypto_amount': str(crypto_amt),
                        'crypto_symbol': w.cryptocurrency.symbol,
                        'rate_usd': str(rate),
                        'platform_usd': str(w.amount),
                        'fee_usd': str(w.fee),
                        'net_usd': str(w.net_amount),
                        'fee_percent': str(form.cleaned_data.get('fee_percent') or 0),
                    },
                )
            create_audit_log(
                request=request,
                user=request.user,
                action=AuditLog.Action.WITHDRAW_CREATE,
                message=(
                    f'Withdrawal {disp_amt} {disp_cur} → '
                    f'{crypto_amt} {w.cryptocurrency.symbol} '
                    f'(platform {w.amount} USD) to {w.wallet_address[:20]}'
                ),
                object_type='Withdrawal',
                object_id=str(w.id),
            )
            notify(
                request.user,
                'Withdrawal Requested',
                f'Your withdrawal of {display_label} '
                f'({crypto_amt} {w.cryptocurrency.symbol}) is pending approval.',
                category=Notification.Category.WITHDRAWAL,
            )
            messages.success(
                request,
                f'Withdrawal submitted: {display_label} → '
                f'{crypto_amt} {w.cryptocurrency.symbol} on {w.network}.',
            )
            return redirect('transactions:withdraw_list')
        except ValueError as exc:
            messages.error(request, str(exc))

    from decimal import Decimal
    from wallets.display import convert_from_usd, crypto_units_to_usd
    from wallets.models import Cryptocurrency

    available_display = format_amount_for_code(wallet.available_balance, display_code)
    cryptos = list(
        Cryptocurrency.objects.filter(is_active=True).order_by('sort_order', 'symbol')
    )
    rates = []
    for c in cryptos:
        price = c.usd_price or 0
        one_crypto_in_display = convert_from_usd(Decimal(str(price or 0)), display_code)
        min_usd = crypto_units_to_usd(c.min_withdrawal or 0, c)
        min_disp = format_amount_for_code(min_usd, display_code)
        rates.append({
            'id': c.pk,
            'symbol': c.symbol,
            'network': c.network,
            'network_label': c.get_network_display(),
            'usd_price': str(price),
            'display_per_unit': str(one_crypto_in_display),
            'min_label': min_disp['label'],
            'min_value': min_disp['value'],
            'fee_units': str(c.withdrawal_fee or 0),
        })

    return render(request, 'transactions/withdraw_form.html', {
        'form': form,
        'wallet': wallet,
        'available_display': available_display,
        'display_currency': display_code,
        'currency_symbol': currency_meta['symbol'],
        'currency_decimals': currency_meta['decimals'],
        'crypto_rates': rates,
    })


@login_required
def withdraw_list(request):
    from wallets.display import format_amount_for_code, get_default_display_code, get_currency_meta

    code = get_default_display_code(request.user, request=request)
    qs = Withdrawal.objects.filter(user=request.user).select_related('cryptocurrency')
    page = Paginator(qs, 15).get_page(request.GET.get('page'))
    for w in page:
        w.amount_display = format_amount_for_code(w.amount, code)
        w.fee_display = format_amount_for_code(w.fee or 0, code)
        # Crypto payout estimate from current rate (historical rate may differ slightly)
        try:
            from wallets.display import usd_to_crypto_units
            w.crypto_payout = usd_to_crypto_units(w.net_amount or w.amount, w.cryptocurrency)
        except Exception:
            w.crypto_payout = None
    return render(request, 'transactions/withdraw_list.html', {
        'page': page,
        'display_currency': code,
        'currency_symbol': get_currency_meta(code)['symbol'],
    })


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
    from wallets.display import format_amount_for_code, get_default_display_code

    code = get_default_display_code(request.user, request=request)
    qs = Transaction.objects.filter(user=request.user)
    tx_type = request.GET.get('type')
    if tx_type:
        qs = qs.filter(tx_type=tx_type)
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    for tx in page:
        tx.amount_display = format_amount_for_code(tx.amount, code)
        tx.fee_display = format_amount_for_code(tx.fee or 0, code) if tx.fee else None
    if request.headers.get('HX-Request'):
        return render(request, 'transactions/partials/history_table.html', {
            'page': page,
            'display_currency': code,
        })
    return render(request, 'transactions/history.html', {
        'page': page,
        'tx_types': Transaction.TxType.choices,
        'display_currency': code,
    })


def _sticker_for_transaction(tx: Transaction) -> str:
    """Map transaction type/status to animated sticker kind."""
    if tx.status in (Transaction.Status.FAILED, Transaction.Status.CANCELLED):
        return 'rejected'
    if tx.status in (Transaction.Status.PENDING, Transaction.Status.PROCESSING):
        return 'pending'
    mapping = {
        Transaction.TxType.DEPOSIT: 'deposit',
        Transaction.TxType.WITHDRAWAL: 'withdraw',
        Transaction.TxType.INVESTMENT: 'invest',
        Transaction.TxType.REINVEST: 'invest',
        Transaction.TxType.PROFIT: 'profit',
        Transaction.TxType.REFERRAL: 'referral',
        Transaction.TxType.REFUND: 'success',
        Transaction.TxType.FEE: 'pending',
        Transaction.TxType.ADJUSTMENT: 'success',
    }
    return mapping.get(tx.tx_type, 'success')


@login_required
@require_GET
def transaction_receipt(request, pk):
    """Official receipt for any ledger transaction belonging to the user."""
    from wallets.display import format_amount_for_code, get_currency_meta, get_default_display_code

    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    code = get_default_display_code(request.user, request=request)
    meta = get_currency_meta(code)
    amount_disp = format_amount_for_code(tx.amount, code)
    fee_disp = format_amount_for_code(tx.fee or 0, code) if tx.fee else None
    net_usd = (tx.amount or 0) - (tx.fee or 0)
    net_disp = format_amount_for_code(net_usd, code)

    sticker = _sticker_for_transaction(tx)
    rows = [
        ('Receipt ID', str(tx.id)),
        ('Type', tx.get_tx_type_display()),
        ('Status', tx.get_status_display()),
        ('Amount', amount_disp['label']),
    ]
    if fee_disp and (tx.fee or 0) > 0:
        rows.append(('Fee', fee_disp['label']))
        rows.append(('Net', net_disp['label']))
    if tx.currency:
        rows.append(('Currency / asset', tx.currency))
    if tx.network:
        rows.append(('Network', tx.network))
    if tx.wallet_address:
        rows.append(('Wallet address', tx.wallet_address))
    if tx.tx_hash:
        rows.append(('Transaction hash', tx.tx_hash))
    if tx.description:
        rows.append(('Description', tx.description))
    if tx.reference_type and tx.reference_id:
        rows.append(('Reference', f'{tx.reference_type}:{tx.reference_id}'))
    rows.append(('Date', tx.created_at))

    # Extra metadata (display amounts, crypto payout, etc.)
    extra = []
    md = tx.metadata or {}
    if md.get('display_amount') and md.get('display_currency'):
        extra.append(('Entered amount', f"{md['display_amount']} {md['display_currency']}"))
    if md.get('crypto_amount') and md.get('crypto_symbol'):
        extra.append(('Crypto amount', f"{md['crypto_amount']} {md['crypto_symbol']}"))
    if md.get('rate_usd'):
        extra.append(('Rate (USD)', f"1 unit ≈ ${md['rate_usd']}"))
    if md.get('platform_credit'):
        extra.append(('Platform credit', str(md['platform_credit'])))

    return render(request, 'transactions/receipt.html', {
        'kind': 'transaction',
        'tx': tx,
        'title': f'{tx.get_tx_type_display()} receipt',
        'sticker_kind': sticker,
        'amount_display': amount_disp,
        'fee_display': fee_disp,
        'net_display': net_disp,
        'display_currency': code,
        'currency_symbol': meta['symbol'],
        'rows': rows,
        'extra_rows': extra,
        'status_class': tx.status,
        'status_label': tx.get_status_display(),
    })


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
