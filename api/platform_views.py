"""Platform API endpoints powering the Vue SPA (parity with Django UI features)."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ActivityEvent, KYCDocument
from api.platform_serializers import (
    ActivityEventSerializer,
    CMSPageSerializer,
    ChangePasswordSerializer,
    FAQSerializer,
    PriceAlertSerializer,
    ReferralCommissionSerializer,
    RegisterSerializer,
    SupportTicketCreateSerializer,
    SupportTicketSerializer,
    TicketMessageSerializer,
    TicketReplySerializer,
    TradingSignalSerializer,
    UserProfileSerializer,
    VIPTierSerializer,
    WatchlistSerializer,
    WalletAddressSerializer,
)
from api.serializers import UserSerializer, WalletSerializer
from cms.models import CMSPage, FAQ
from core.models import SiteConfiguration
from core.platform_models import PriceAlert, TradingSignal, VIPTier, WatchlistItem
from core.portfolio import chart_series, compute_equity, record_snapshot
from core.vip import decorate_tier, refresh_user_vip_context
from investments.models import Earning, Investment, InvestmentPlan
from markets.pairs import FOREX_CATEGORIES, all_pairs
from notifications.models import Notification, notify
from referrals.models import ReferralCommission, ReferralProgram
from referrals.services import get_program_rates
from support.models import SupportTicket, TicketMessage
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.models import Cryptocurrency, UserWalletAddress, Wallet

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            return Response({'email': ['An account with this email already exists.']}, status=400)
        user = User.objects.create_user(
            email=email,
            password=ser.validated_data['password'],
            first_name=ser.validated_data.get('first_name', ''),
            last_name=ser.validated_data.get('last_name', ''),
        )
        ref = (ser.validated_data.get('referral_code') or '').strip()
        if ref:
            referrer = User.objects.filter(referral_code__iexact=ref).exclude(pk=user.pk).first()
            if referrer:
                user.referred_by = referrer
                user.save(update_fields=['referred_by'])
        Wallet.objects.get_or_create(user=user)
        notify(
            user, 'Welcome!',
            f'Welcome to the platform. Complete KYC and make your first deposit to get started.',
            category=Notification.Category.SYSTEM,
        )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        }, status=201)


class ProfileView(APIView):
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        ser = UserProfileSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class ChangePasswordView(APIView):
    def post(self, request):
        ser = ChangePasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not request.user.check_password(ser.validated_data['current_password']):
            return Response({'current_password': ['Incorrect password.']}, status=400)
        request.user.set_password(ser.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({'detail': 'Password updated.', 'token': token.key})


class SupportTicketViewSet(viewsets.ModelViewSet):
    """User support chat: messages, typing, presence, read receipts, poll sync."""
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return SupportTicket.objects.filter(user=self.request.user).prefetch_related('messages__sender')

    def get_serializer_class(self):
        if self.action == 'create':
            return SupportTicketCreateSerializer
        return SupportTicketSerializer

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()
        self._mark_peer_messages_read(ticket, is_staff=False)
        return Response(SupportTicketSerializer(ticket).data)

    def create(self, request, *args, **kwargs):
        from support.realtime import notify_new_message

        ser = SupportTicketCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ticket = SupportTicket.objects.create(
            user=request.user,
            subject=ser.validated_data['subject'],
            category=ser.validated_data.get('category') or 'general',
        )
        msg = TicketMessage.objects.create(
            ticket=ticket, sender=request.user, body=ser.validated_data['body'],
        )
        notify_new_message(ticket, msg)
        return Response(SupportTicketSerializer(ticket).data, status=201)

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        from support.realtime import notify_new_message

        ticket = self.get_object()
        if ticket.status in (SupportTicket.Status.CLOSED, SupportTicket.Status.RESOLVED):
            return Response({'detail': 'This conversation is closed.'}, status=400)
        ser = TicketReplySerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        body = (ser.validated_data.get('body') or '').strip()
        attachment = ser.validated_data.get('attachment')
        if not body and not attachment:
            return Response({'detail': 'Message or attachment required'}, status=400)
        msg = TicketMessage.objects.create(
            ticket=ticket, sender=request.user, body=body or '(attachment)',
            attachment=attachment,
        )
        if ticket.status == SupportTicket.Status.WAITING:
            ticket.status = SupportTicket.Status.OPEN
            ticket.save(update_fields=['status', 'updated_at'])
        else:
            ticket.save(update_fields=['updated_at'])
        notify_new_message(ticket, msg)
        return Response(TicketMessageSerializer(msg).data, status=201)

    @action(detail=True, methods=['get'])
    def poll(self, request, pk=None):
        """Near-realtime sync when WebSockets are unavailable (e.g. PythonAnywhere)."""
        from support.realtime import get_presence, get_typing, set_presence

        ticket = self.get_object()
        set_presence(ticket.id, request.user, is_staff=False)
        self._mark_peer_messages_read(ticket, is_staff=False)

        since = request.query_params.get('since')
        qs = ticket.messages.select_related('sender').all()
        if since:
            try:
                since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
                if timezone.is_naive(since_dt):
                    since_dt = timezone.make_aware(since_dt, timezone.get_current_timezone())
                qs = qs.filter(created_at__gt=since_dt)
            except (ValueError, TypeError):
                pass

        # Receipt updates for own messages (staff may have read them)
        own = ticket.messages.filter(is_staff_reply=False).select_related('sender')
        return Response({
            'ticket_id': str(ticket.id),
            'status': ticket.status,
            'updated_at': ticket.updated_at,
            'messages': TicketMessageSerializer(qs, many=True).data,
            'receipts': TicketMessageSerializer(own, many=True).data,
            'typing': get_typing(ticket.id, exclude_user_id=request.user.pk),
            'presence': get_presence(ticket.id),
            'server_time': timezone.now().isoformat(),
        })

    @action(detail=True, methods=['post'])
    def typing(self, request, pk=None):
        from support.realtime import as_bool, set_typing

        ticket = self.get_object()
        is_typing = as_bool(request.data.get('is_typing', True), default=True)
        set_typing(ticket.id, request.user, is_typing=is_typing, is_staff=False)
        return Response({'ok': True, 'is_typing': is_typing})

    @action(detail=True, methods=['post'])
    def heartbeat(self, request, pk=None):
        from support.realtime import get_presence, set_presence

        ticket = self.get_object()
        set_presence(ticket.id, request.user, is_staff=False)
        self._mark_peer_messages_read(ticket, is_staff=False)
        return Response({'ok': True, 'presence': get_presence(ticket.id)})

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Mark customer offline immediately when they leave the chat."""
        from support.realtime import clear_presence, get_presence

        ticket = self.get_object()
        clear_presence(ticket.id, request.user, is_staff=False)
        return Response({'ok': True, 'presence': get_presence(ticket.id)})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        ticket = self.get_object()
        n = self._mark_peer_messages_read(ticket, is_staff=False)
        return Response({'ok': True, 'updated': n})

    def _mark_peer_messages_read(self, ticket, *, is_staff: bool) -> int:
        from support.realtime import notify_receipts

        now = timezone.now()
        qs = TicketMessage.objects.filter(ticket=ticket, read_at__isnull=True)
        if is_staff:
            qs = qs.filter(is_staff_reply=False)
        else:
            qs = qs.filter(is_staff_reply=True)
        ids = list(qs.values_list('id', flat=True))
        if not ids:
            return 0
        updated = qs.update(delivered_at=now, read_at=now, updated_at=now)
        notify_receipts(ticket.id, ids, 'read', now.isoformat())
        return updated


