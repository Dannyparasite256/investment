"""UX feature views: global search, receipts, statements, risk questionnaire."""
from decimal import Decimal
from io import StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from investments.models import Investment, InvestmentPlan
from support.models import SupportTicket
from transactions.models import Deposit, Transaction, Withdrawal


@login_required
@require_GET
def global_search(request):
    """Search deposits, withdrawals, investments, tickets for the current user."""
    q = (request.GET.get('q') or '').strip()
    results = []
    if len(q) >= 2:
        user = request.user
        for d in Deposit.objects.filter(user=user).filter(
            Q(transaction_hash__icontains=q) | Q(id__icontains=q) | Q(cryptocurrency__symbol__icontains=q)
        )[:8]:
            results.append({
                'type': 'deposit',
                'title': f'Deposit {d.amount} {d.cryptocurrency.symbol}',
                'subtitle': d.get_status_display(),
                'url': f'/transactions/deposits/{d.pk}/',
                'icon': 'bi-download',
            })
        for w in Withdrawal.objects.filter(user=user).filter(
            Q(wallet_address__icontains=q) | Q(id__icontains=q) | Q(cryptocurrency__symbol__icontains=q)
        )[:8]:
            results.append({
                'type': 'withdrawal',
                'title': f'Withdraw {w.amount} {w.cryptocurrency.symbol}',
                'subtitle': w.get_status_display(),
                'url': '/transactions/withdrawals/',
                'icon': 'bi-upload',
            })
        for inv in Investment.objects.filter(user=user).select_related('plan').filter(
            Q(plan__name__icontains=q) | Q(id__icontains=q)
        )[:8]:
            results.append({
                'type': 'investment',
                'title': inv.plan.name,
                'subtitle': f'{inv.amount} · {inv.get_status_display()}',
                'url': f'/investments/{inv.pk}/',
                'icon': 'bi-graph-up-arrow',
            })
        for plan in InvestmentPlan.objects.filter(status=InvestmentPlan.Status.ACTIVE).filter(
            Q(name__icontains=q) | Q(slug__icontains=q)
        )[:6]:
            results.append({
                'type': 'plan',
                'title': plan.name,
                'subtitle': (plan.short_description or 'Investment plan')[:80],
                'url': f'/investments/plan/{plan.slug}/',
                'icon': 'bi-lightning',
            })
        for t in SupportTicket.objects.filter(user=user).filter(
            Q(subject__icontains=q) | Q(id__icontains=q)
        )[:5]:
            results.append({
                'type': 'ticket',
                'title': t.subject,
                'subtitle': t.get_status_display(),
                'url': f'/support/{t.pk}/',
                'icon': 'bi-headset',
            })
        # Static destinations
        static_hits = [
            ('dashboard', 'Dashboard', '/dashboard/', 'bi-grid-1x2'),
            ('wallet', 'Wallet', '/wallets/', 'bi-wallet2'),
            ('deposit', 'New deposit', '/transactions/deposits/new/', 'bi-download'),
            ('withdraw', 'Withdraw', '/transactions/withdrawals/new/', 'bi-upload'),
            ('referrals', 'Referrals', '/referrals/', 'bi-people'),
            ('portfolio', 'Portfolio performance', '/portfolio/', 'bi-pie-chart'),
            ('vip', 'VIP status', '/vip/', 'bi-award'),
            ('activity', 'Activity', '/activity/', 'bi-activity'),
            ('markets', 'Markets', '/markets/', 'bi-bar-chart-line'),
            ('profile', 'Profile', '/accounts/profile/', 'bi-person'),
            ('kyc', 'KYC', '/accounts/kyc/', 'bi-shield-check'),
            ('statements', 'Statements', '/statements/', 'bi-file-earmark-text'),
            ('risk', 'Risk questionnaire', '/risk-quiz/', 'bi-clipboard-check'),
        ]
        ql = q.lower()
        for key, title, url, icon in static_hits:
            if ql in key or ql in title.lower():
                results.append({
                    'type': 'page',
                    'title': title,
                    'subtitle': 'Go to page',
                    'url': url,
                    'icon': icon,
                })

    if request.headers.get('Accept', '').find('application/json') >= 0 or request.GET.get('format') == 'json':
        return JsonResponse({'q': q, 'results': results[:25]})
    return render(request, 'core/search.html', {'q': q, 'results': results[:25]})


@login_required
@require_GET
def deposit_receipt(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk, user=request.user)
    return render(request, 'transactions/receipt.html', {
        'deposit': deposit,
        'kind': 'deposit',
        'title': 'Deposit receipt',
    })


@login_required
@require_GET
def withdraw_receipt(request, pk):
    withdrawal = get_object_or_404(Withdrawal, pk=pk, user=request.user)
    return render(request, 'transactions/receipt.html', {
        'withdrawal': withdrawal,
        'kind': 'withdrawal',
        'title': 'Withdrawal receipt',
    })


