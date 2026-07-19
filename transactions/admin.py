from django.contrib import admin, messages
from django.db import transaction as db_transaction
from django.utils.html import format_html

from core.models import AuditLog
from core.utils import create_audit_log
from notifications.models import Notification, notify
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.display import (
    resolve_deposit_display_amounts,
    resolve_transaction_display_amounts,
    resolve_withdrawal_display_amounts,
)


class DesiredAmountMixin:
    """Admin columns that show user preferred / desired amounts."""

    @admin.display(description='Amount (user)')
    def amount_user_display(self, obj):
        try:
            if isinstance(obj, Deposit):
                r = resolve_deposit_display_amounts(obj)
            elif isinstance(obj, Withdrawal):
                r = resolve_withdrawal_display_amounts(obj)
            else:
                r = resolve_transaction_display_amounts(obj)
            label = r['amount_display']['label']
            if r.get('crypto_amount') and r.get('crypto_symbol'):
                return format_html(
                    "{}<br><span style='opacity:.7;font-size:11px'>{} {}</span>",
                    label, r['crypto_amount'], r['crypto_symbol'],
                )
            if r.get('platform_usd') is not None:
                return format_html(
                    "{}<br><span style='opacity:.7;font-size:11px'>{} USD</span>",
                    label, r['platform_usd'],
                )
            return label
        except Exception:
            return str(getattr(obj, 'amount', '—'))

    @admin.display(description='User currency')
    def user_currency_display(self, obj):
        user = getattr(obj, 'user', None)
        if not user:
            return '—'
        return (getattr(user, 'preferred_currency', None) or 'USD') or 'USD'


@admin.register(Deposit)
class DepositAdmin(DesiredAmountMixin, admin.ModelAdmin):
    list_display = (
        'id', 'user', 'cryptocurrency', 'amount_user_display', 'amount', 'credit_amount',
        'user_currency_display', 'status', 'transaction_hash', 'created_at', 'reviewed_by',
    )
    list_filter = ('status', 'cryptocurrency')
    search_fields = ('user__email', 'transaction_hash')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'amount_user_display')
    actions = ['approve_deposits', 'reject_deposits', 'mark_waiting']

    @admin.action(description='Approve selected deposits (credit balance)')
    def approve_deposits(self, request, queryset):
        count = 0
        for dep in queryset.exclude(status=Deposit.Status.APPROVED):
            try:
                with db_transaction.atomic():
                    dep.approve(request.user)
                    r = resolve_deposit_display_amounts(dep)
                    label = r['amount_display']['label']
                    crypto = f"{dep.amount} {dep.cryptocurrency.symbol}"
                    notify(
                        dep.user, 'Deposit Approved',
                        f'Your deposit of {crypto} (≈ {label}) was approved.',
                        level=Notification.Level.SUCCESS, category=Notification.Category.DEPOSIT,
                    )
                    try:
                        from referrals.services import process_referral_commission
                        process_referral_commission(
                            dep.user, dep.credit_amount or dep.amount,
                            source='deposit', reference_type='deposit', reference_id=dep.id,
                        )
                    except Exception:
                        pass
                    create_audit_log(
                        request=request, user=request.user,
                        action=AuditLog.Action.DEPOSIT_APPROVE,
                        message=f'Approved deposit {dep.id} → {label}', object_id=str(dep.id),
                    )
                    count += 1
            except Exception as exc:
                messages.error(request, f'Failed {dep.id}: {exc}')
        self.message_user(request, f'{count} deposit(s) approved.')

    @admin.action(description='Reject selected deposits')
    def reject_deposits(self, request, queryset):
        count = 0
        for dep in queryset.exclude(status__in=[Deposit.Status.APPROVED, Deposit.Status.REJECTED]):
            dep.reject(request.user, reason='Rejected by administrator')
            r = resolve_deposit_display_amounts(dep)
            label = r['amount_display']['label']
            notify(
                dep.user, 'Deposit Rejected',
                f'Your deposit of {label} was rejected.',
                level=Notification.Level.DANGER, category=Notification.Category.DEPOSIT,
            )
            create_audit_log(
                request=request, user=request.user,
                action=AuditLog.Action.DEPOSIT_REJECT,
                message=f'Rejected deposit {dep.id}', object_id=str(dep.id),
            )
            count += 1
        self.message_user(request, f'{count} deposit(s) rejected.')

    @admin.action(description='Mark as waiting confirmation')
    def mark_waiting(self, request, queryset):
        updated = queryset.filter(status=Deposit.Status.PENDING).update(
            status=Deposit.Status.WAITING_CONFIRMATION
        )
        self.message_user(request, f'{updated} deposit(s) marked waiting confirmation.')