class ReferralsView(APIView):
    def get(self, request):
        user = request.user
        program = ReferralProgram.get_active()
        live = get_program_rates(program)
        commissions = ReferralCommission.objects.filter(referrer=user).select_related('referred_user')
        referred = user.referrals.all().order_by('-date_joined')[:50]
        pending = commissions.filter(status=ReferralCommission.Status.PENDING).aggregate(t=Sum('amount'))['t'] or 0
        paid = commissions.filter(status=ReferralCommission.Status.PAID).aggregate(t=Sum('amount'))['t'] or 0
        link = request.build_absolute_uri(f'/accounts/register/?ref={user.referral_code}')
        spa_link = request.build_absolute_uri(f'/app/register?ref={user.referral_code}')
        return Response({
            'code': user.referral_code,
            'link': link,
            'spa_link': spa_link,
            'stats': {
                'total_referrals': user.referrals.count(),
                'total_earned': str(user.referral_earnings),
                'pending': str(pending),
                'paid': str(paid),
                'rate': str(live['rates'][1]),
                'rate_l2': str(live['rates'][2]),
                'rate_l3': str(live['rates'][3]),
                'pays_on': live['source'],
            },
            'referred': [
                {
                    'id': u.id,
                    'email': u.email,
                    'date_joined': u.date_joined,
                    'is_kyc_verified': u.is_kyc_verified,
                }
                for u in referred
            ],
            'commissions': ReferralCommissionSerializer(commissions[:30], many=True).data,
        })


