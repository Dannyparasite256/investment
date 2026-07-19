"""JSON receipts for deposits, withdrawals, investments, earnings, referrals."""
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils import format_money, quantize_amount
from investments.models import Earning, Investment
from referrals.models import ReferralCommission
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


class InvestmentReceiptView(APIView):
    """Receipt for opening / holding an investment position."""

    def get(self, request, pk):
        inv = get_object_or_404(
            Investment.objects.select_related('plan'),
            pk=pk,
            user=request.user,
        )
        linked = Transaction.objects.filter(
            user=request.user, reference_type='investment', reference_id=str(inv.id),
        ).order_by('created_at').first()
        if linked and request.GET.get('tx') == '1':
            return Response(_tx_payload(request, linked))

        code = get_default_display_code(request.user, request=request)
        meta = get_currency_meta(code)
        amount_disp = format_amount_for_code(inv.amount, code)
        earned_disp = format_amount_for_code(inv.total_earned or 0, code)
        rows = [
            _row('Receipt ID', inv.id),
            _row('Type', 'Investment'),
            _row('Status', inv.get_status_display()),
            _row('Plan', inv.plan.name if inv.plan_id else '—'),
            _row('Invested amount', amount_disp['label']),
            _row('Total earned', earned_disp['label']),
            _row('Profit rate', f'{inv.profit_rate_percent}%'),
            _row('Payout frequency', inv.payout_frequency),
            _row('Duration', f'{inv.duration_days} days'),
            _row('Payouts', f'{inv.payouts_count} / {inv.expected_payouts}'),
            _row('Auto reinvest', 'Yes' if inv.auto_reinvest else 'No'),
            _row('Return principal', 'Yes' if inv.return_principal else 'No'),
            _row('Started', inv.started_at),
            _row('Matures', inv.matures_at),
        ]
        if inv.completed_at:
            rows.append(_row('Completed', inv.completed_at))
        rows.append(_row('Platform value (invested)', format_amount_for_code(inv.amount, 'USD')['label']))
        if linked:
            rows.append(_row('Ledger tx', linked.id))

        return Response({
            'kind': 'investment',
            'id': str(inv.id),
            'title': 'Investment receipt',
            'status': inv.status,
            'status_label': inv.get_status_display(),
            'display_currency': code,
            'currency_symbol': str(meta['symbol']),
            'amount': amount_disp,
            'earned': earned_disp,
            'rows': rows,
            'print_url': '',
        })


class EarningReceiptView(APIView):
    """Receipt for a profit / investment earnings payout."""

    def get(self, request, pk):
        earning = get_object_or_404(
            Earning.objects.select_related('investment', 'investment__plan'),
            pk=pk,
            user=request.user,
        )
        linked = Transaction.objects.filter(
            user=request.user, reference_type='earning', reference_id=str(earning.id),
        ).first()
        if linked and request.GET.get('tx') == '1':
            return Response(_tx_payload(request, linked))

        code = get_default_display_code(request.user, request=request)
        meta = get_currency_meta(code)
        amount_disp = format_amount_for_code(earning.amount, code)
        plan_name = ''
        inv_amount = None
        if earning.investment_id:
            plan_name = earning.investment.plan.name if earning.investment.plan_id else ''
            inv_amount = earning.investment.amount
        rows = [
            _row('Receipt ID', earning.id),
            _row('Type', 'Investment profit / earning'),
            _row('Status', 'Reinvested' if earning.is_reinvested else 'Paid'),
            _row('Amount', amount_disp['label']),
            _row('Period', earning.period_number),
            _row('Plan', plan_name or '—'),
            _row('Investment ID', earning.investment_id or '—'),
        ]
        if inv_amount is not None:
            rows.append(_row('Position size', format_amount_for_code(inv_amount, code)['label']))
        if earning.description:
            rows.append(_row('Description', earning.description))
        rows.append(_row('Date', earning.created_at))
        rows.append(_row('Platform value', format_amount_for_code(earning.amount, 'USD')['label']))
        if linked:
            rows.append(_row('Ledger tx', linked.id))

        return Response({
            'kind': 'earning',
            'id': str(earning.id),
            'title': 'Earning receipt',
            'status': 'reinvested' if earning.is_reinvested else 'paid',
            'status_label': 'Reinvested' if earning.is_reinvested else 'Paid',
            'display_currency': code,
            'currency_symbol': str(meta['symbol']),
            'amount': amount_disp,
            'rows': rows,
            'print_url': '',
        })


class ReferralReceiptView(APIView):
    """Receipt for a referral commission credit."""

    def get(self, request, pk):
        comm = get_object_or_404(
            ReferralCommission.objects.select_related('referred_user'),
            pk=pk,
            referrer=request.user,
        )
        linked = Transaction.objects.filter(
            user=request.user,
            tx_type=Transaction.TxType.REFERRAL,
            reference_id=str(comm.id),
        ).first()
        if not linked:
            linked = Transaction.objects.filter(
                user=request.user,
                reference_type='referral',
                reference_id=str(comm.id),
            ).first()

        code = get_default_display_code(request.user, request=request)
        meta = get_currency_meta(code)
        amount_disp = format_amount_for_code(comm.amount, code)
        base_disp = format_amount_for_code(comm.base_amount, code)
        referred = comm.referred_user.email if comm.referred_user_id else '—'
        # Lightly mask email for privacy on printed receipt of referred user
        if '@' in referred:
            local, domain = referred.split('@', 1)
            referred_display = (local[:2] + '***@' + domain) if len(local) > 2 else '***@' + domain
        else:
            referred_display = referred

        rows = [
            _row('Receipt ID', comm.id),
            _row('Type', 'Referral commission'),
            _row('Status', comm.get_status_display()),
            _row('Commission', amount_disp['label']),
            _row('Rate', f'{comm.rate_percent}%'),
            _row('Level', comm.level),
            _row('Source', comm.source or '—'),
            _row('Base amount', base_disp['label']),
            _row('Referred user', referred_display),
            _row('Date', comm.created_at),
        ]
        if comm.paid_at:
            rows.append(_row('Paid at', comm.paid_at))
        if comm.notes:
            rows.append(_row('Notes', comm.notes))
        rows.append(_row('Platform value', format_amount_for_code(comm.amount, 'USD')['label']))
        if linked:
            rows.append(_row('Ledger tx', linked.id))

        return Response({
            'kind': 'referral',
            'id': str(comm.id),
            'title': 'Referral earnings receipt',
            'status': comm.status,
            'status_label': comm.get_status_display(),
            'display_currency': code,
            'currency_symbol': str(meta['symbol']),
            'amount': amount_disp,
            'rows': rows,
            'print_url': '',
        })
