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
from django.urls import reverse
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
                _rate = deposit.cryptocurrency.usd_price or 1
                try:
                    from decimal import Decimal as _D
                    from core.utils import quantize_amount as _q
                    _credit_est = _q(_D(str(deposit.amount)) * _D(str(_rate)), 8)
                except Exception:
                    _credit_est = deposit.amount
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
                        'crypto_symbol': deposit.cryptocurrency.symbol,
                        'symbol': deposit.cryptocurrency.symbol,
                        'rate_usd': str(_rate),
                        'platform_credit': str(_credit_est),
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
    from wallets.display import annotate_deposits, get_default_display_code, get_currency_meta

    code = get_default_display_code(request.user, request=request)
    qs = Deposit.objects.filter(user=request.user).select_related('cryptocurrency')
    page = Paginator(qs, 15).get_page(request.GET.get('page'))
    annotate_deposits(page.object_list, display_code=code, use_user_pref=False)
    return render(request, 'transactions/deposit_list.html', {
        'page': page,
        'display_currency': code,
        'currency_symbol': get_currency_meta(code)['symbol'],
    })


@login_required
def deposit_detail(request, pk):
    from wallets.display import apply_display_amounts, get_default_display_code, resolve_deposit_display_amounts

    deposit = get_object_or_404(Deposit, pk=pk, user=request.user)
    code = get_default_display_code(request.user, request=request)
    apply_display_amounts(deposit, resolve_deposit_display_amounts(deposit, code))
    return render(request, 'transactions/deposit_detail.html', {
        'deposit': deposit,
        'display_currency': code,
    })


def _session_time_ok(request, key: str, minutes: int = 20) -> bool:
    from datetime import timedelta

    from django.utils import timezone
    from django.utils.dateparse import parse_datetime

    raw = request.session.get(key) or ''
    when = parse_datetime(raw) if raw else None
    if not when:
        return False
    if timezone.is_naive(when):
        when = timezone.make_aware(when, timezone.get_current_timezone())
    return when >= timezone.now() - timedelta(minutes=minutes)


def _recent_google_reauth(request, minutes=20) -> bool:
    """True if user confirmed Google identity within the window."""
    if request.session.get('social_reauth_provider') != 'google':
        return False
    return _session_time_ok(request, 'social_reauth_at', minutes=minutes)


def _recent_email_reauth(request, minutes=20) -> bool:
    return _session_time_ok(request, 'withdraw_email_verified_at', minutes=minutes)


def _withdraw_reauth_ok(request) -> bool:
    """Either recent Google confirm or recent email code counts."""
    return _recent_google_reauth(request) or _recent_email_reauth(request)


def _send_withdraw_email_code(request) -> None:
    """Send free email OTP for withdrawal confirmation (shared OTP service)."""
    from django.utils import timezone

    from accounts.otp import PURPOSE_WITHDRAW, send_email_otp

    # Clear previous success so they must re-enter a fresh code
    request.session.pop('withdraw_email_verified_at', None)
    request.session.pop('withdraw_email_code', None)
    request.session.pop('withdraw_email_code_at', None)
    result = send_email_otp(request.user, PURPOSE_WITHDRAW)
    if not result.ok:
        raise RuntimeError(result.message)
    request.session['withdraw_email_code_pending'] = True
    request.session['withdraw_email_code_at'] = timezone.now().isoformat()


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

    # Ensure latest preference from DB (not a stale session user object)
    try:
        request.user.refresh_from_db(
            fields=['require_social_reauth_withdraw', 'email'],
        )
    except Exception:
        pass

    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    display_code = get_default_display_code(request.user, request=request)
    currency_meta = get_currency_meta(display_code)
    needs_reauth = bool(getattr(request.user, 'require_social_reauth_withdraw', False))
    reauth_ok = _withdraw_reauth_ok(request) if needs_reauth else True
    reauth_via = (
        'google' if _recent_google_reauth(request)
        else ('email' if _recent_email_reauth(request) else '')
    )

    # Handle verification actions before the withdrawal form
    if request.method == 'POST' and request.POST.get('security_action'):
        action = request.POST.get('security_action')
        if action == 'send_email_code':
            try:
                _send_withdraw_email_code(request)
                messages.success(
                    request,
                    f'We sent a 6-digit code to {request.user.email}. Enter it below.',
                )
            except Exception as exc:
                messages.error(request, f'Could not send email: {exc}')
            return redirect('transactions:withdraw_create')
        if action == 'verify_email_code':
            from django.utils import timezone

            from accounts.otp import PURPOSE_WITHDRAW, verify_email_otp

            submitted = (request.POST.get('email_code') or '').strip()
            result = verify_email_otp(request.user, PURPOSE_WITHDRAW, submitted)
            if result.ok:
                request.session['withdraw_email_verified_at'] = timezone.now().isoformat()
                request.session.pop('withdraw_email_code_pending', None)
                request.session.pop('withdraw_email_code', None)
                messages.success(request, 'Email confirmed. You can submit your withdrawal now.')
            else:
                messages.error(request, result.message)
            return redirect('transactions:withdraw_create')

    form = WithdrawalForm(
        user=request.user,
        currency_code=display_code,
        data=request.POST or None if not request.POST.get('security_action') else None,
    )
    if request.method == 'POST' and not request.POST.get('security_action') and form.is_valid():
        if needs_reauth and not _withdraw_reauth_ok(request):
            messages.error(
                request,
                'Extra security is on for your account. Confirm by email code or Google first, '
                'then submit the withdrawal again.',
            )
            return redirect('transactions:withdraw_create')
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
            try:
                from core.email_events import email_withdrawal_requested
                email_withdrawal_requested(w, amount_label=display_label)
            except Exception:
                pass
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
        'needs_reauth': needs_reauth,
        'reauth_ok': reauth_ok,
        'reauth_via': reauth_via,
        'code_sent': bool(
            request.session.get('withdraw_email_code_pending')
            or request.session.get('withdraw_email_code')
        ),
        'user_email': request.user.email,
        'google_reauth_url': (
            reverse('accounts:oauth_start', args=['google'])
            + '?next=' + reverse('transactions:withdraw_create')
        ),
    })