class LeaderboardView(APIView):
    def get(self, request):
        season = (request.query_params.get('season') or 'all').lower()
        leaders = User.objects.filter(referral_earnings__gt=0).annotate(ref_count=Count('referrals'))
        if season in ('week', 'month'):
            from referrals.models import ReferralCommission
            days = 7 if season == 'week' else 30
            since = timezone.now() - __import__('datetime').timedelta(days=days)
            # rank by commission earned in season
            from django.db.models import Sum as DjSum
            top = (
                ReferralCommission.objects.filter(created_at__gte=since)
                .values('referrer')
                .annotate(season_total=DjSum('amount'), ref_count=Count('id'))
                .order_by('-season_total')[:50]
            )
            out = []
            for i, row in enumerate(top):
                u = User.objects.filter(pk=row['referrer']).first()
                if not u:
                    continue
                out.append({
                    'rank': i + 1,
                    'email': u.email[:3] + '***@' + (u.email.split('@')[-1] if '@' in u.email else '***'),
                    'referral_earnings': str(row['season_total'] or 0),
                    'ref_count': row['ref_count'],
                    'is_you': u.pk == request.user.pk,
                    'season': season,
                })
            return Response(out)
        leaders = leaders.order_by('-referral_earnings')[:50]
        return Response([
            {
                'rank': i + 1,
                'email': u.email[:3] + '***@' + (u.email.split('@')[-1] if '@' in u.email else '***'),
                'referral_earnings': str(u.referral_earnings),
                'ref_count': u.ref_count,
                'is_you': u.pk == request.user.pk,
                'season': 'all',
            }
            for i, u in enumerate(leaders)
        ])


class VIPView(APIView):
    def get(self, request):
        ctx = refresh_user_vip_context(request.user)
        tiers = [decorate_tier(t) for t in VIPTier.objects.filter(is_active=True)]

        def tier_payload(t):
            if not t:
                return None
            return {
                'id': t.id,
                'name': t.name,
                'slug': t.slug,
                'min_total_invested': str(t.min_total_invested),
                'badge_color': t.badge_color,
                'deposit_fee_percent': str(t.deposit_fee_percent),
                'withdrawal_fee_percent': str(t.withdrawal_fee_percent),
                'referral_bonus_boost': str(t.referral_bonus_boost),
                'sticker_emoji': getattr(t, 'sticker_emoji', '⭐'),
                'sticker_tagline': getattr(t, 'sticker_tagline', ''),
            }

        user = request.user
        return Response({
            'tier': tier_payload(ctx.get('tier')),
            'next_tier': tier_payload(ctx.get('next_tier')),
            'total_invested': str(ctx.get('total_invested') or 0),
            'progress_pct': ctx.get('vip_progress_pct', 0),
            'remaining': str(ctx.get('vip_remaining') or 0),
            'sticker_emoji': ctx.get('sticker_emoji', '⭐'),
            'tiers': [tier_payload(t) for t in tiers],
            'member': {
                'name': user.display_name or user.email,
                'email': user.email,
                'avatar_url': user.avatar_display_url or '',
                'initials': (
                    ''.join(
                        p[0] for p in (user.display_name or user.email or 'U').split()[:2] if p
                    ).upper()
                    or 'U'
                )[:2],
            },
        })


