"""Staff/admin API for the Vue SPA (subset of /staff/ panel)."""
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import KYCDocument
from core.models import AuditLog
from core.utils import create_audit_log
from investments.models import Investment
from notifications.models import Notification, notify
from staffpanel.permissions import user_is_staff_panel
from staffpanel.utils import log_admin_activity
from support.models import SupportTicket, TicketMessage
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.display import (
    annotate_deposits,
    annotate_withdrawals,
    deposit_platform_usd,
    format_amount_for_code,
    resolve_deposit_display_amounts,
    resolve_withdrawal_display_amounts,
)
from wallets.models import Wallet

User = get_user_model()


class IsStaffPanel(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and user_is_staff_panel(request.user))


class StaffDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def get(self, request):
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)
        month_ago = timezone.now() - timedelta(days=30)

        pending_deps = list(
            Deposit.objects.filter(
                status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION],
            ).select_related('cryptocurrency', 'user')
        )
        pending_dep_usd = sum((deposit_platform_usd(d) for d in pending_deps), Decimal('0'))
        pending_wd_usd = Withdrawal.objects.filter(
            status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.APPROVED],
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
        invested_total = Investment.objects.filter(status=Investment.Status.ACTIVE).aggregate(
            t=Sum('amount'),
        )['t'] or Decimal('0')
        revenue_month = Deposit.objects.filter(
            status=Deposit.Status.APPROVED, reviewed_at__gte=month_ago,
        ).aggregate(t=Sum('credit_amount'))['t'] or Decimal('0')

        deposit_daily = (
            Deposit.objects.filter(
                status=Deposit.Status.APPROVED,
                reviewed_at__gte=timezone.now() - timedelta(days=14),
            )
            .annotate(day=TruncDate('reviewed_at'))
            .values('day')
            .annotate(total=Sum('credit_amount'), count=Count('id'))
            .order_by('day')
        )
        chart_labels = [str(r['day']) for r in deposit_daily]
        chart_deposits = [float(r['total'] or 0) for r in deposit_daily]

        recent_deposits = list(
            Deposit.objects.select_related('user', 'cryptocurrency').order_by('-created_at')[:10]
        )
        recent_withdrawals = list(
            Withdrawal.objects.select_related('user', 'cryptocurrency').order_by('-created_at')[:10]
        )
        annotate_deposits(recent_deposits, use_user_pref=True)
        annotate_withdrawals(recent_withdrawals, use_user_pref=True)

        def pack_dep(d):
            ad = getattr(d, 'amount_display', None) or {}
            return {
                'id': str(d.id),
                'user_email': d.user.email,
                'amount': str(d.amount),
                'crypto_symbol': d.cryptocurrency.symbol,
                'status': d.status,
                'created_at': d.created_at,
                'display_label': ad.get('label') if isinstance(ad, dict) else str(d.amount),
            }

        def pack_wd(w):
            ad = getattr(w, 'amount_display', None) or {}
            return {
                'id': str(w.id),
                'user_email': w.user.email,
                'amount': str(w.amount),
                'crypto_symbol': w.cryptocurrency.symbol,
                'status': w.status,
                'created_at': w.created_at,
                'display_label': ad.get('label') if isinstance(ad, dict) else str(w.amount),
            }

        return Response({
            'stats': {
                'users_total': User.objects.count(),
                'users_today': User.objects.filter(date_joined__date=today).count(),
                'users_week': User.objects.filter(date_joined__gte=week_ago).count(),
                'deposits_pending': len(pending_deps),
                'deposits_pending_sum': format_amount_for_code(pending_dep_usd, 'USD')['label'],
                'withdrawals_pending': Withdrawal.objects.filter(
                    status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.APPROVED],
                ).count(),
                'withdrawals_pending_sum': format_amount_for_code(pending_wd_usd, 'USD')['label'],
                'kyc_pending': KYCDocument.objects.filter(
                    status__in=[KYCDocument.Status.PENDING, KYCDocument.Status.UNDER_REVIEW],
                ).count(),
                'active_investments': Investment.objects.filter(status=Investment.Status.ACTIVE).count(),
                'invested_total': format_amount_for_code(invested_total, 'USD')['label'],
                'revenue_month': format_amount_for_code(revenue_month, 'USD')['label'],
                'open_tickets': SupportTicket.objects.exclude(
                    status__in=[SupportTicket.Status.CLOSED, SupportTicket.Status.RESOLVED],
                ).count(),
            },
            'chart': {'labels': chart_labels, 'deposits': chart_deposits},
            'recent_deposits': [pack_dep(d) for d in recent_deposits],
            'recent_withdrawals': [pack_wd(w) for w in recent_withdrawals],
        })


class StaffDepositListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def get(self, request):
        status_f = request.GET.get('status', '')
        q = (request.GET.get('q') or '').strip()
        qs = Deposit.objects.select_related('user', 'cryptocurrency').order_by('-created_at')
        if status_f == 'pending':
            qs = qs.filter(status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION])
        elif status_f:
            qs = qs.filter(status=status_f)
        if q:
            qs = qs.filter(Q(user__email__icontains=q) | Q(transaction_hash__icontains=q) | Q(id__icontains=q))
        rows = list(qs[:50])
        annotate_deposits(rows, use_user_pref=True)
        data = []
        for d in rows:
            ad = getattr(d, 'amount_display', None) or {}
            data.append({
                'id': str(d.id),
                'user_email': d.user.email,
                'user_id': d.user_id,
                'amount': str(d.amount),
                'crypto_symbol': d.cryptocurrency.symbol,
                'network': d.network,
                'transaction_hash': d.transaction_hash or '',
                'status': d.status,
                'created_at': d.created_at,
                'display_label': ad.get('label') if isinstance(ad, dict) else f'{d.amount} {d.cryptocurrency.symbol}',
            })
        return Response({'results': data})


class StaffDepositActionView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def post(self, request, pk, action):
        dep = get_object_or_404(Deposit, pk=pk)
        if action == 'approve':
            notes = request.data.get('notes', '')
            try:
                dep.approve(request.user, notes=notes)
                try:
                    from core.vip import apply_deposit_fee
                    from wallets.models import WalletLedger
                    credit = dep.credit_amount or dep.amount
                    net, fee, pct = apply_deposit_fee(dep.user, credit)
                    if fee > 0:
                        wallet, _ = Wallet.objects.get_or_create(user=dep.user)
                        if wallet.available_balance >= fee:
                            wallet.debit(fee)
                            WalletLedger.objects.create(
                                wallet=wallet,
                                entry_type=WalletLedger.EntryType.FEE,
                                amount=-fee,
                                balance_after=wallet.balance,
                                description=f'VIP deposit fee {pct}%',
                                reference_type='deposit',
                                reference_id=str(dep.id),
                            )
                except Exception:
                    pass
                try:
                    from referrals.services import process_referral_commission
                    process_referral_commission(
                        dep.user, dep.credit_amount or dep.amount, source='deposit',
                        reference_type='deposit', reference_id=dep.id,
                    )
                except Exception:
                    pass
                try:
                    disp = resolve_deposit_display_amounts(dep)
                    credit_label = disp['amount_display']['label']
                except Exception:
                    credit_label = str(dep.credit_amount or dep.amount)
                notify(
                    dep.user, 'Deposit approved',
                    f'Your deposit was approved and credited ({credit_label}).',
                    level=Notification.Level.SUCCESS, category=Notification.Category.DEPOSIT,
                    link='/app/deposits',
                )
                create_audit_log(
                    request=request, action=AuditLog.Action.DEPOSIT_APPROVE,
                    message=f'Approved deposit {dep.id}', object_type='Deposit', object_id=dep.id,
                )
                log_admin_activity(request, 'deposit_approve', notes, 'Deposit', dep.id)
                return Response({'ok': True, 'status': dep.status, 'detail': 'Approved'})
            except ValueError as e:
                return Response({'ok': False, 'detail': str(e)}, status=400)

        if action == 'reject':
            reason = request.data.get('reason') or 'Rejected by administrator'
            try:
                dep.reject(request.user, reason=reason)
                notify(
                    dep.user, 'Deposit rejected',
                    f'Your deposit of {dep.amount} was rejected. {reason}',
                    level=Notification.Level.DANGER, category=Notification.Category.DEPOSIT,
                )
                create_audit_log(
                    request=request, action=AuditLog.Action.DEPOSIT_REJECT,
                    message=f'Rejected deposit {dep.id}', object_type='Deposit', object_id=dep.id,
                )
                log_admin_activity(request, 'deposit_reject', reason, 'Deposit', dep.id)
                return Response({'ok': True, 'status': dep.status, 'detail': 'Rejected'})
            except ValueError as e:
                return Response({'ok': False, 'detail': str(e)}, status=400)

        return Response({'detail': 'Unknown action'}, status=400)


class StaffWithdrawalListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def get(self, request):
        status_f = request.GET.get('status', '')
        q = (request.GET.get('q') or '').strip()
        qs = Withdrawal.objects.select_related('user', 'cryptocurrency').order_by('-created_at')
        if status_f:
            qs = qs.filter(status=status_f)
        if q:
            qs = qs.filter(Q(user__email__icontains=q) | Q(wallet_address__icontains=q) | Q(id__icontains=q))
        rows = list(qs[:50])
        annotate_withdrawals(rows, use_user_pref=True)
        data = []
        for w in rows:
            ad = getattr(w, 'amount_display', None) or {}
            data.append({
                'id': str(w.id),
                'user_email': w.user.email,
                'amount': str(w.amount),
                'fee': str(w.fee or 0),
                'crypto_symbol': w.cryptocurrency.symbol,
                'wallet_address': w.wallet_address,
                'status': w.status,
                'created_at': w.created_at,
                'display_label': ad.get('label') if isinstance(ad, dict) else str(w.amount),
            })
        return Response({'results': data})


class StaffWithdrawalActionView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def post(self, request, pk, action):
        w = get_object_or_404(Withdrawal, pk=pk)
        try:
            if action == 'approve':
                notes = request.data.get('notes', '')
                w.approve(request.user, notes=notes)
                try:
                    amt_label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
                except Exception:
                    amt_label = str(w.amount)
                notify(
                    w.user, 'Withdrawal approved',
                    f'Your withdrawal of {amt_label} was approved and is being processed.',
                    level=Notification.Level.SUCCESS, category=Notification.Category.WITHDRAWAL,
                )
                log_admin_activity(request, 'withdrawal_approve', notes, 'Withdrawal', w.id)
                return Response({'ok': True, 'status': w.status})
            if action == 'paid':
                tx_hash = request.data.get('tx_hash', '')
                notes = request.data.get('notes', '')
                w.mark_paid(request.user, tx_hash=tx_hash, notes=notes)
                try:
                    amt_label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
                except Exception:
                    amt_label = str(w.amount)
                notify(
                    w.user, 'Withdrawal paid',
                    f'Your withdrawal of {amt_label} has been paid.' + (f' Tx: {tx_hash}' if tx_hash else ''),
                    level=Notification.Level.SUCCESS, category=Notification.Category.WITHDRAWAL,
                )
                log_admin_activity(request, 'withdrawal_paid', f'hash={tx_hash}', 'Withdrawal', w.id)
                return Response({'ok': True, 'status': w.status})
            if action == 'reject':
                reason = request.data.get('reason') or 'Rejected by administrator'
                w.reject(request.user, reason=reason)
                try:
                    amt_label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
                except Exception:
                    amt_label = str(w.amount)
                notify(
                    w.user, 'Withdrawal rejected',
                    f'Your withdrawal of {amt_label} was rejected. Funds unlocked. {reason}',
                    level=Notification.Level.WARNING, category=Notification.Category.WITHDRAWAL,
                )
                log_admin_activity(request, 'withdrawal_reject', reason, 'Withdrawal', w.id)
                return Response({'ok': True, 'status': w.status})
        except ValueError as e:
            return Response({'ok': False, 'detail': str(e)}, status=400)
        return Response({'detail': 'Unknown action'}, status=400)


class StaffKYCListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def get(self, request):
        status_f = request.GET.get('status', '')
        qs = KYCDocument.objects.select_related('user').order_by('-created_at')
        if status_f:
            qs = qs.filter(status=status_f)
        else:
            qs = qs.filter(status__in=[KYCDocument.Status.PENDING, KYCDocument.Status.UNDER_REVIEW])
        data = [{
            'id': str(d.id),
            'user_email': d.user.email,
            'document_type': d.document_type,
            'document_number': d.document_number,
            'status': d.status,
            'created_at': d.created_at,
            'front_image': d.front_image.url if d.front_image else None,
        } for d in qs[:50]]
        return Response({'results': data})


class StaffKYCActionView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def post(self, request, pk, action):
        doc = get_object_or_404(KYCDocument, pk=pk)
        if action == 'approve':
            doc.status = KYCDocument.Status.APPROVED
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
            doc.user.is_kyc_verified = True
            doc.user.save(update_fields=['is_kyc_verified'])
            notify(doc.user, 'KYC approved', 'Your identity verification was approved.',
                   level=Notification.Level.SUCCESS, category=Notification.Category.KYC)
            log_admin_activity(request, 'kyc_approve', '', 'KYCDocument', doc.id)
            return Response({'ok': True, 'status': doc.status})
        if action == 'reject':
            reason = request.data.get('reason') or 'Rejected'
            doc.status = KYCDocument.Status.REJECTED
            doc.rejection_reason = reason
            doc.reviewed_by = request.user
            doc.reviewed_at = timezone.now()
            doc.save(update_fields=['status', 'rejection_reason', 'reviewed_by', 'reviewed_at', 'updated_at'])
            notify(doc.user, 'KYC rejected', reason, level=Notification.Level.WARNING, category=Notification.Category.KYC)
            log_admin_activity(request, 'kyc_reject', reason, 'KYCDocument', doc.id)
            return Response({'ok': True, 'status': doc.status})
        return Response({'detail': 'Unknown action'}, status=400)


class StaffUserListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def get(self, request):
        q = (request.GET.get('q') or '').strip()
        qs = User.objects.all().order_by('-date_joined')
        if q:
            qs = qs.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
        data = []
        for u in qs[:50]:
            wallet, _ = Wallet.objects.get_or_create(user=u)
            data.append({
                'id': u.id,
                'email': u.email,
                'name': u.get_full_name(),
                'is_kyc_verified': u.is_kyc_verified,
                'email_verified': u.email_verified,
                'is_active': u.is_active,
                'role': u.role,
                'date_joined': u.date_joined,
                'balance': str(wallet.balance),
                'available': str(wallet.available_balance),
                'preferred_currency': u.preferred_currency or '',
            })
        return Response({'results': data})


class StaffTicketListView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def get(self, request):
        qs = (
            SupportTicket.objects.select_related('user')
            .prefetch_related('messages')
            .order_by('-updated_at')[:80]
        )
        results = []
        for t in qs:
            last = t.messages.order_by('-created_at').first()
            results.append({
                'id': str(t.id),
                'subject': t.subject,
                'status': t.status,
                'priority': t.priority,
                'category': t.category,
                'user_email': t.user.email,
                'user_name': t.user.get_full_name() or t.user.email,
                'created_at': t.created_at,
                'updated_at': t.updated_at,
                'message_count': t.messages.count(),
                'last_message': ({
                    'id': str(last.id),
                    'body': last.body,
                    'is_staff_reply': last.is_staff_reply,
                    'created_at': last.created_at,
                    'receipt_status': last.receipt_status,
                } if last else None),
            })
        return Response({'results': results})