@admin.register(Withdrawal)
class WithdrawalAdmin(DesiredAmountMixin, admin.ModelAdmin):
    list_display = (
        'id', 'user', 'cryptocurrency', 'amount_user_display', 'amount', 'wallet_address',
        'user_currency_display', 'status', 'created_at', 'reviewed_by', 'paid_at',
    )
    list_filter = ('status', 'cryptocurrency')
    search_fields = ('user__email', 'wallet_address', 'transaction_hash')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at', 'funds_locked', 'paid_at', 'amount_user_display')
    actions = ['approve_withdrawals', 'mark_paid', 'reject_withdrawals']

    @admin.action(description='Approve selected withdrawals (Pending → Approved)')
    def approve_withdrawals(self, request, queryset):
        count = 0
        for w in queryset.filter(status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.PROCESSING]):
            try:
                w.approve(request.user)
                label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
                notify(
                    w.user, 'Withdrawal Approved',
                    f'Your withdrawal of {label} was approved and is being processed.',
                    level=Notification.Level.SUCCESS, category=Notification.Category.WITHDRAWAL,
                )
                create_audit_log(
                    request=request, user=request.user,
                    action=AuditLog.Action.WITHDRAW_APPROVE,
                    message=f'Approved withdrawal {w.id} ({label})', object_id=str(w.id),
                )
                count += 1
            except Exception as exc:
                messages.error(request, f'Failed {w.id}: {exc}')
        self.message_user(request, f'{count} withdrawal(s) approved.')

    @admin.action(description='Mark as Paid (debit balance)')
    def mark_paid(self, request, queryset):
        count = 0
        for w in queryset.filter(status__in=[
            Withdrawal.Status.APPROVED, Withdrawal.Status.PENDING, Withdrawal.Status.PROCESSING,
        ]):
            try:
                with db_transaction.atomic():
                    w.mark_paid(request.user)
                    label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
                    notify(
                        w.user, 'Withdrawal Paid',
                        f'Your withdrawal of {label} has been paid.',
                        level=Notification.Level.SUCCESS, category=Notification.Category.WITHDRAWAL,
                    )
                    create_audit_log(
                        request=request, user=request.user,
                        action=AuditLog.Action.WITHDRAW_PAID,
                        message=f'Paid withdrawal {w.id} ({label})', object_id=str(w.id),
                    )
                    count += 1
            except Exception as exc:
                messages.error(request, f'Failed {w.id}: {exc}')
        self.message_user(request, f'{count} withdrawal(s) marked Paid.')

    @admin.action(description='Reject selected withdrawals (unlock funds)')
    def reject_withdrawals(self, request, queryset):
        count = 0
        for w in queryset.filter(status__in=[
            Withdrawal.Status.PENDING, Withdrawal.Status.PROCESSING, Withdrawal.Status.APPROVED,
        ]):
            label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
            w.reject(request.user, reason='Rejected by administrator')
            notify(
                w.user, 'Withdrawal Rejected',
                f'Your withdrawal of {label} was rejected. Funds unlocked.',
                level=Notification.Level.WARNING, category=Notification.Category.WITHDRAWAL,
            )
            create_audit_log(
                request=request, user=request.user,
                action=AuditLog.Action.WITHDRAW_REJECT,
                message=f'Rejected withdrawal {w.id}', object_id=str(w.id),
            )
            count += 1
        self.message_user(request, f'{count} withdrawal(s) rejected.')


@admin.register(Transaction)
class TransactionAdmin(DesiredAmountMixin, admin.ModelAdmin):
    list_display = (
        'id', 'created_at', 'user', 'tx_type', 'amount_user_display', 'amount', 'fee',
        'user_currency_display', 'currency', 'network', 'status', 'tx_hash', 'administrator',
    )
    list_filter = ('tx_type', 'status', 'currency', 'network')
    search_fields = ('user__email', 'description', 'reference_id', 'tx_hash', 'wallet_address', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'amount_user_display')