class PortfolioView(APIView):
    def get(self, request):
        days = int(request.GET.get('days') or 30)
        days = max(7, min(days, 365))
        record_snapshot(request.user)
        labels, equity, profit = chart_series(request.user, days=days)
        equity_now = compute_equity(request.user)
        active = Investment.objects.filter(user=request.user, status=Investment.Status.ACTIVE)
        return Response({
            'days': days,
            'equity_now': str(equity_now),
            'labels': labels,
            'equity': equity,
            'profit': profit,
            'active_investments': active.count(),
            'total_earned': str(
                Earning.objects.filter(user=request.user).aggregate(t=Sum('amount'))['t'] or 0
            ),
            'disclaimer': SiteConfiguration.get_solo().risk_disclaimer,
        })


class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    pagination_class = None

    def get_queryset(self):
        return WatchlistItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PriceAlertViewSet(viewsets.ModelViewSet):
    serializer_class = PriceAlertSerializer
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    pagination_class = None

    def get_queryset(self):
        return PriceAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SignalsView(generics.ListAPIView):
    serializer_class = TradingSignalSerializer
    pagination_class = None

    def get_queryset(self):
        return TradingSignal.objects.filter(is_published=True)[:50]

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = TradingSignalSerializer(qs, many=True).data
        return Response({
            'results': data,
            'disclaimer': SiteConfiguration.get_solo().risk_disclaimer,
        })


class ActivityView(generics.ListAPIView):
    serializer_class = ActivityEventSerializer

    def get_queryset(self):
        return ActivityEvent.objects.filter(user=self.request.user)[:100]


class MarketPairsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'categories': FOREX_CATEGORIES,
            'pairs': all_pairs(),
        })


class FAQListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = FAQSerializer
    pagination_class = None

    def get_queryset(self):
        return FAQ.objects.filter(is_published=True)


class CMSPageDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CMSPageSerializer
    lookup_field = 'slug'
    queryset = CMSPage.objects.filter(is_published=True)


class CalculatorView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = InvestmentPlan.objects.filter(status=InvestmentPlan.Status.ACTIVE)
        return Response({
            'plans': [
                {
                    'id': str(p.id),
                    'name': p.name,
                    'slug': p.slug,
                    'min_deposit': str(p.min_deposit),
                    'max_deposit': str(p.max_deposit),
                    'duration_days': p.duration_days,
                    'profit_rate_percent': str(p.profit_rate_percent),
                    'return_percent_min': str(p.return_percent_min),
                    'return_percent_max': str(p.return_percent_max),
                    'payout_frequency': p.payout_frequency,
                    'expected_return': p.expected_return_display(),
                }
                for p in plans
            ],
        })

    def post(self, request):
        try:
            amount = Decimal(str(request.data.get('amount') or 0))
            rate = Decimal(str(request.data.get('profit_rate_percent') or 0))
            days = int(request.data.get('duration_days') or 30)
        except (InvalidOperation, TypeError, ValueError):
            return Response({'detail': 'Invalid input'}, status=400)
        if amount <= 0 or days <= 0:
            return Response({'detail': 'Amount and duration must be positive'}, status=400)
        # Simple linear model matching plan rate × periods approximation
        total_return = (amount * rate / Decimal('100')) * (Decimal(days) / Decimal('30'))
        return Response({
            'amount': str(amount),
            'rate_percent': str(rate),
            'duration_days': days,
            'estimated_profit': str(total_return.quantize(Decimal('0.00000001'))),
            'estimated_total': str((amount + total_return).quantize(Decimal('0.00000001'))),
        })


