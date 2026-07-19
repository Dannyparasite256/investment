"""Feature-pack APIs: bootstrap, goals, promos, push, trust, fraud, broadcast, CSAT."""
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from io import StringIO
import csv

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ActivityEvent
from cms.models import Announcement, FAQ
from core.models import SiteConfiguration
from core.platform_models import (
    BroadcastCampaign,
    CalculatorScenario,
    CannedReply,
    PromoCode,
    PushSubscription,
    SavingsGoal,
    TicketCSAT,
    UserFraudScore,
    VIPTier,
)
from core.promo import compute_bonus, validate_promo
from core.vip import get_user_tier, user_total_invested
from investments.models import Earning, Investment, InvestmentPlan
from notifications.models import Notification, notify
from staffpanel.permissions import user_is_staff_panel
from support.models import SupportTicket, TicketMessage
from transactions.models import Deposit, Withdrawal
from wallets.models import Wallet

User = get_user_model()


class IsStaffPanel(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and user_is_staff_panel(request.user)


class BootstrapView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cfg = SiteConfiguration.get_solo()
        user = request.user if request.user.is_authenticated else None
        flags = cfg.feature_flags if isinstance(cfg.feature_flags, dict) else {}
        flags.setdefault('goals', True)
        flags.setdefault('trust_center', True)
        flags.setdefault('onboarding', True)
        flags.setdefault('promos', True)
        data = {
            'site_name': cfg.site_name,
            'support_email': cfg.support_email,
            'maintenance_mode': cfg.maintenance_mode,
            'maintenance_message': cfg.maintenance_message,
            'announcement': cfg.announcement,
            'risk_disclaimer': cfg.risk_disclaimer,
            'large_withdraw_threshold': str(cfg.large_withdraw_threshold),
            'support_sla_hours': cfg.support_sla_hours,
            'push_enabled': bool(cfg.push_enabled),
            'feature_flags': flags,
            'min_withdrawal': str(cfg.min_withdrawal),
            'max_withdrawal': str(cfg.max_withdrawal),
        }
        if user:
            data['user'] = {
                'tour_completed': bool(getattr(user, 'tour_completed', False)),
                'is_kyc_verified': bool(user.is_kyc_verified),
                'two_factor_enabled': bool(user.two_factor_enabled),
                'email_verified': bool(user.email_verified),
                'preferred_language': user.preferred_language or 'en',
            }
            data['onboarding'] = {
                'has_deposit': Deposit.objects.filter(user=user, status=Deposit.Status.APPROVED).exists(),
                'has_investment': Investment.objects.filter(user=user).exists(),
                'kyc_done': bool(user.is_kyc_verified),
                'two_fa_done': bool(user.two_factor_enabled),
                'tour_completed': bool(getattr(user, 'tour_completed', False)),
            }
        return Response(data)


class AnnouncementsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        qs = Announcement.objects.filter(is_active=True)
        items = []
        for a in qs[:50]:
            if a.starts_at and a.starts_at > now:
                continue
            if a.ends_at and a.ends_at < now:
                continue
            items.append({
                'id': str(a.id),
                'title': a.title,
                'message': a.message,
                'level': a.level,
                'created_at': a.created_at,
            })
        cfg = SiteConfiguration.get_solo()
        if cfg.announcement:
            items.insert(0, {
                'id': 'site',
                'title': 'Site notice',
                'message': cfg.announcement,
                'level': 'info',
                'created_at': cfg.updated_at,
            })
        return Response({'results': items})


class CompleteTourView(APIView):
    def post(self, request):
        request.user.tour_completed = True
        request.user.save(update_fields=['tour_completed'])
        return Response({'ok': True, 'tour_completed': True})


class SocialProofView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        recent = Earning.objects.select_related('user').order_by('-created_at')[:12]
        cards = []
        for e in recent:
            country = (e.user.country_code or e.user.country or 'XX')[:2].upper() or 'XX'
            cards.append({
                'label': f'Investor · {country}',
                'amount': str(e.amount),
                'when': e.created_at,
            })
        return Response({'results': cards})


class PromoValidateView(APIView):
    def post(self, request):
        code = (request.data.get('code') or '').strip()
        try:
            amount = Decimal(str(request.data.get('amount') or 0))
        except (InvalidOperation, TypeError):
            amount = Decimal('0')
        from core.promo import PromoError
        try:
            promo = validate_promo(code, request.user, amount)
            bonus = compute_bonus(promo, amount)
            return Response({
                'ok': True,
                'code': promo.code,
                'bonus_amount': str(bonus),
                'description': promo.description,
            })
        except PromoError as exc:
            return Response({'ok': False, 'detail': str(exc)}, status=400)


class GoalsView(APIView):
    def get(self, request):
        goals = SavingsGoal.objects.filter(user=request.user)
        return Response({
            'results': [{
                'id': str(g.id),
                'title': g.title,
                'target_amount': str(g.target_amount),
                'current_amount': str(g.current_amount),
                'progress_pct': g.progress_pct,
                'deadline': g.deadline,
                'is_completed': g.is_completed,
                'notes': g.notes,
                'created_at': g.created_at,
            } for g in goals]
        })

    def post(self, request):
        title = (request.data.get('title') or '').strip()
        try:
            target = Decimal(str(request.data.get('target_amount') or 0))
        except (InvalidOperation, TypeError):
            return Response({'detail': 'Invalid target'}, status=400)
        if not title or target <= 0:
            return Response({'detail': 'Title and positive target required'}, status=400)
        g = SavingsGoal.objects.create(
            user=request.user, title=title, target_amount=target,
            deadline=request.data.get('deadline') or None,
            notes=(request.data.get('notes') or '')[:255],
        )
        return Response({
            'id': str(g.id), 'title': g.title, 'target_amount': str(g.target_amount),
            'current_amount': str(g.current_amount), 'progress_pct': g.progress_pct,
        }, status=201)


class GoalDetailView(APIView):
    def delete(self, request, pk):
        SavingsGoal.objects.filter(pk=pk, user=request.user).delete()
        return Response(status=204)

    def patch(self, request, pk):
        g = SavingsGoal.objects.filter(pk=pk, user=request.user).first()
        if not g:
            return Response({'detail': 'Not found'}, status=404)
        if 'title' in request.data:
            g.title = str(request.data['title'])[:120]
        if 'is_completed' in request.data:
            g.is_completed = bool(request.data['is_completed'])
        g.save()
        return Response({'id': str(g.id), 'title': g.title, 'is_completed': g.is_completed})


class CalculatorScenariosView(APIView):
    def get(self, request):
        rows = CalculatorScenario.objects.filter(user=request.user)[:30]
        return Response({
            'results': [{
                'id': str(s.id), 'label': s.label,
                'amount': str(s.amount), 'rate_percent': str(s.rate_percent),
                'duration_days': s.duration_days, 'estimated_profit': str(s.estimated_profit),
                'created_at': s.created_at,
            } for s in rows]
        })

    def post(self, request):
        label = (request.data.get('label') or 'Scenario').strip()[:100]
        try:
            amount = Decimal(str(request.data.get('amount') or 0))
            rate = Decimal(str(request.data.get('rate_percent') or 0))
            days = int(request.data.get('duration_days') or 30)
        except (InvalidOperation, TypeError, ValueError):
            return Response({'detail': 'Invalid numbers'}, status=400)
        profit = (amount * rate / Decimal('100')) * (Decimal(days) / Decimal('30'))
        s = CalculatorScenario.objects.create(
            user=request.user, label=label, amount=amount, rate_percent=rate,
            duration_days=days, estimated_profit=profit.quantize(Decimal('0.00000001')),
        )
        return Response({'id': str(s.id), 'label': s.label, 'estimated_profit': str(s.estimated_profit)}, status=201)


class PushSubscribeView(APIView):
    def post(self, request):
        endpoint = (request.data.get('endpoint') or '').strip()
        if not endpoint:
            return Response({'detail': 'endpoint required'}, status=400)
        keys = request.data.get('keys') or {}
        sub, _ = PushSubscription.objects.update_or_create(
            user=request.user, endpoint=endpoint[:500],
            defaults={
                'p256dh': (keys.get('p256dh') or '')[:255],
                'auth': (keys.get('auth') or '')[:255],
                'user_agent': (request.META.get('HTTP_USER_AGENT') or '')[:255],
                'is_active': True,
            },
        )
        return Response({'ok': True, 'id': str(sub.id)})

    def delete(self, request):
        endpoint = (request.data.get('endpoint') or '').strip()
        PushSubscription.objects.filter(user=request.user, endpoint=endpoint).update(is_active=False)
        return Response({'ok': True})


class TrustCenterView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        since = timezone.now() - timedelta(days=30)
        paid = Withdrawal.objects.filter(status=Withdrawal.Status.PAID, updated_at__gte=since)
        total_paid = paid.aggregate(t=Sum('amount'))['t'] or 0
        pending_w = Withdrawal.objects.filter(status=Withdrawal.Status.PENDING).count()
        approved_d = Deposit.objects.filter(status=Deposit.Status.APPROVED, reviewed_at__gte=since).count()
        return Response({
            'period_days': 30,
            'withdrawals_paid_count': paid.count(),
            'withdrawals_paid_volume': str(total_paid),
            'pending_withdrawals': pending_w,
            'deposits_approved_count': approved_d,
            'active_investors': User.objects.filter(investments__status='active').distinct().count(),
            'disclaimer': SiteConfiguration.get_solo().risk_disclaimer,
        })


class CannedRepliesView(APIView):
    permission_classes = [IsStaffPanel]

    def get(self, request):
        rows = CannedReply.objects.filter(is_active=True)
        return Response({
            'results': [{
                'id': str(r.id), 'title': r.title, 'body': r.body, 'category': r.category,
            } for r in rows]
        })

    def post(self, request):
        title = (request.data.get('title') or '').strip()
        body = (request.data.get('body') or '').strip()
        if not title or not body:
            return Response({'detail': 'title and body required'}, status=400)
        r = CannedReply.objects.create(
            title=title[:100], body=body,
            category=(request.data.get('category') or 'general')[:50],
        )
        return Response({'id': str(r.id), 'title': r.title}, status=201)


class TicketCSATView(APIView):
    def post(self, request, pk):
        ticket = SupportTicket.objects.filter(pk=pk, user=request.user).first()
        if not ticket:
            return Response({'detail': 'Not found'}, status=404)
        try:
            score = int(request.data.get('score') or 0)
        except (TypeError, ValueError):
            return Response({'detail': 'score 1-5 required'}, status=400)
        if score < 1 or score > 5:
            return Response({'detail': 'score 1-5 required'}, status=400)
        csat, _ = TicketCSAT.objects.update_or_create(
            ticket=ticket,
            defaults={
                'user': request.user,
                'score': score,
                'comment': (request.data.get('comment') or '')[:500],
            },
        )
        return Response({'ok': True, 'score': csat.score})


class StaffFraudView(APIView):
    permission_classes = [IsStaffPanel]

    def get(self, request):
        from accounts.security_models import LoginHistory
        rows = []
        for u in User.objects.filter(is_active=True).order_by('-date_joined')[:100]:
            flags = []
            score = 0
            logins = LoginHistory.objects.filter(user=u).order_by('-created_at')[:20]
            ips = {x.ip_address for x in logins if x.ip_address}
            if len(ips) >= 5:
                flags.append('many_ips')
                score += 15
            # same IP multi-account
            if ips:
                shared = LoginHistory.objects.filter(ip_address__in=list(ips)[:3]).exclude(user=u).values('user').distinct().count()
                if shared >= 2:
                    flags.append('shared_ip_accounts')
                    score += 25
            last_dep = Deposit.objects.filter(user=u, status=Deposit.Status.APPROVED).order_by('-reviewed_at').first()
            last_wd = Withdrawal.objects.filter(user=u).order_by('-created_at').first()
            if last_dep and last_wd and last_dep.reviewed_at and last_wd.created_at:
                if last_wd.created_at - last_dep.reviewed_at < timedelta(hours=2):
                    flags.append('rapid_withdraw_after_deposit')
                    score += 30
            if not u.is_kyc_verified and Withdrawal.objects.filter(user=u).exists():
                flags.append('withdraw_without_kyc')
                score += 20
            if flags:
                UserFraudScore.objects.update_or_create(
                    user=u, defaults={'score': min(100, score), 'flags': flags},
                )
                rows.append({
                    'user_id': u.pk, 'email': u.email, 'score': min(100, score),
                    'flags': flags, 'is_kyc_verified': u.is_kyc_verified,
                })
        rows.sort(key=lambda x: -x['score'])
        return Response({'results': rows[:50]})


class StaffBroadcastView(APIView):
    permission_classes = [IsStaffPanel]

    def post(self, request):
        title = (request.data.get('title') or '').strip()
        message = (request.data.get('message') or '').strip()
        vip_slug = (request.data.get('vip_slug') or '').strip()
        if not title or not message:
            return Response({'detail': 'title and message required'}, status=400)
        users = User.objects.filter(is_active=True)
        if vip_slug:
            tier = VIPTier.objects.filter(slug=vip_slug, is_active=True).first()
            if tier:
                # filter by invested amount
                ids = []
                for u in users.iterator():
                    if user_total_invested(u) >= tier.min_total_invested:
                        ids.append(u.pk)
                users = User.objects.filter(pk__in=ids)
        count = 0
        for u in users.iterator():
            notify(u, title, message, category=Notification.Category.ANNOUNCEMENT, link='/app/announcements')
            count += 1
        camp = BroadcastCampaign.objects.create(
            title=title, message=message, vip_slug=vip_slug,
            sent_count=count, created_by=request.user,
        )
        return Response({'ok': True, 'sent_count': count, 'id': str(camp.id)})


class StaffExportView(APIView):
    permission_classes = [IsStaffPanel]

    def get(self, request):
        kind = request.query_params.get('kind') or 'users'
        buf = StringIO()
        w = csv.writer(buf)
        if kind == 'deposits':
            w.writerow(['id', 'user', 'amount', 'status', 'created_at'])
            for d in Deposit.objects.select_related('user').order_by('-created_at')[:2000]:
                w.writerow([d.id, d.user.email, d.amount, d.status, d.created_at.isoformat()])
        elif kind == 'withdrawals':
            w.writerow(['id', 'user', 'amount', 'status', 'priority', 'created_at'])
            for x in Withdrawal.objects.select_related('user').order_by('-priority', '-created_at')[:2000]:
                w.writerow([x.id, x.user.email, x.amount, x.status, x.priority, x.created_at.isoformat()])
        else:
            w.writerow(['id', 'email', 'kyc', 'joined', 'balance'])
            for u in User.objects.all().order_by('-date_joined')[:5000]:
                wal, _ = Wallet.objects.get_or_create(user=u)
                w.writerow([u.pk, u.email, u.is_kyc_verified, u.date_joined.isoformat(), wal.balance])
        resp = HttpResponse(buf.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = f'attachment; filename="{kind}-export.csv"'
        return resp


class SupportTriageView(APIView):
    """Bot triage: FAQ suggestions before opening a ticket."""
    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        faqs = FAQ.objects.filter(is_published=True)
        if q:
            faqs = faqs.filter(Q(question__icontains=q) | Q(answer__icontains=q) | Q(category__icontains=q))
        return Response({
            'results': [{
                'id': str(f.id), 'question': f.question, 'answer': f.answer, 'category': f.category,
            } for f in faqs[:8]]
        })
