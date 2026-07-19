"""JSON receipts for deposits, withdrawals, and ledger transactions."""
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import format_money, quantize_amount
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.display import (
    format_amount_for_code,
    format_amount_native,
    get_currency_meta,
    get_default_display_code,
    platform_usd_from_transaction,
    resolve_deposit_display_amounts,
    resolve_withdrawal_display_amounts,
)


def _row(label, value):
    if hasattr(value, 'isoformat'):
        value = value.isoformat()
    return {'label': label, 'value': str(value) if value is not None else '—'}


def _tx_payload(request, tx):
    code = get_default_display_code(request.user, request=request)
    meta = get_currency_meta(code)
    usd = platform_usd_from_transaction(tx)
    amount_disp = format_amount_for_code(usd, code)
    rows = [
        _row('Receipt ID', tx.id),
        _row('Type', tx.get_tx_type_display() if hasattr(tx, 'get_tx_type_display') else tx.tx_type),
        _row('Status', tx.get_status_display() if hasattr(tx, 'get_status_display') else tx.status),
        _row('Amount', amount_disp['label']),
        _row('Platform value', format_amount_for_code(usd, 'USD')['label']),
        _row('Description', tx.description or '—'),
        _row('Reference', f'{tx.reference_type}:{tx.reference_id}' if tx.reference_type else '—'),
        _row('Date', tx.created_at),
    ]
    return {
        'kind': 'transaction',
        'id': str(tx.id),
        'title': f'{tx.get_tx_type_display() if hasattr(tx, "get_tx_type_display") else tx.tx_type} receipt',
        'status': tx.status,
        'status_label': tx.get_status_display() if hasattr(tx, 'get_status_display') else tx.status,
        'display_currency': code,
        'currency_symbol': str(meta['symbol']),
        'amount': amount_disp,
        'rows': rows,
        'print_url': f'/transactions/receipts/{tx.id}/',
    }


class DepositReceiptView(APIView):
    def get(self, request, pk):
        deposit = get_object_or_404(Deposit, pk=pk, user=request.user)
        linked = Transaction.objects.filter(
            user=request.user, reference_type='deposit', reference_id=str(deposit.id),
        ).first()
        if linked:
            return Response(_tx_payload(request, linked))

        code = get_default_display_code(request.user, request=request)
        meta = get_currency_meta(code)
        try:
            disp = resolve_deposit_display_amounts(deposit, display_code=code)
            amount_disp = disp.get('amount_display')
        except Exception:
            amount_disp = None
            credit = deposit.credit_amount
            if credit is None:
                price = Decimal(str(getattr(deposit.cryptocurrency, 'usd_price', None) or 0))
                if price > 0:
                    credit = quantize_amount(Decimal(str(deposit.amount or 0)) * price, 8)
            if credit is not None:
                amount_disp = format_amount_for_code(credit, code)

        crypto_label = (
            f"{format_money(deposit.amount, 8, strip_trailing_zeros=True)} "
            f"{deposit.cryptocurrency.symbol}"
        )
        rows = [
            _row('Receipt ID', deposit.id),
            _row('Type', 'Crypto deposit'),
            _row('Status', deposit.get_status_display()),
            _row('Amount', amount_disp['label'] if amount_disp else crypto_label),
            _row('Crypto amount', crypto_label),
            _row('Network', deposit.network or deposit.cryptocurrency.network),
            _row('Tx hash', deposit.transaction_hash or '—'),
            _row('Submitted', deposit.created_at),
        ]
        if amount_disp and amount_disp.get('usd_equivalent'):
            rows.append(_row('Platform value (USD)', f"{amount_disp['usd_equivalent']} USD"))

        return Response({
            'kind': 'deposit',
            'id': str(deposit.id),
            'title': 'Deposit receipt',
            'status': deposit.status,
            'status_label': deposit.get_status_display(),
            'display_currency': code,
            'currency_symbol': str(meta['symbol']),
            'amount': amount_disp or {
                'label': crypto_label,
                'value': str(deposit.amount),
                'symbol': deposit.cryptocurrency.symbol,
                'formatted': format_money(deposit.amount, 8, strip_trailing_zeros=True),
            },
            'rows': rows,
            'print_url': f'/receipts/deposit/{deposit.id}/',
        })


class WithdrawalReceiptView(APIView):
    def get(self, request, pk):
        withdrawal = get_object_or_404(Withdrawal, pk=pk, user=request.user)
        linked = Transaction.objects.filter(
            user=request.user, reference_type='withdrawal', reference_id=str(withdrawal.id),
        ).first()
        if linked:
            return Response(_tx_payload(request, linked))

        code = get_default_display_code(request.user, request=request)
        meta = get_currency_meta(code)
        try:
            resolved = resolve_withdrawal_display_amounts(withdrawal, display_code=code)
            amount_disp = resolved.get('amount_display') or format_amount_for_code(withdrawal.amount, code)
            fee_disp = resolved.get('fee_display')
            net_disp = resolved.get('net_display')
        except Exception:
            amount_disp = format_amount_for_code(withdrawal.amount, code)
            fee_disp = format_amount_for_code(withdrawal.fee or 0, code) if withdrawal.fee else None
            net_disp = format_amount_for_code(
                withdrawal.net_amount if withdrawal.net_amount is not None
                else (withdrawal.amount - (withdrawal.fee or 0)),
                code,
            )

        notes = withdrawal.admin_notes or ''
        if notes.startswith('Display:'):
            try:
                part = notes.split('·')[0].replace('Display:', '').strip()
                bits = part.rsplit(' ', 1)
                if len(bits) == 2 and bits[1].upper() == code.upper():
                    amount_disp = format_amount_native(bits[0], code)
            except Exception:
                pass

        rows = [
            _row('Receipt ID', withdrawal.id),
            _row('Type', 'Withdrawal'),
            _row('Status', withdrawal.get_status_display()),
            _row('Amount', amount_disp['label']),
        ]
        if fee_disp:
            rows.append(_row('Fee', fee_disp['label']))
            if net_disp:
                rows.append(_row('Net amount', net_disp['label']))
        rows.append(_row('Platform value', format_amount_for_code(withdrawal.amount, 'USD')['label']))
        rows.append(_row('Network', withdrawal.network or withdrawal.cryptocurrency.symbol))
        rows.append(_row('Address', withdrawal.wallet_address))
        if withdrawal.transaction_hash:
            rows.append(_row('Transaction hash', withdrawal.transaction_hash))
        rows.append(_row('Submitted', withdrawal.created_at))

        return Response({
            'kind': 'withdrawal',
            'id': str(withdrawal.id),
            'title': 'Withdrawal receipt',
            'status': withdrawal.status,
            'status_label': withdrawal.get_status_display(),
            'display_currency': code,
            'currency_symbol': str(meta['symbol']),
            'amount': amount_disp,
            'fee': fee_disp,
            'net': net_disp,
            'rows': rows,
            'print_url': f'/receipts/withdrawal/{withdrawal.id}/',
        })


class TransactionReceiptView(APIView):
    def get(self, request, pk):
        tx = get_object_or_404(Transaction, pk=pk, user=request.user)
        return Response(_tx_payload(request, tx))