class StatementsView(APIView):
    def get(self, request):
        from django.http import HttpResponse
        import csv
        from io import StringIO

        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        fmt = (request.query_params.get('format') or 'json').lower()
        txs = Transaction.objects.filter(user=request.user)
        deposits = Deposit.objects.filter(user=request.user).select_related('cryptocurrency')
        withdrawals = Withdrawal.objects.filter(user=request.user).select_related('cryptocurrency')
        if date_from:
            txs = txs.filter(created_at__date__gte=date_from)
            deposits = deposits.filter(created_at__date__gte=date_from)
            withdrawals = withdrawals.filter(created_at__date__gte=date_from)
        if date_to:
            txs = txs.filter(created_at__date__lte=date_to)
            deposits = deposits.filter(created_at__date__lte=date_to)
            withdrawals = withdrawals.filter(created_at__date__lte=date_to)
        txs = txs[:500]
        deposits = deposits[:200]
        withdrawals = withdrawals[:200]
        if fmt == 'csv':
            buf = StringIO()
            w = csv.writer(buf)
            w.writerow(['kind', 'id', 'type', 'amount', 'status', 'created_at', 'description'])
            for t in txs:
                w.writerow(['transaction', t.id, t.tx_type, t.amount, t.status, t.created_at.isoformat(), t.description])
            for d in deposits:
                w.writerow(['deposit', d.id, d.cryptocurrency.symbol, d.amount, d.status, d.created_at.isoformat(), ''])
            for x in withdrawals:
                w.writerow(['withdrawal', x.id, x.cryptocurrency.symbol, x.amount, x.status, x.created_at.isoformat(), ''])
            resp = HttpResponse(buf.getvalue(), content_type='text/csv')
            resp['Content-Disposition'] = 'attachment; filename="statement.csv"'
            return resp
        if fmt == 'pdf':
            from io import BytesIO
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas

            bio = BytesIO()
            c = canvas.Canvas(bio, pagesize=A4)
            width, height = A4
            y = height - 50
            c.setFont('Helvetica-Bold', 14)
            c.drawString(40, y, 'Account statement')
            y -= 20
            c.setFont('Helvetica', 9)
            c.drawString(40, y, f'Generated {timezone.now().isoformat()} · {request.user.email}')
            y -= 28
            c.setFont('Helvetica-Bold', 10)
            c.drawString(40, y, 'Recent transactions')
            y -= 16
            c.setFont('Helvetica', 8)
            for t in list(txs)[:80]:
                if y < 50:
                    c.showPage()
                    y = height - 40
                    c.setFont('Helvetica', 8)
                line = f"{t.created_at.date()}  {t.tx_type:12}  {t.amount}  {t.status}  {(t.description or '')[:50]}"
                c.drawString(40, y, line[:110])
                y -= 12
            y -= 16
            if y < 80:
                c.showPage()
                y = height - 40
            c.setFont('Helvetica-Bold', 10)
            c.drawString(40, y, 'Deposits')
            y -= 14
            c.setFont('Helvetica', 8)
            for d in list(deposits)[:40]:
                if y < 50:
                    c.showPage()
                    y = height - 40
                    c.setFont('Helvetica', 8)
                c.drawString(40, y, f"{d.created_at.date()}  {d.cryptocurrency.symbol}  {d.amount}  {d.status}"[:110])
                y -= 12
            y -= 16
            if y < 80:
                c.showPage()
                y = height - 40
            c.setFont('Helvetica-Bold', 10)
            c.drawString(40, y, 'Withdrawals')
            y -= 14
            c.setFont('Helvetica', 8)
            for x in list(withdrawals)[:40]:
                if y < 50:
                    c.showPage()
                    y = height - 40
                    c.setFont('Helvetica', 8)
                c.drawString(40, y, f"{x.created_at.date()}  {x.cryptocurrency.symbol}  {x.amount}  {x.status}"[:110])
                y -= 12
            c.save()
            pdf = bio.getvalue()
            resp = HttpResponse(pdf, content_type='application/pdf')
            resp['Content-Disposition'] = 'attachment; filename="statement.pdf"'
            return resp
        return Response({
            'generated_at': timezone.now().isoformat(),
            'transactions': [
                {
                    'id': str(t.id),
                    'tx_type': t.tx_type,
                    'amount': str(t.amount),
                    'status': t.status,
                    'description': t.description,
                    'created_at': t.created_at,
                }
                for t in txs
            ],
            'deposits': [
                {
                    'id': str(d.id),
                    'amount': str(d.amount),
                    'symbol': d.cryptocurrency.symbol,
                    'status': d.status,
                    'created_at': d.created_at,
                }
                for d in deposits
            ],
            'withdrawals': [
                {
                    'id': str(w.id),
                    'amount': str(w.amount),
                    'symbol': w.cryptocurrency.symbol,
                    'status': w.status,
                    'created_at': w.created_at,
                }
                for w in withdrawals
            ],
        })


