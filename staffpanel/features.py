"""Extra staff features: treasury, bulk match, SLA, risk, audit pack, backup, signals, promos."""
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import mail_admins
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from core.backup import create_backup
from core.models import AuditLog, SiteConfiguration
from core.platform_models import (
    GeoRule,
    PlatformBackup,
    PromoCode,
    TradingSignal,
    VIPTier,
    WebhookEndpoint,
)
from core.portfolio import snapshot_all_users
from core.risk import compute_risk_score
from staffpanel.exports import export_csv, export_excel, export_pdf
from staffpanel.permissions import staff_panel_required
from staffpanel.utils import log_admin_activity
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.models import Wallet

User = get_user_model()


@staff_panel_required
def treasury(request):
    """Platform liability / float overview."""
    wallets = Wallet.objects.aggregate(
        bal=Sum('balance'),
        locked=Sum('locked_balance'),
        profit=Sum('total_profit'),
        dep=Sum('total_deposited'),
        wd=Sum('total_withdrawn'),
        inv=Sum('total_invested'),
    )
    pending_dep = Deposit.objects.filter(
        status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION],
    ).aggregate(t=Sum('amount'), c=Count('id'))
    pending_wd = Withdrawal.objects.filter(
        status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.APPROVED, Withdrawal.Status.PROCESSING],
    ).aggregate(t=Sum('amount'), c=Count('id'))
    liability = (wallets['bal'] or 0) + (pending_wd['t'] or 0)
    return render(request, 'staffpanel/treasury.html', {
        'wallets': wallets,
        'pending_dep': pending_dep,
        'pending_wd': pending_wd,
        'liability': liability,
        'net_in': (wallets['dep'] or 0) - (wallets['wd'] or 0),
    })


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def bulk_deposit_match(request):
    """Paste tx hashes or amount lines to match pending deposits."""
    results = []
    if request.method == 'POST':
        raw = request.POST.get('payload', '')
        action = request.POST.get('action', 'preview')
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        for line in lines:
            # formats: hash OR amount hash
            parts = line.split()
            tx_hash = parts[-1]
            qs = Deposit.objects.filter(
                status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION],
                transaction_hash__iexact=tx_hash,
            )
            dep = qs.first()
            row = {'line': line, 'hash': tx_hash, 'deposit': dep, 'status': 'matched' if dep else 'no_match'}
            if dep and action == 'approve':
                try:
                    dep.approve(request.user, notes='Bulk match approve')
                    row['status'] = 'approved'
                    try:
                        from core.notify_service import alert_user
                        from referrals.services import process_referral_commission
                        alert_user(
                            dep.user, 'Deposit approved',
                            f'Deposit {dep.amount} {dep.cryptocurrency.symbol} approved.',
                            email=True, event_name='deposit.approved',
                        )
                        process_referral_commission(
                            dep.user, dep.credit_amount or dep.amount,
                            source='deposit', reference_type='deposit', reference_id=dep.id,
                        )
                    except Exception:
                        pass
                except Exception as exc:
                    row['status'] = f'error: {exc}'
            results.append(row)
        log_admin_activity(request, 'bulk_deposit_match', f'{len(results)} lines, action={action}')
        if action == 'approve':
            messages.success(request, f'Processed {len(results)} line(s).')
    return render(request, 'staffpanel/bulk_match.html', {'results': results})


@staff_panel_required
def withdrawal_sla_queue(request):
    now = timezone.now()
    qs = Withdrawal.objects.filter(
        status__in=[Withdrawal.Status.PENDING, Withdrawal.Status.APPROVED, Withdrawal.Status.PROCESSING],
    ).select_related('user', 'cryptocurrency').order_by('-priority', 'sla_deadline', 'created_at')
    items = []
    for w in qs[:100]:
        overdue = bool(w.sla_deadline and w.sla_deadline < now)
        items.append({'w': w, 'overdue': overdue})
    return render(request, 'staffpanel/sla_queue.html', {'items': items, 'now': now})


@staff_panel_required
def risk_dashboard(request):
    users = User.objects.filter(is_active=True).order_by('-risk_score', '-date_joined')[:50]
    # refresh top users if requested
    if request.GET.get('refresh') == '1':
        for u in User.objects.filter(is_active=True)[:200]:
            data = compute_risk_score(u)
            User.objects.filter(pk=u.pk).update(risk_score=data['score'])
        messages.success(request, 'Risk scores refreshed.')
        return redirect('staffpanel:risk')
    rows = []
    for u in users:
        data = compute_risk_score(u)
        rows.append({'user': u, **data})
    return render(request, 'staffpanel/risk.html', {'rows': rows})