class StaffTicketDetailView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPanel]

    def _msg_dict(self, m):
        return {
            'id': str(m.id),
            'body': m.body,
            'is_staff_reply': m.is_staff_reply,
            'sender_name': m.sender.get_full_name() or m.sender.email,
            'created_at': m.created_at,
            'delivered_at': m.delivered_at,
            'read_at': m.read_at,
            'receipt_status': m.receipt_status,
            'sender': m.sender_id,
        }

    def _mark_user_messages_read(self, ticket):
        from support.realtime import notify_receipts

        now = timezone.now()
        qs = TicketMessage.objects.filter(
            ticket=ticket, is_staff_reply=False, read_at__isnull=True,
        )
        ids = list(qs.values_list('id', flat=True))
        if not ids:
            return 0
        n = qs.update(delivered_at=now, read_at=now, updated_at=now)
        notify_receipts(ticket.id, ids, 'read', now.isoformat())
        return n

    def get(self, request, pk):
        from support.realtime import get_presence, set_presence

        t = get_object_or_404(SupportTicket.objects.prefetch_related('messages__sender'), pk=pk)
        set_presence(t.id, request.user, is_staff=True)
        self._mark_user_messages_read(t)
        return Response({
            'id': str(t.id),
            'subject': t.subject,
            'status': t.status,
            'category': t.category,
            'priority': t.priority,
            'user_email': t.user.email,
            'user_name': t.user.get_full_name() or t.user.email,
            'updated_at': t.updated_at,
            'created_at': t.created_at,
            'messages': [self._msg_dict(m) for m in t.messages.all()],
            'presence': get_presence(t.id),
        })

    def post(self, request, pk):
        from support.realtime import get_presence, get_typing, notify_new_message, set_presence, set_typing

        t = get_object_or_404(SupportTicket.objects.prefetch_related('messages__sender'), pk=pk)
        action = (request.data.get('action') or 'reply').strip()

        if action == 'typing':
            from support.realtime import as_bool
            is_typing = as_bool(request.data.get('is_typing', True), default=True)
            set_typing(t.id, request.user, is_typing=is_typing, is_staff=True)
            return Response({'ok': True, 'is_typing': is_typing})

        if action == 'heartbeat':
            set_presence(t.id, request.user, is_staff=True)
            self._mark_user_messages_read(t)
            return Response({
                'ok': True,
                'presence': get_presence(t.id),
                'typing': get_typing(t.id, exclude_user_id=request.user.pk),
            })

        if action == 'poll':
            set_presence(t.id, request.user, is_staff=True)
            self._mark_user_messages_read(t)
            since = request.data.get('since') or request.query_params.get('since')
            qs = t.messages.select_related('sender').all()
            if since:
                try:
                    since_dt = datetime.fromisoformat(str(since).replace('Z', '+00:00'))
                    if timezone.is_naive(since_dt):
                        since_dt = timezone.make_aware(since_dt, timezone.get_current_timezone())
                    qs = qs.filter(created_at__gt=since_dt)
                except (ValueError, TypeError):
                    pass
            own = t.messages.filter(is_staff_reply=True).select_related('sender')
            return Response({
                'messages': [self._msg_dict(m) for m in qs],
                'receipts': [self._msg_dict(m) for m in own],
                'typing': get_typing(t.id, exclude_user_id=request.user.pk),
                'presence': get_presence(t.id),
                'status': t.status,
                'server_time': timezone.now().isoformat(),
            })

        body = (request.data.get('body') or '').strip()
        if not body:
            return Response({'detail': 'Message required'}, status=400)
        msg = TicketMessage.objects.create(
            ticket=t, sender=request.user, body=body, is_staff_reply=True,
        )
        t.status = SupportTicket.Status.WAITING
        t.save(update_fields=['status', 'updated_at'])
        notify_new_message(t, msg)
        notify(
            t.user, 'Support reply', f'Re: {t.subject}',
            category=Notification.Category.SYSTEM, link=f'/app/support/{t.id}',
        )
        return Response(self._msg_dict(msg), status=201)