class RiskQuizView(APIView):
    def get(self, request):
        return Response({
            'score': request.user.risk_score,
            'questions': [
                {
                    'id': 'horizon',
                    'text': 'How long do you plan to keep funds invested?',
                    'options': [
                        {'value': 1, 'label': 'Less than 1 month'},
                        {'value': 2, 'label': '1–3 months'},
                        {'value': 3, 'label': '3–12 months'},
                        {'value': 4, 'label': 'Over 1 year'},
                    ],
                },
                {
                    'id': 'loss',
                    'text': 'How would you react to a temporary 20% drawdown?',
                    'options': [
                        {'value': 1, 'label': 'Withdraw immediately'},
                        {'value': 2, 'label': 'Reduce exposure'},
                        {'value': 3, 'label': 'Hold and wait'},
                        {'value': 4, 'label': 'Buy more if possible'},
                    ],
                },
                {
                    'id': 'experience',
                    'text': 'Your experience with crypto investments?',
                    'options': [
                        {'value': 1, 'label': 'Beginner'},
                        {'value': 2, 'label': 'Some experience'},
                        {'value': 3, 'label': 'Experienced'},
                        {'value': 4, 'label': 'Professional'},
                    ],
                },
                {
                    'id': 'goal',
                    'text': 'Primary goal?',
                    'options': [
                        {'value': 1, 'label': 'Capital preservation'},
                        {'value': 2, 'label': 'Steady income'},
                        {'value': 3, 'label': 'Balanced growth'},
                        {'value': 4, 'label': 'Maximum returns'},
                    ],
                },
            ],
        })

    def post(self, request):
        answers = request.data.get('answers') or {}
        total = 0
        count = 0
        for v in answers.values():
            try:
                total += int(v)
                count += 1
            except (TypeError, ValueError):
                pass
        score = int(round((total / max(count, 1)) * 25))  # 0–100 scale-ish
        score = max(0, min(100, score))
        request.user.risk_score = score
        request.user.save(update_fields=['risk_score'])
        if score < 35:
            profile = 'Conservative'
            tip = 'Prefer lower-risk plans and shorter commitments.'
        elif score < 65:
            profile = 'Balanced'
            tip = 'A mix of steady and growth plans may suit you.'
        else:
            profile = 'Aggressive'
            tip = 'You may tolerate higher-risk, higher-return plans — invest only what you can afford to lose.'
        return Response({
            'score': score,
            'profile': profile,
            'tip': tip,
        })