@staff_panel_required
def compliance_export(request):
    """Export user/KYC/deposit/withdrawal pack by date range."""
    days = int(request.GET.get('days') or 30)
    since = timezone.now() - timedelta(days=days)
    fmt = request.GET.get('export') or 'csv'
    rows = []
    for d in Deposit.objects.filter(created_at__gte=since).select_related('user', 'cryptocurrency'):
        rows.append([
            'deposit', str(d.id), d.user.email, str(d.amount), d.cryptocurrency.symbol,
            d.status, d.transaction_hash, d.created_at.isoformat(),
        ])
    for w in Withdrawal.objects.filter(created_at__gte=since).select_related('user', 'cryptocurrency'):
        rows.append([
            'withdrawal', str(w.id), w.user.email, str(w.amount), w.cryptocurrency.symbol,
            w.status, w.wallet_address, w.created_at.isoformat(),
        ])
    headers = ['type', 'id', 'email', 'amount', 'currency', 'status', 'ref', 'created_at']
    fname = f'compliance_{days}d'
    if fmt == 'xlsx':
        return export_excel(f'{fname}.xlsx', headers, rows, 'Compliance')
    if fmt == 'pdf':
        return export_pdf(f'{fname}.pdf', f'Compliance pack {days}d', headers, rows)
    return export_csv(f'{fname}.csv', headers, rows)


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def backups(request):
    if request.method == 'POST':
        b = create_backup(user=request.user, notes=request.POST.get('notes', ''))
        log_admin_activity(request, 'backup_create', b.filename)
        messages.success(request, f'Backup created: {b.filename}')
        return redirect('staffpanel:backups')
    items = PlatformBackup.objects.all()[:50]
    return render(request, 'staffpanel/backups.html', {'items': items})


@staff_panel_required
@require_POST
def send_daily_digest(request):
    """Email admins a daily ops digest (also callable from celery)."""
    today = timezone.now().date()
    body = (
        f"Users today: {User.objects.filter(date_joined__date=today).count()}\n"
        f"Pending deposits: {Deposit.objects.filter(status=Deposit.Status.PENDING).count()}\n"
        f"Pending withdrawals: {Withdrawal.objects.filter(status=Withdrawal.Status.PENDING).count()}\n"
        f"Approved deposits today: {Deposit.objects.filter(status=Deposit.Status.APPROVED, reviewed_at__date=today).count()}\n"
    )
    mail_admins(f'{SiteConfiguration.get_solo().site_name} daily digest', body, fail_silently=True)
    # also snapshot portfolios
    n = snapshot_all_users()
    messages.success(request, f'Digest emailed to admins. Snapshots: {n}')
    log_admin_activity(request, 'daily_digest', body[:200])
    return redirect('staffpanel:reports')


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def signals_admin(request):
    if request.method == 'POST':
        TradingSignal.objects.create(
            title=request.POST.get('title', 'Signal'),
            symbol=request.POST.get('symbol', 'FX:EURUSD'),
            side=request.POST.get('side', 'hold'),
            entry_note=request.POST.get('entry_note', ''),
            target=request.POST.get('target', ''),
            stop_loss=request.POST.get('stop_loss', ''),
            is_published=request.POST.get('is_published') == 'on',
            created_by=request.user,
        )
        messages.success(request, 'Signal published.')
        return redirect('staffpanel:signals')
    signals = TradingSignal.objects.all()[:50]
    return render(request, 'staffpanel/signals.html', {'signals': signals})


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def promos_admin(request):
    if request.method == 'POST':
        PromoCode.objects.create(
            code=(request.POST.get('code') or '').strip().upper(),
            description=request.POST.get('description', ''),
            bonus_percent=Decimal(request.POST.get('bonus_percent') or '0'),
            bonus_fixed=Decimal(request.POST.get('bonus_fixed') or '0'),
            min_deposit=Decimal(request.POST.get('min_deposit') or '0'),
            max_uses=int(request.POST['max_uses']) if request.POST.get('max_uses') else None,
            is_active=True,
        )
        messages.success(request, 'Promo created.')
        return redirect('staffpanel:promos')
    promos = PromoCode.objects.all()[:50]
    return render(request, 'staffpanel/promos.html', {'promos': promos})


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def vip_admin(request):
    if request.method == 'POST':
        VIPTier.objects.update_or_create(
            slug=request.POST.get('slug') or 'bronze',
            defaults={
                'name': request.POST.get('name', 'Bronze'),
                'min_total_invested': Decimal(request.POST.get('min_total_invested') or '0'),
                'deposit_fee_percent': Decimal(request.POST.get('deposit_fee_percent') or '0'),
                'withdrawal_fee_percent': Decimal(request.POST.get('withdrawal_fee_percent') or '0'),
                'referral_bonus_boost': Decimal(request.POST.get('referral_bonus_boost') or '0'),
                'sort_order': int(request.POST.get('sort_order') or 0),
                'is_active': True,
            },
        )
        messages.success(request, 'VIP tier saved.')
        return redirect('staffpanel:vip')
    tiers = VIPTier.objects.all()
    return render(request, 'staffpanel/vip.html', {'tiers': tiers})


@staff_panel_required
@require_http_methods(['GET', 'POST'])
def geo_admin(request):
    rule = GeoRule.objects.first()
    if request.method == 'POST':
        if not rule:
            rule = GeoRule()
        rule.name = request.POST.get('name', 'Geo rules')
        rule.mode = request.POST.get('mode', 'block')
        rule.country_codes = request.POST.get('country_codes', '')
        rule.block_message = request.POST.get('block_message', rule.block_message)
        rule.is_active = request.POST.get('is_active') == 'on'
        rule.save()
        messages.success(request, 'Geo rules saved.')
        return redirect('staffpanel:geo')
    return render(request, 'staffpanel/geo.html', {'rule': rule})