@login_required
@require_GET
def statement_export(request):
    """CSV statement of transactions for the user."""
    fmt = (request.GET.get('format') or 'html').lower()
    txs = Transaction.objects.filter(user=request.user).order_by('-created_at')[:2000]
    if fmt == 'csv':
        buf = StringIO()
        buf.write('date,type,amount,fee,currency,status,reference\n')
        for t in txs:
            buf.write(
                f'{t.created_at.isoformat()},{t.tx_type},{t.amount},{t.fee},'
                f'{t.currency},{t.status},{t.reference_type}:{t.reference_id}\n'
            )
        resp = HttpResponse(buf.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = (
            f'attachment; filename="statement-{timezone.now().date()}.csv"'
        )
        return resp
    deposits = Deposit.objects.filter(user=request.user).count()
    withdrawals = Withdrawal.objects.filter(user=request.user).count()
    investments = Investment.objects.filter(user=request.user).count()
    return render(request, 'core/statements.html', {
        'txs': txs[:50],
        'deposits': deposits,
        'withdrawals': withdrawals,
        'investments': investments,
    })


RISK_QUESTIONS = [
    {
        'id': 'experience',
        'q': 'How experienced are you with crypto investing?',
        'options': [
            ('0', 'Beginner'),
            ('1', 'Some experience'),
            ('2', 'Experienced'),
            ('3', 'Professional'),
        ],
    },
    {
        'id': 'horizon',
        'q': 'What is your typical investment horizon?',
        'options': [
            ('0', 'Under 30 days'),
            ('1', '1–3 months'),
            ('2', '3–12 months'),
            ('3', 'Over 1 year'),
        ],
    },
    {
        'id': 'loss',
        'q': 'How would you react to a 20% temporary drop?',
        'options': [
            ('0', 'Sell immediately'),
            ('1', 'Worry but hold'),
            ('2', 'Hold calmly'),
            ('3', 'Buy more if I can'),
        ],
    },
    {
        'id': 'portion',
        'q': 'What portion of liquid assets would you invest here?',
        'options': [
            ('0', 'Less than 5%'),
            ('1', '5–15%'),
            ('2', '15–40%'),
            ('3', 'More than 40%'),
        ],
    },
    {
        'id': 'goal',
        'q': 'Primary goal?',
        'options': [
            ('0', 'Capital preservation'),
            ('1', 'Steady income'),
            ('2', 'Balanced growth'),
            ('3', 'Maximum growth'),
        ],
    },
]


@login_required
@require_http_methods(['GET', 'POST'])
def risk_questionnaire(request):
    result = None
    if request.method == 'POST':
        score = 0
        for item in RISK_QUESTIONS:
            score += int(request.POST.get(item['id']) or 0)
        if score <= 4:
            profile = 'Conservative'
            tip = 'Prefer lower-risk, shorter-duration plans and only invest spare capital.'
            color = '#22C55E'
        elif score <= 9:
            profile = 'Moderate'
            tip = 'A mix of steady and growth plans fits your profile. Diversify durations.'
            color = '#3B82F6'
        elif score <= 13:
            profile = 'Growth'
            tip = 'You can tolerate more volatility. Still size positions carefully.'
            color = '#8B5CF6'
        else:
            profile = 'Aggressive'
            tip = 'High risk appetite. Cap any single plan and never invest more than you can lose.'
            color = '#EF4444'
        result = {'score': score, 'profile': profile, 'tip': tip, 'color': color}
        try:
            request.user.notes_internal = (
                (request.user.notes_internal or '') +
                f'\n[Risk quiz {timezone.now().date()}] {profile} score={score}'
            )
            # store lightly on user without breaking schema
            if hasattr(request.user, 'risk_score'):
                request.user.risk_score = min(100, score * 6)
                request.user.save(update_fields=['notes_internal', 'risk_score'])
            else:
                request.user.save(update_fields=['notes_internal'])
        except Exception:
            pass
        messages.success(request, f'Risk profile: {profile}')
    return render(request, 'core/risk_quiz.html', {
        'questions': RISK_QUESTIONS,
        'result': result,
    })


@login_required
@require_GET
def fee_preview_api(request):
    """Live withdrawal fee estimate for the withdraw form."""
    from core.vip import apply_withdrawal_fee
    from wallets.models import Cryptocurrency

    amount = Decimal(str(request.GET.get('amount') or 0))
    crypto_id = request.GET.get('crypto')
    crypto_fee = Decimal('0')
    symbol = 'USD'
    if crypto_id:
        c = Cryptocurrency.objects.filter(pk=crypto_id, is_active=True).first()
        if c:
            crypto_fee = Decimal(str(c.withdrawal_fee or 0))
            symbol = c.symbol
    fee_total, pct = apply_withdrawal_fee(request.user, amount, crypto_fee)
    net = amount - fee_total if amount > fee_total else Decimal('0')
    return JsonResponse({
        'ok': True,
        'amount': str(amount),
        'fee': str(fee_total),
        'fee_percent': str(pct),
        'crypto_fee': str(crypto_fee),
        'net': str(net),
        'symbol': symbol,
    })


@require_GET
def live_prices_api(request):
    """
    Public-ish JSON ticker for the UI (login not required for market chips,
    but rate-limited by cache). Refreshes from free APIs when stale.
    """
    from core.price_feed import get_ticker_snapshot, refresh_all_prices

    if request.GET.get('refresh') == '1':
        try:
            refresh_all_prices(force=True)
        except Exception:
            pass
    tick = get_ticker_snapshot()
    return JsonResponse({'ok': True, **tick})


@login_required
@require_GET
def command_palette_data(request):
    """Nav destinations for ⌘K / Ctrl+K palette."""
    items = [
        {'title': 'Dashboard', 'url': '/dashboard/', 'icon': 'bi-grid-1x2', 'keywords': 'home'},
        {'title': 'New deposit', 'url': '/transactions/deposits/new/', 'icon': 'bi-download', 'keywords': 'fund'},
        {'title': 'Withdraw', 'url': '/transactions/withdrawals/new/', 'icon': 'bi-upload', 'keywords': 'cash out'},
        {'title': 'Investment plans', 'url': '/investments/plans/', 'icon': 'bi-graph-up-arrow', 'keywords': 'invest'},
        {'title': 'My portfolio', 'url': '/investments/my/', 'icon': 'bi-briefcase', 'keywords': 'positions'},
        {'title': 'Wallet', 'url': '/wallets/', 'icon': 'bi-wallet2', 'keywords': 'balance'},
        {'title': 'History', 'url': '/transactions/history/', 'icon': 'bi-clock-history', 'keywords': 'ledger'},
        {'title': 'Markets', 'url': '/markets/', 'icon': 'bi-bar-chart-line', 'keywords': 'forex crypto'},
        {'title': 'Referrals', 'url': '/referrals/', 'icon': 'bi-people', 'keywords': 'affiliate'},
        {'title': 'VIP status', 'url': '/vip/', 'icon': 'bi-award', 'keywords': 'tier'},
        {'title': 'Portfolio performance', 'url': '/portfolio/', 'icon': 'bi-pie-chart', 'keywords': 'equity'},
        {'title': 'Activity', 'url': '/activity/', 'icon': 'bi-activity', 'keywords': 'timeline'},
        {'title': 'Watchlist', 'url': '/watchlist/', 'icon': 'bi-star', 'keywords': 'pairs'},
        {'title': 'Price alerts', 'url': '/alerts/', 'icon': 'bi-bell', 'keywords': 'notify'},
        {'title': 'Signals', 'url': '/signals/', 'icon': 'bi-broadcast', 'keywords': 'trading'},
        {'title': 'Statements', 'url': '/statements/', 'icon': 'bi-file-earmark-text', 'keywords': 'export csv'},
        {'title': 'Risk quiz', 'url': '/risk-quiz/', 'icon': 'bi-clipboard-check', 'keywords': 'profile'},
        {'title': 'Support', 'url': '/support/', 'icon': 'bi-headset', 'keywords': 'ticket help'},
        {'title': 'Profile', 'url': '/accounts/profile/', 'icon': 'bi-person', 'keywords': 'settings'},
        {'title': 'KYC', 'url': '/accounts/kyc/', 'icon': 'bi-shield-check', 'keywords': 'verify'},
        {'title': 'Calculator', 'url': '/investments/calculator/', 'icon': 'bi-calculator', 'keywords': 'profit'},
        {'title': 'Notifications', 'url': '/notifications/', 'icon': 'bi-bell', 'keywords': 'inbox'},
    ]
    if request.user.is_staff or request.user.is_superuser:
        items.extend([
            {'title': 'Staff panel', 'url': '/staff/', 'icon': 'bi-shield-lock', 'keywords': 'admin'},
            {'title': 'Staff deposits', 'url': '/staff/deposits/', 'icon': 'bi-inbox', 'keywords': 'approve'},
            {'title': 'Staff withdrawals', 'url': '/staff/withdrawals/', 'icon': 'bi-cash-stack', 'keywords': 'payout'},
            {'title': 'Bulk match', 'url': '/staff/deposits/bulk-match/', 'icon': 'bi-intersect', 'keywords': 'hash'},
            {'title': 'SLA queue', 'url': '/staff/withdrawals/sla/', 'icon': 'bi-hourglass', 'keywords': 'priority'},
        ])
    return JsonResponse({'items': items})