class DashboardStatsView(APIView):
    def get(self, request):
        user = request.user
        wallet, _ = Wallet.objects.get_or_create(user=user)
        return Response({
            'wallet': WalletSerializer(wallet).data,
            'unread_notifications': user.notifications.filter(is_read=False).count(),
            'open_tickets': SupportTicket.objects.filter(
                user=user,
                status__in=[SupportTicket.Status.OPEN, SupportTicket.Status.IN_PROGRESS, SupportTicket.Status.WAITING],
            ).count(),
            'active_investments': Investment.objects.filter(user=user, status=Investment.Status.ACTIVE).count(),
            'pending_deposits': Deposit.objects.filter(user=user, status=Deposit.Status.PENDING).count(),
            'pending_withdrawals': Withdrawal.objects.filter(user=user, status=Withdrawal.Status.PENDING).count(),
        })


class SearchView(APIView):
    def get(self, request):
        q = (request.GET.get('q') or '').strip()
        results = []
        if len(q) < 2:
            return Response({'results': results})
        user = request.user
        for d in Deposit.objects.filter(user=user).filter(
            transaction_hash__icontains=q,
        )[:5]:
            results.append({
                'type': 'deposit',
                'title': f'Deposit {d.amount} {d.cryptocurrency.symbol}',
                'subtitle': d.get_status_display(),
                'path': '/deposits',
            })
        for inv in Investment.objects.filter(user=user).select_related('plan').filter(
            plan__name__icontains=q,
        )[:5]:
            results.append({
                'type': 'investment',
                'title': inv.plan.name,
                'subtitle': f'{inv.amount} · {inv.get_status_display()}',
                'path': f'/investments/{inv.pk}',
            })
        for plan in InvestmentPlan.objects.filter(status=InvestmentPlan.Status.ACTIVE).filter(
            name__icontains=q,
        )[:5]:
            results.append({
                'type': 'plan',
                'title': plan.name,
                'subtitle': (plan.short_description or '')[:80],
                'path': f'/plans/{plan.slug}',
            })
        for t in SupportTicket.objects.filter(user=user).filter(subject__icontains=q)[:5]:
            results.append({
                'type': 'ticket',
                'title': t.subject,
                'subtitle': t.get_status_display(),
                'path': f'/support/{t.pk}',
            })
        static = [
            ('Dashboard', '/dashboard'),
            ('Wallet', '/wallet'),
            ('Deposit', '/deposits'),
            ('Withdraw', '/withdrawals'),
            ('Markets', '/markets'),
            ('VIP', '/vip'),
            ('Referrals', '/referrals'),
            ('Support', '/support'),
            ('KYC', '/kyc'),
            ('Calculator', '/calculator'),
        ]
        ql = q.lower()
        for title, path in static:
            if ql in title.lower():
                results.append({'type': 'page', 'title': title, 'subtitle': 'Navigate', 'path': path})
        return Response({'results': results[:25]})


class FeePreviewView(APIView):
    def get(self, request):
        try:
            amount = Decimal(str(request.GET.get('amount') or 0))
            crypto_id = request.GET.get('cryptocurrency')
        except (InvalidOperation, TypeError):
            return Response({'detail': 'Invalid amount'}, status=400)
        crypto = None
        if crypto_id:
            crypto = Cryptocurrency.objects.filter(pk=crypto_id, is_active=True).first()
        from core.vip import apply_withdrawal_fee
        fee_total, pct = apply_withdrawal_fee(
            request.user, amount, crypto.withdrawal_fee if crypto else 0,
        )
        return Response({
            'amount': str(amount),
            'fee': str(fee_total),
            'fee_percent': str(pct),
            'net': str(max(Decimal('0'), amount - fee_total)),
            'crypto_fee': str(crypto.withdrawal_fee) if crypto else '0',
        })