@login_required
def withdraw_list(request):
    from wallets.display import (
        annotate_withdrawals,
        get_default_display_code,
        get_currency_meta,
        usd_to_crypto_units,
    )

    code = get_default_display_code(request.user, request=request)
    qs = Withdrawal.objects.filter(user=request.user).select_related('cryptocurrency')
    page = Paginator(qs, 15).get_page(request.GET.get('page'))
    annotate_withdrawals(page.object_list, display_code=code, use_user_pref=False)
    for w in page:
        # Prefer historical crypto label; else live estimate for payout column
        if getattr(w, 'crypto_label', None):
            w.crypto_payout = w.crypto_label
        else:
            try:
                w.crypto_payout = f"{usd_to_crypto_units(w.net_amount or w.amount, w.cryptocurrency)} {w.cryptocurrency.symbol}"
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
    from wallets.display import annotate_transactions, get_default_display_code

    code = get_default_display_code(request.user, request=request)
    qs = Transaction.objects.filter(user=request.user)
    tx_type = request.GET.get('type')
    if tx_type:
        qs = qs.filter(tx_type=tx_type)
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    annotate_transactions(page.object_list, display_code=code, use_user_pref=False)
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
    from core.utils import format_money
    from wallets.display import (
        format_amount_for_code,
        format_amount_native,
        get_currency_meta,
        get_default_display_code,
        resolve_transaction_display_amounts,
    )

    tx = get_object_or_404(Transaction, pk=pk, user=request.user)
    code = get_default_display_code(request.user, request=request)
    meta = get_currency_meta(code)
    resolved = resolve_transaction_display_amounts(tx, code)
    amount_disp = resolved['amount_display']
    fee_disp = resolved['fee_display']
    net_disp = resolved['net_display']
    md = tx.metadata or {}

    sticker = _sticker_for_transaction(tx)
    rows = [
        ('Receipt ID', str(tx.id)),
        ('Type', tx.get_tx_type_display()),
        ('Status', tx.get_status_display()),
        ('Amount', amount_disp['label']),
    ]
    if fee_disp and resolved['fee_usd'] and resolved['fee_usd'] > 0:
        rows.append(('Fee', fee_disp['label']))
        rows.append(('Net amount', net_disp['label']))

    # Exact desired entry (when user entered a different currency than table amount)
    if (
        resolved.get('desired_amount') is not None
        and resolved.get('desired_currency')
        and not amount_disp.get('native')
    ):
        desired = format_amount_native(
            resolved['desired_amount'],
            resolved['desired_currency'],
        )
        rows.append(('You entered', desired['label']))

    if resolved.get('crypto_amount') and resolved.get('crypto_symbol'):
        crypto_label = f"{format_money(resolved['crypto_amount'], 8, strip_trailing_zeros=True)} {resolved['crypto_symbol']}"
        rows.append(('Crypto amount', crypto_label))
    elif tx.currency and tx.tx_type == Transaction.TxType.DEPOSIT:
        rows.append(('Crypto amount', f"{format_money(tx.amount, 8, strip_trailing_zeros=True)} {tx.currency}"))

    # Platform value for ops clarity (always matches wallet ledger)
    platform_disp = format_amount_for_code(resolved['platform_usd'], 'USD')
    rows.append(('Platform value', f"{platform_disp['label']}"))

    if resolved.get('rate_usd'):
        unit = resolved.get('crypto_symbol') or tx.currency or 'unit'
        rows.append(('Rate', f"1 {unit} ≈ ${format_money(resolved['rate_usd'], 8, strip_trailing_zeros=True)}"))

    if tx.network:
        rows.append(('Network', tx.network))
    if tx.wallet_address:
        rows.append(('Wallet address', tx.wallet_address))
    if tx.tx_hash:
        rows.append(('Transaction hash', tx.tx_hash))
    if tx.description:
        rows.append(('Description', tx.description))
    if tx.reference_type and tx.reference_id:
        rows.append(('Reference', f'{tx.reference_type} · {tx.reference_id}'))
    rows.append(('Date', tx.created_at))

    extra = []
    if md.get('fee_percent') not in (None, '', '0', '0.0'):
        extra.append(('Fee rate', f"{md['fee_percent']}%"))

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
        'resolved': resolved,
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
