"""Custom professional staff admin dashboard and management views."""
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.models import ActivityEvent, KYCDocument
from accounts.security_models import AdminActivityLog, LoginHistory, UserSuspension
from cms.models import Announcement, CMSPage, FAQ
from core.models import AuditLog, CurrencyRate, SiteConfiguration
from core.utils import create_audit_log
from investments.models import Investment, InvestmentPlan
from notifications.models import Notification, notify
from referrals.models import ReferralCommission, ReferralProgram
from staffpanel.exports import export_csv, export_excel, export_pdf
from staffpanel.permissions import staff_panel_required
from staffpanel.utils import log_admin_activity
from support.models import SupportTicket, TicketMessage
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.models import Cryptocurrency, Wallet

User = get_user_model()


@staff_panel_required
def dashboard(request):
    from wallets.display import (
        annotate_deposits,
        annotate_withdrawals,
        deposit_platform_usd,
        format_amount_for_code,
    )

    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)
    month_ago = timezone.now() - timedelta(days=30)

    pending_deps = list(
        Deposit.objects.filter(
            status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION]
        ).select_related('cryptocurrency', 'user')
    )
    pending_dep_usd = sum((deposit_platform_usd(d) for d in pending_deps), Decimal('0'))
    pending_wd_usd = Withdrawal.objects.filter(
        status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.APPROVED]
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    invested_total = Investment.objects.filter(status=Investment.Status.ACTIVE).aggregate(
        t=Sum('amount')
    )['t'] or Decimal('0')
    revenue_month = Deposit.objects.filter(
        status=Deposit.Status.APPROVED, reviewed_at__gte=month_ago,
    ).aggregate(t=Sum('credit_amount'))['t'] or Decimal('0')
    withdrawals_month = Withdrawal.objects.filter(
        status=Withdrawal.Status.PAID, paid_at__gte=month_ago,
    ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

    stats = {
        'users_total': User.objects.count(),
        'users_today': User.objects.filter(date_joined__date=today).count(),
        'users_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'deposits_pending': len(pending_deps),
        'deposits_pending_sum': format_amount_for_code(pending_dep_usd, 'USD')['label'],
        'withdrawals_pending': Withdrawal.objects.filter(
            status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.APPROVED]
        ).count(),
        'withdrawals_pending_sum': format_amount_for_code(pending_wd_usd, 'USD')['label'],
        'kyc_pending': KYCDocument.objects.filter(
            status__in=[KYCDocument.Status.PENDING, KYCDocument.Status.UNDER_REVIEW]
        ).count(),
        'active_investments': Investment.objects.filter(status=Investment.Status.ACTIVE).count(),
        'invested_total': format_amount_for_code(invested_total, 'USD')['label'],
        'revenue_month': revenue_month,
        'revenue_month_label': format_amount_for_code(revenue_month, 'USD')['label'],
        'withdrawals_month': withdrawals_month,
        'withdrawals_month_label': format_amount_for_code(withdrawals_month, 'USD')['label'],
        'open_tickets': SupportTicket.objects.exclude(
            status__in=[SupportTicket.Status.CLOSED, SupportTicket.Status.RESOLVED]
        ).count(),
    }

    # Chart: last 14 days deposits
    deposit_daily = (
        Deposit.objects.filter(status=Deposit.Status.APPROVED, reviewed_at__gte=timezone.now() - timedelta(days=14))
        .annotate(day=TruncDate('reviewed_at'))
        .values('day')
        .annotate(total=Sum('credit_amount'), count=Count('id'))
        .order_by('day')
    )
    chart_labels = [str(r['day']) for r in deposit_daily]
    chart_deposits = [float(r['total'] or 0) for r in deposit_daily]

    withdraw_daily = (
        Withdrawal.objects.filter(status=Withdrawal.Status.PAID, paid_at__gte=timezone.now() - timedelta(days=14))
        .annotate(day=TruncDate('paid_at'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )
    wmap = {str(r['day']): float(r['total'] or 0) for r in withdraw_daily}
    chart_withdrawals = [wmap.get(d, 0) for d in chart_labels]

    recent_deposits = list(
        Deposit.objects.select_related('user', 'cryptocurrency').order_by('-created_at')[:8]
    )
    recent_withdrawals = list(
        Withdrawal.objects.select_related('user', 'cryptocurrency').order_by('-created_at')[:8]
    )
    annotate_deposits(recent_deposits, use_user_pref=True)
    annotate_withdrawals(recent_withdrawals, use_user_pref=True)
    recent_activity = AdminActivityLog.objects.select_related('admin')[:10]

    return render(request, 'staffpanel/dashboard.html', {
        'stats': stats,
        'chart_labels': json.dumps(chart_labels),
        'chart_deposits': json.dumps(chart_deposits),
        'chart_withdrawals': json.dumps(chart_withdrawals),
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'recent_activity': recent_activity,
    })


# ---------- Deposits ----------
@staff_panel_required
def deposit_list(request):
    # Default: show queue needing action (pending + waiting), or all if status=
    status = request.GET.get('status', 'queue')
    q = request.GET.get('q', '').strip()
    qs = Deposit.objects.select_related('user', 'cryptocurrency', 'reviewed_by').order_by('-created_at')
    if status == 'queue' or status == 'pending':
        qs = qs.filter(status__in=[
            Deposit.Status.PENDING,
            Deposit.Status.WAITING_CONFIRMATION,
        ])
        status_label = 'queue'
    elif status:
        qs = qs.filter(status=status)
        status_label = status
    else:
        status_label = ''
    if q:
        qs = qs.filter(
            Q(user__email__icontains=q) | Q(transaction_hash__icontains=q) | Q(id__icontains=q)
        )
    counts = {
        'all': Deposit.objects.count(),
        'queue': Deposit.objects.filter(status__in=[
            Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION,
        ]).count(),
        'approved': Deposit.objects.filter(status=Deposit.Status.APPROVED).count(),
        'rejected': Deposit.objects.filter(status=Deposit.Status.REJECTED).count(),
    }
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    from wallets.display import annotate_deposits
    annotate_deposits(page.object_list, use_user_pref=True)
    return render(request, 'staffpanel/deposits.html', {
        'page': page,
        'status': status_label if status != 'pending' else 'queue',
        'q': q,
        'statuses': Deposit.Status.choices,
        'counts': counts,
    })


@staff_panel_required
@require_POST
def deposit_approve(request, pk):
    dep = get_object_or_404(Deposit, pk=pk)
    notes = request.POST.get('notes', '')
    try:
        dep.approve(request.user, notes=notes)
        credit = dep.credit_amount or dep.amount
        from wallets.display import resolve_deposit_display_amounts
        dep_disp = resolve_deposit_display_amounts(dep)
        credit_label = dep_disp['amount_display']['label']
        crypto_label = dep_disp.get('crypto_amount') and dep_disp.get('crypto_symbol') and (
            f"{dep_disp['crypto_amount']} {dep_disp['crypto_symbol']}"
        ) or f"{dep.amount} {dep.cryptocurrency.symbol}"
        # VIP deposit fee adjustment note (credit already = amount; fee handled at display)
        try:
            from core.vip import apply_deposit_fee
            net, fee, pct = apply_deposit_fee(dep.user, credit)
            if fee > 0:
                from wallets.models import Wallet, WalletLedger
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
        # Promo bonus
        if dep.promo_code:
            try:
                from core.promo import apply_promo_on_deposit, validate_promo
                promo = validate_promo(dep.promo_code, dep.user, credit)
                apply_promo_on_deposit(dep.user, promo, credit, deposit_id=dep.id)
            except Exception:
                pass
        try:
            from core.notify_service import alert_user
            from core.portfolio import record_snapshot
            alert_user(
                dep.user, 'Deposit approved',
                f'Your deposit of {crypto_label} (≈ {credit_label}) was approved and credited.',
                level=Notification.Level.SUCCESS, category=Notification.Category.DEPOSIT,
                link='/transactions/deposits/',
                email=getattr(dep.user, 'email_alerts', True),
                sms=getattr(dep.user, 'sms_alerts', False),
                event_name='deposit.approved',
                event_payload={
                    'deposit_id': str(dep.id),
                    'amount': str(dep.amount),
                    'credit_label': credit_label,
                },
            )
            record_snapshot(dep.user)
        except Exception:
            notify(
                dep.user, 'Deposit approved',
                f'Your deposit of {crypto_label} (≈ {credit_label}) was approved.',
                level=Notification.Level.SUCCESS, category=Notification.Category.DEPOSIT,
                link='/transactions/deposits/',
            )
        try:
            from referrals.services import process_referral_commission
            process_referral_commission(
                dep.user, credit, source='deposit', reference_type='deposit', reference_id=dep.id,
            )
        except Exception:
            pass
        # Do not wipe permanent display currency (e.g. UGX) on approve
        try:
            if not (dep.user.preferred_currency or '').strip():
                dep.user.preferred_currency = dep.cryptocurrency.symbol
                dep.user.save(update_fields=['preferred_currency'])
        except Exception:
            pass
        create_audit_log(
            request=request, action=AuditLog.Action.DEPOSIT_APPROVE,
            message=(
                f'Approved deposit {dep.id}: {crypto_label} → {credit_label} '
                f'(platform {dep.credit_amount}, rate {dep.rate_usd})'
            ),
            object_type='Deposit', object_id=dep.id,
        )
        log_admin_activity(request, 'deposit_approve', f'Approved {dep.id} → {credit_label}', 'Deposit', dep.id)
        messages.success(request, f'Deposit approved and credited ({credit_label}).')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect(request.META.get('HTTP_REFERER') or 'staffpanel:deposits')


@staff_panel_required
@require_POST
def deposit_reject(request, pk):
    dep = get_object_or_404(Deposit, pk=pk)
    reason = request.POST.get('reason', 'Rejected by administrator')
    try:
        dep.reject(request.user, reason=reason)
        try:
            from core.notify_service import alert_user
            alert_user(
                dep.user, 'Deposit rejected',
                f'Your deposit of {dep.amount} was rejected. {reason}',
                level=Notification.Level.DANGER, category=Notification.Category.DEPOSIT,
                email=True, event_name='deposit.rejected',
            )
        except Exception:
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
        messages.success(request, 'Deposit rejected.')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect(request.META.get('HTTP_REFERER') or 'staffpanel:deposits')


# ---------- Withdrawals ----------
@staff_panel_required
def withdrawal_list(request):
    status = request.GET.get('status', '')
    q = request.GET.get('q', '').strip()
    qs = Withdrawal.objects.select_related('user', 'cryptocurrency', 'reviewed_by')
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(user__email__icontains=q) | Q(wallet_address__icontains=q) | Q(id__icontains=q)
        )
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    from wallets.display import annotate_withdrawals
    annotate_withdrawals(page.object_list, use_user_pref=True)
    return render(request, 'staffpanel/withdrawals.html', {
        'page': page, 'status': status, 'q': q, 'statuses': Withdrawal.Status.choices,
    })


@staff_panel_required
@require_POST
def withdrawal_approve(request, pk):
    w = get_object_or_404(Withdrawal, pk=pk)
    notes = request.POST.get('notes', '')
    try:
        w.approve(request.user, notes=notes)
        from wallets.display import resolve_withdrawal_display_amounts
        amt_label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
        notify(
            w.user, 'Withdrawal approved',
            f'Your withdrawal of {amt_label} was approved and is being processed.',
            level=Notification.Level.SUCCESS, category=Notification.Category.WITHDRAWAL,
        )
        create_audit_log(
            request=request, action=AuditLog.Action.WITHDRAW_APPROVE,
            message=f'Approved withdrawal {w.id}', object_type='Withdrawal', object_id=w.id,
        )
        log_admin_activity(request, 'withdrawal_approve', notes, 'Withdrawal', w.id)
        messages.success(request, 'Withdrawal approved (awaiting payout).')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect(request.META.get('HTTP_REFERER') or 'staffpanel:withdrawals')


@staff_panel_required
@require_POST
def withdrawal_paid(request, pk):
    w = get_object_or_404(Withdrawal, pk=pk)
    tx_hash = request.POST.get('tx_hash', '')
    notes = request.POST.get('notes', '')
    try:
        w.mark_paid(request.user, tx_hash=tx_hash, notes=notes)
        from wallets.display import resolve_withdrawal_display_amounts
        amt_label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
        paid_msg = f'Your withdrawal of {amt_label} has been paid.' + (f' Tx: {tx_hash}' if tx_hash else '')
        try:
            from core.notify_service import alert_user
            from core.portfolio import record_snapshot
            alert_user(
                w.user, 'Withdrawal paid',
                paid_msg,
                level=Notification.Level.SUCCESS, category=Notification.Category.WITHDRAWAL,
                email=True, sms=getattr(w.user, 'sms_alerts', False),
                event_name='withdrawal.paid',
            )
            record_snapshot(w.user)
        except Exception:
            notify(
                w.user, 'Withdrawal paid',
                paid_msg,
                level=Notification.Level.SUCCESS, category=Notification.Category.WITHDRAWAL,
            )
        create_audit_log(
            request=request, action=AuditLog.Action.WITHDRAW_PAID,
            message=f'Paid withdrawal {w.id}', object_type='Withdrawal', object_id=w.id,
        )
        log_admin_activity(request, 'withdrawal_paid', f'hash={tx_hash}', 'Withdrawal', w.id)
        messages.success(request, 'Withdrawal marked as Paid.')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect(request.META.get('HTTP_REFERER') or 'staffpanel:withdrawals')


@staff_panel_required
@require_POST
def withdrawal_reject(request, pk):
    w = get_object_or_404(Withdrawal, pk=pk)
    reason = request.POST.get('reason', 'Rejected by administrator')
    try:
        w.reject(request.user, reason=reason)
        from wallets.display import resolve_withdrawal_display_amounts
        amt_label = resolve_withdrawal_display_amounts(w)['amount_display']['label']
        notify(
            w.user, 'Withdrawal rejected',
            f'Your withdrawal of {amt_label} was rejected. Funds unlocked. {reason}',
            level=Notification.Level.WARNING, category=Notification.Category.WITHDRAWAL,
        )
        create_audit_log(
            request=request, action=AuditLog.Action.WITHDRAW_REJECT,
            message=f'Rejected withdrawal {w.id}', object_type='Withdrawal', object_id=w.id,
        )
        log_admin_activity(request, 'withdrawal_reject', reason, 'Withdrawal', w.id)
        messages.success(request, 'Withdrawal rejected and funds unlocked.')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect(request.META.get('HTTP_REFERER') or 'staffpanel:withdrawals')


# ---------- Users ----------
@staff_panel_required
def user_list(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    qs = User.objects.all()
    if q:
        qs = qs.filter(Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'suspended':
        qs = qs.filter(is_active=False)
    elif status == 'kyc':
        qs = qs.filter(is_kyc_verified=True)
    page = Paginator(qs, 30).get_page(request.GET.get('page'))
    return render(request, 'staffpanel/users.html', {'page': page, 'q': q, 'status': status})


@staff_panel_required
def user_detail(request, pk):
    from wallets.display import (
        annotate_deposits,
        annotate_withdrawals,
        format_amount_for_code,
        get_default_display_code,
    )

    user = get_object_or_404(User, pk=pk)
    wallet, _ = Wallet.objects.get_or_create(user=user)
    code = get_default_display_code(user)
    deposits = list(user.deposits.select_related('cryptocurrency').all()[:10])
    withdrawals = list(user.withdrawals.select_related('cryptocurrency').all()[:10])
    annotate_deposits(deposits, display_code=code, use_user_pref=False)
    annotate_withdrawals(withdrawals, display_code=code, use_user_pref=False)
    investments = list(user.investments.select_related('plan')[:10])
    for inv in investments:
        inv.amount_display = format_amount_for_code(inv.amount, code)
        inv.earned_display = format_amount_for_code(inv.total_earned, code)
    return render(request, 'staffpanel/user_detail.html', {
        'target': user,
        'wallet': wallet,
        'bal_display': format_amount_for_code(wallet.balance, code),
        'profit_display': format_amount_for_code(wallet.total_profit, code),
        'referral_display': format_amount_for_code(user.referral_earnings or 0, code),
        'display_currency': code,
        'deposits': deposits,
        'withdrawals': withdrawals,
        'investments': investments,
        'logins': user.login_history.all()[:15],
        'kyc_docs': user.kyc_documents.all()[:5],
    })


@staff_panel_required
@require_POST
def user_suspend(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser:
        messages.error(request, 'Cannot suspend a superuser.')
        return redirect('staffpanel:user_detail', pk=pk)
    reason = request.POST.get('reason', 'Suspended by admin')
    user.is_active = False
    user.save(update_fields=['is_active'])
    UserSuspension.objects.create(user=user, reason=reason, suspended_by=request.user)
    create_audit_log(
        request=request, action=AuditLog.Action.USER_SUSPEND,
        message=f'Suspended {user.email}: {reason}', object_type='User', object_id=user.pk,
    )
    log_admin_activity(request, 'user_suspend', reason, 'User', user.pk)
    notify(user, 'Account suspended', reason, level=Notification.Level.DANGER, category=Notification.Category.SECURITY)
    messages.success(request, f'{user.email} suspended.')
    return redirect('staffpanel:user_detail', pk=pk)


@staff_panel_required
@require_POST
def user_activate(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save(update_fields=['is_active'])
    for s in user.suspensions.filter(is_active=True):
        s.lift(request.user)
    create_audit_log(
        request=request, action=AuditLog.Action.USER_ACTIVATE,
        message=f'Activated {user.email}', object_type='User', object_id=user.pk,
    )
    log_admin_activity(request, 'user_activate', '', 'User', user.pk)
    messages.success(request, f'{user.email} activated.')
    return redirect('staffpanel:user_detail', pk=pk)


@staff_panel_required
@require_POST
def user_verify_email(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.email_verified = True
    user.email_verification_token = ''
    user.save(update_fields=['email_verified', 'email_verification_token'])
    create_audit_log(
        request=request, action=AuditLog.Action.EMAIL_VERIFY,
        message=f'Admin verified email for {user.email}', object_type='User', object_id=user.pk,
    )
    log_admin_activity(request, 'email_verify', user.email, 'User', user.pk)
    try:
        from core.notify_service import alert_user
        alert_user(
            user, 'Email verified',
            'An administrator has verified your email address.',
            level=Notification.Level.SUCCESS, category=Notification.Category.SYSTEM,
        )
    except Exception:
        notify(user, 'Email verified', 'An administrator has verified your email address.')
    messages.success(request, f'Email verified for {user.email}.')
    return redirect('staffpanel:user_detail', pk=pk)


@staff_panel_required
@require_POST
def user_unverify_email(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.email_verified = False
    user.save(update_fields=['email_verified'])
    log_admin_activity(request, 'email_unverify', user.email, 'User', user.pk)
    messages.info(request, f'Email marked unverified for {user.email}.')
    return redirect('staffpanel:user_detail', pk=pk)


# ---------- KYC ----------
@staff_panel_required
def kyc_list(request):
    status = request.GET.get('status', 'pending')
    qs = KYCDocument.objects.select_related('user', 'reviewed_by')
    if status:
        qs = qs.filter(status=status)
    page = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'staffpanel/kyc.html', {
        'page': page, 'status': status, 'statuses': KYCDocument.Status.choices,
    })


@staff_panel_required
@require_POST
def kyc_approve(request, pk):
    doc = get_object_or_404(KYCDocument, pk=pk)
    doc.approve(request.user)
    notify(doc.user, 'KYC approved', 'Your identity verification was approved.',
           level=Notification.Level.SUCCESS, category=Notification.Category.KYC)
    create_audit_log(request=request, action=AuditLog.Action.KYC_APPROVE, object_id=doc.id, message='KYC approved')
    log_admin_activity(request, 'kyc_approve', '', 'KYCDocument', doc.id)
    messages.success(request, 'KYC approved.')
    return redirect('staffpanel:kyc')


@staff_panel_required
@require_POST
def kyc_reject(request, pk):
    doc = get_object_or_404(KYCDocument, pk=pk)
    reason = request.POST.get('reason', 'Documents not acceptable')
    doc.reject(request.user, reason=reason)
    notify(doc.user, 'KYC rejected', reason, level=Notification.Level.WARNING, category=Notification.Category.KYC)
    create_audit_log(request=request, action=AuditLog.Action.KYC_REJECT, object_id=doc.id, message=reason)
    log_admin_activity(request, 'kyc_reject', reason, 'KYCDocument', doc.id)
    messages.success(request, 'KYC rejected.')
    return redirect('staffpanel:kyc')


# ---------- Plans / Crypto / Transactions / Logs ----------
@staff_panel_required
def plan_list(request):
    plans = InvestmentPlan.objects.all()
    return render(request, 'staffpanel/plans.html', {'plans': plans})


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def plan_edit(request, pk=None):
    plan = get_object_or_404(InvestmentPlan, pk=pk) if pk else None
    if request.method == 'POST':
        from django.utils.text import slugify
        data = request.POST
        if plan is None:
            plan = InvestmentPlan()
        plan.name = data.get('name', plan.name if plan else 'plan') or 'plan'
        # Model.save() also slugifies; set raw source for uniqueness handling
        plan.slug = slugify(data.get('slug') or plan.name)[:160] or 'plan'
        plan.description = data.get('description', '')
        plan.short_description = data.get('short_description', '')
        plan.min_deposit = Decimal(data.get('min_deposit') or '50')
        plan.max_deposit = Decimal(data.get('max_deposit') or '10000')
        plan.duration_days = int(data.get('duration_days') or 30)
        plan.profit_rate_percent = Decimal(data.get('profit_rate_percent') or '1')
        plan.return_percent_min = Decimal(data.get('return_percent_min') or '0')
        plan.return_percent_max = Decimal(data.get('return_percent_max') or '0')
        plan.payout_frequency = data.get('payout_frequency') or 'daily'
        plan.profit_method = data.get('profit_method') or 'pct_principal'
        plan.risk_level = data.get('risk_level') or 'medium'
        plan.status = data.get('status') or 'active'
        plan.is_featured = data.get('is_featured') == 'on'
        plan.allow_auto_reinvest = data.get('allow_auto_reinvest') == 'on'
        plan.allow_manual_reinvest = data.get('allow_manual_reinvest') == 'on'
        plan.return_principal = data.get('return_principal') == 'on'
        plan.save()
        log_admin_activity(request, 'plan_save', plan.name, 'InvestmentPlan', plan.id)
        messages.success(request, 'Plan saved.')
        return redirect('staffpanel:plans')
    return render(request, 'staffpanel/plan_form.html', {
        'plan': plan,
        'profit_methods': InvestmentPlan.ProfitMethod.choices,
        'payout_freqs': InvestmentPlan.PayoutFrequency.choices,
        'risk_levels': InvestmentPlan.RiskLevel.choices,
        'statuses': InvestmentPlan.Status.choices,
    })


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def crypto_list(request):
    cryptos = Cryptocurrency.objects.all()
    if request.method == 'POST':
        pk = request.POST.get('pk')
        crypto = get_object_or_404(Cryptocurrency, pk=pk)
        crypto.deposit_address = request.POST.get('deposit_address', crypto.deposit_address)
        crypto.is_active = request.POST.get('is_active') == 'on'
        crypto.min_deposit = Decimal(request.POST.get('min_deposit') or crypto.min_deposit)
        crypto.min_withdrawal = Decimal(request.POST.get('min_withdrawal') or crypto.min_withdrawal)
        crypto.max_withdrawal = Decimal(request.POST.get('max_withdrawal') or crypto.max_withdrawal)
        crypto.withdrawal_fee = Decimal(request.POST.get('withdrawal_fee') or crypto.withdrawal_fee)
        if request.POST.get('usd_price') not in (None, ''):
            crypto.usd_price = Decimal(request.POST.get('usd_price') or crypto.usd_price)
        crypto.save()
        log_admin_activity(request, 'crypto_update', crypto.symbol, 'Cryptocurrency', crypto.pk)
        messages.success(request, f'{crypto.symbol} updated.')
        return redirect('staffpanel:cryptos')
    return render(request, 'staffpanel/cryptos.html', {'cryptos': cryptos})


@staff_panel_required
def transaction_list(request):
    q = request.GET.get('q', '').strip()
    tx_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    qs = Transaction.objects.select_related('user', 'administrator')
    if q:
        qs = qs.filter(
            Q(user__email__icontains=q) | Q(tx_hash__icontains=q) | Q(id__icontains=q) | Q(wallet_address__icontains=q)
        )
    if tx_type:
        qs = qs.filter(tx_type=tx_type)
    if status:
        qs = qs.filter(status=status)
    page = Paginator(qs, 40).get_page(request.GET.get('page'))
    from wallets.display import annotate_transactions
    annotate_transactions(page.object_list, use_user_pref=True)
    return render(request, 'staffpanel/transactions.html', {
        'page': page, 'q': q, 'tx_type': tx_type, 'status': status,
        'tx_types': Transaction.TxType.choices, 'statuses': Transaction.Status.choices,
    })


@staff_panel_required
def audit_logs(request):
    q = request.GET.get('q', '').strip()
    action = request.GET.get('action', '')
    qs = AuditLog.objects.select_related('user')
    if q:
        qs = qs.filter(Q(user__email__icontains=q) | Q(message__icontains=q) | Q(ip_address__icontains=q))
    if action:
        qs = qs.filter(action=action)
    page = Paginator(qs, 40).get_page(request.GET.get('page'))
    return render(request, 'staffpanel/audit_logs.html', {
        'page': page, 'q': q, 'action': action, 'actions': AuditLog.Action.choices,
    })


@staff_panel_required
def admin_activity(request):
    page = Paginator(AdminActivityLog.objects.select_related('admin'), 40).get_page(request.GET.get('page'))
    return render(request, 'staffpanel/admin_activity.html', {'page': page})


@staff_panel_required
def login_history(request):
    q = request.GET.get('q', '').strip()
    qs = LoginHistory.objects.select_related('user')
    if q:
        qs = qs.filter(
            Q(user__email__icontains=q)
            | Q(email_attempted__icontains=q)
            | Q(ip_address__icontains=q)
            | Q(city__icontains=q)
            | Q(country__icontains=q)
            | Q(region__icontains=q)
            | Q(timezone_name__icontains=q)
        )
    if request.GET.get('suspicious') == '1':
        qs = qs.filter(is_suspicious=True)
    page = Paginator(qs, 40).get_page(request.GET.get('page'))
    return render(request, 'staffpanel/login_history.html', {'page': page, 'q': q})


@staff_panel_required
def wallets_overview(request):
    from wallets.display import format_amount_for_code, get_default_display_code

    wallets = list(Wallet.objects.select_related('user').order_by('-balance')[:100])
    for w in wallets:
        code = get_default_display_code(w.user)
        w.bal_display = format_amount_for_code(w.balance, code)
        w.profit_display = format_amount_for_code(w.total_profit, code)
        w.display_currency = code
    totals = Wallet.objects.aggregate(
        bal=Sum('balance'), profit=Sum('total_profit'), dep=Sum('total_deposited'),
    )
    totals_fmt = {
        'bal': format_amount_for_code(totals['bal'] or 0, 'USD')['label'],
        'profit': format_amount_for_code(totals['profit'] or 0, 'USD')['label'],
        'dep': format_amount_for_code(totals['dep'] or 0, 'USD')['label'],
    }
    return render(request, 'staffpanel/wallets.html', {
        'wallets': wallets,
        'totals': totals,
        'totals_fmt': totals_fmt,
    })


@staff_panel_required
def referrals_admin(request):
    program = ReferralProgram.get_active()
    commissions = ReferralCommission.objects.select_related('referrer', 'referred_user')[:50]
    leaders = (
        User.objects.filter(referral_earnings__gt=0)
        .order_by('-referral_earnings')[:20]
    )
    if request.method == 'POST':
        pct = Decimal(request.POST.get('commission_percent') or (program.commission_percent if program else '5'))
        commission_on = request.POST.get('commission_on') or 'deposit'
        is_active = request.POST.get('is_active') == 'on'
        l2 = Decimal(request.POST.get('level2_percent') or (program.level2_percent if program else '0'))
        l3 = Decimal(request.POST.get('level3_percent') or (program.level3_percent if program else '0'))
        max_levels = int(request.POST.get('max_levels') or (program.max_levels if program else 1))
        max_levels = max(1, min(3, max_levels))
        min_dep = Decimal(request.POST.get('min_deposit_for_commission') or (program.min_deposit_for_commission if program else '0'))
        if program:
            program.commission_percent = pct
            program.level1_percent = pct  # always apply on deposit
            program.level2_percent = l2
            program.level3_percent = l3
            program.max_levels = max_levels
            program.min_deposit_for_commission = min_dep
            program.commission_on = commission_on
            program.is_active = is_active
            program.save()
            messages.success(
                request,
                f'Referral program updated — Level 1 commission is now {pct}% on every {commission_on}.',
            )
        else:
            ReferralProgram.objects.create(
                name='Standard Referral',
                commission_percent=pct,
                level1_percent=pct,
                level2_percent=l2,
                level3_percent=l3,
                max_levels=max_levels,
                min_deposit_for_commission=min_dep,
                commission_on=commission_on,
                is_active=is_active,
            )
            messages.success(request, f'Referral program created at {pct}%.')
        return redirect('staffpanel:referrals')
    from referrals.services import get_program_rates
    live = get_program_rates(program)
    return render(request, 'staffpanel/referrals.html', {
        'program': program,
        'commissions': commissions,
        'leaders': leaders,
        'live_rates': live,
    })


@staff_panel_required
def notifications_center(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        audience = request.POST.get('audience', 'all')
        level = request.POST.get('level', 'info')
        if title and message:
            users = User.objects.filter(is_active=True)
            if audience == 'kyc':
                users = users.filter(is_kyc_verified=True)
            count = 0
            for u in users.iterator():
                notify(u, title, message, level=level, category=Notification.Category.ANNOUNCEMENT)
                count += 1
            Announcement.objects.create(
                title=title, message=message, level=level, created_by=request.user, is_active=True,
            )
            log_admin_activity(request, 'broadcast', f'{count} users', extra={'title': title})
            messages.success(request, f'Notification sent to {count} users.')
            return redirect('staffpanel:notifications')
    recent = Notification.objects.select_related('user').order_by('-created_at')[:40]
    announcements = Announcement.objects.all()[:20]
    return render(request, 'staffpanel/notifications.html', {
        'recent': recent, 'announcements': announcements,
    })


@staff_panel_required
def reports(request):
    days = int(request.GET.get('days') or 30)
    since = timezone.now() - timedelta(days=days)
    deposits = Deposit.objects.filter(status=Deposit.Status.APPROVED, reviewed_at__gte=since)
    withdrawals = Withdrawal.objects.filter(status=Withdrawal.Status.PAID, paid_at__gte=since)
    investments = Investment.objects.filter(created_at__gte=since)
    registrations = User.objects.filter(date_joined__gte=since)

    deposit_rows = list(
        deposits.annotate(day=TruncDate('reviewed_at')).values('day')
        .annotate(total=Sum('credit_amount'), count=Count('id')).order_by('day')
    )
    summary = {
        'deposits_sum': deposits.aggregate(t=Sum('credit_amount'))['t'] or 0,
        'deposits_count': deposits.count(),
        'withdrawals_sum': withdrawals.aggregate(t=Sum('amount'))['t'] or 0,
        'withdrawals_count': withdrawals.count(),
        'investments_sum': investments.aggregate(t=Sum('amount'))['t'] or 0,
        'investments_count': investments.count(),
        'registrations': registrations.count(),
        'days': days,
    }
    chart_labels = [str(r['day']) for r in deposit_rows]
    chart_values = [float(r['total'] or 0) for r in deposit_rows]

    export = request.GET.get('export')
    if export:
        headers = ['Date', 'Deposits total', 'Deposit count']
        rows = [(str(r['day']), r['total'] or 0, r['count']) for r in deposit_rows]
        fname = f'revenue_{days}d'
        if export == 'csv':
            return export_csv(f'{fname}.csv', headers, rows)
        if export == 'xlsx':
            return export_excel(f'{fname}.xlsx', headers, rows, 'Revenue')
        if export == 'pdf':
            return export_pdf(f'{fname}.pdf', f'Revenue last {days} days', headers, rows)

    return render(request, 'staffpanel/reports.html', {
        'summary': summary,
        'chart_labels': json.dumps(chart_labels),
        'chart_values': json.dumps(chart_values),
        'days': days,
    })


@staff_panel_required
def settings_view(request):
    cfg = SiteConfiguration.get_solo()
    if request.method == 'POST':
        cfg.site_name = request.POST.get('site_name', cfg.site_name)
        cfg.support_email = request.POST.get('support_email', cfg.support_email)
        cfg.min_withdrawal = Decimal(request.POST.get('min_withdrawal') or cfg.min_withdrawal)
        cfg.max_withdrawal = Decimal(request.POST.get('max_withdrawal') or cfg.max_withdrawal)
        cfg.referral_bonus_percent = Decimal(request.POST.get('referral_bonus_percent') or cfg.referral_bonus_percent)
        cfg.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        cfg.maintenance_message = request.POST.get('maintenance_message', cfg.maintenance_message)
        cfg.announcement = request.POST.get('announcement', cfg.announcement)
        cfg.session_timeout_minutes = int(request.POST.get('session_timeout_minutes') or 60)
        cfg.save()
        log_admin_activity(request, 'settings_update', 'Site configuration updated')
        messages.success(request, 'Settings saved.')
        return redirect('staffpanel:settings')
    rates = CurrencyRate.objects.all()
    return render(request, 'staffpanel/settings.html', {'cfg': cfg, 'rates': rates})


@staff_panel_required
def tickets_list(request):
    status = request.GET.get('status', '')
    qs = SupportTicket.objects.select_related('user', 'assigned_to')
    if status:
        qs = qs.filter(status=status)
    page = Paginator(qs, 25).get_page(request.GET.get('page'))
    return render(request, 'staffpanel/tickets.html', {
        'page': page, 'status': status, 'statuses': SupportTicket.Status.choices,
    })


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def ticket_detail(request, pk):
    ticket = get_object_or_404(SupportTicket.objects.select_related('user'), pk=pk)
    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if body:
            TicketMessage.objects.create(
                ticket=ticket, sender=request.user, body=body, is_staff_reply=True,
            )
            ticket.status = SupportTicket.Status.WAITING
            ticket.assigned_to = request.user
            ticket.save(update_fields=['status', 'assigned_to', 'updated_at'])
            notify(ticket.user, 'Support reply', f'Re: {ticket.subject}', category=Notification.Category.SYSTEM)
            messages.success(request, 'Reply sent.')
            return redirect('staffpanel:ticket_detail', pk=pk)
        new_status = request.POST.get('status')
        if new_status in dict(SupportTicket.Status.choices):
            ticket.status = new_status
            ticket.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Status updated.')
            return redirect('staffpanel:ticket_detail', pk=pk)
    return render(request, 'staffpanel/ticket_detail.html', {
        'ticket': ticket, 'messages_list': ticket.messages.select_related('sender'),
        'statuses': SupportTicket.Status.choices,
    })


@staff_panel_required
def cms_pages(request):
    pages = CMSPage.objects.all()
    faqs = FAQ.objects.all()
    return render(request, 'staffpanel/cms.html', {'pages': pages, 'faqs': faqs})
