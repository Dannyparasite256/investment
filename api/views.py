from decimal import Decimal

from rest_framework import generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.models import KYCDocument
from api.serializers import (
    CryptocurrencySerializer,
    DepositSerializer,
    EarningSerializer,
    InvestCreateSerializer,
    InvestmentPlanSerializer,
    InvestmentSerializer,
    KYCSerializer,
    NotificationSerializer,
    TransactionSerializer,
    UserSerializer,
    UserWalletAddressSerializer,
    WalletSerializer,
    WithdrawalSerializer,
)
from investments.models import Earning, Investment, InvestmentPlan
from investments.services import create_investment
from notifications.models import Notification
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.models import Cryptocurrency, UserWalletAddress, Wallet


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'user_id', None) == request.user.id


class CustomAuthToken(ObtainAuthToken):
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        })


class MeView(APIView):
    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            'user': UserSerializer(request.user).data,
            'wallet': WalletSerializer(wallet).data,
        })


class WalletView(APIView):
    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response(WalletSerializer(wallet).data)


class CryptocurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cryptocurrency.objects.filter(is_active=True)
    serializer_class = CryptocurrencySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class InvestmentPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InvestmentPlan.objects.filter(status=InvestmentPlan.Status.ACTIVE)
    serializer_class = InvestmentPlanSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


class InvestmentViewSet(viewsets.ModelViewSet):
    serializer_class = InvestmentSerializer
    http_method_names = ['get', 'patch', 'post', 'head', 'options']

    def get_queryset(self):
        return Investment.objects.filter(user=self.request.user).select_related('plan')

    def partial_update(self, request, *args, **kwargs):
        inv = self.get_object()
        if 'auto_reinvest' in request.data:
            want = bool(request.data.get('auto_reinvest'))
            if want and not inv.plan.allow_auto_reinvest:
                return Response({'detail': 'This plan does not allow auto-reinvest.'}, status=400)
            inv.auto_reinvest = want
            inv.save(update_fields=['auto_reinvest', 'updated_at'])
        return Response(InvestmentSerializer(inv).data)

    @action(detail=False, methods=['post'], serializer_class=InvestCreateSerializer)
    def create_investment(self, request):
        ser = InvestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        plan = InvestmentPlan.objects.filter(
            id=ser.validated_data['plan_id'],
            status=InvestmentPlan.Status.ACTIVE,
        ).first()
        if not plan:
            return Response({'detail': 'Plan not found or inactive.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            inv = create_investment(
                user=request.user,
                plan=plan,
                amount=ser.validated_data['amount'],
                auto_reinvest=ser.validated_data.get('auto_reinvest', False),
                duration_days=ser.validated_data.get('duration_days'),
                request=request,
            )
            try:
                from accounts.models import ActivityEvent
                ActivityEvent.objects.create(
                    user=request.user, event_type='invest', title='Investment created',
                    description=f'{plan.name} · {inv.amount}',
                    metadata={'investment_id': str(inv.id)},
                )
            except Exception:
                pass
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InvestmentSerializer(inv).data, status=status.HTTP_201_CREATED)


class DepositViewSet(viewsets.ModelViewSet):
    serializer_class = DepositSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return Deposit.objects.filter(user=self.request.user).select_related('cryptocurrency')

    def perform_create(self, serializer):
        crypto = serializer.validated_data['cryptocurrency']
        promo = (serializer.validated_data.get('promo_code') or '').strip().upper()
        deposit = serializer.save(
            user=self.request.user,
            network=crypto.network,
            deposit_address=crypto.deposit_address,
            status=Deposit.Status.PENDING,
            promo_code=promo,
        )
        Transaction.objects.create(
            user=self.request.user,
            tx_type=Transaction.TxType.DEPOSIT,
            amount=deposit.amount,
            status=Transaction.Status.PENDING,
            description=f'Deposit {deposit.amount} {crypto.symbol}',
            reference_type='deposit',
            reference_id=str(deposit.id),
        )
        try:
            from accounts.models import ActivityEvent
            ActivityEvent.objects.create(
                user=self.request.user, event_type='deposit', title='Deposit submitted',
                description=f'{deposit.amount} {crypto.symbol}',
                metadata={'deposit_id': str(deposit.id)},
            )
        except Exception:
            pass


class WithdrawalViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return Withdrawal.objects.filter(user=self.request.user).select_related('cryptocurrency')

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        crypto = ser.validated_data['cryptocurrency']
        amount = ser.validated_data['amount']
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        if amount < crypto.min_withdrawal:
            return Response({'detail': f'Minimum withdrawal is {crypto.min_withdrawal}'}, status=400)
        if amount > crypto.max_withdrawal:
            return Response({'detail': f'Maximum withdrawal is {crypto.max_withdrawal}'}, status=400)
        if amount > wallet.available_balance:
            return Response({'detail': 'Insufficient available balance'}, status=400)
        from django.db import transaction as db_tx

        # Large withdrawal: require 2FA when enabled and amount >= threshold
        from core.models import SiteConfiguration
        cfg = SiteConfiguration.get_solo()
        threshold = cfg.large_withdraw_threshold or Decimal('1000')
        if amount >= threshold and not request.user.two_factor_enabled:
            return Response({
                'detail': f'Withdrawals of {threshold}+ require 2FA. Enable it under Security.',
                'code': 'two_fa_required',
            }, status=403)
        # VIP priority for staff queue
        try:
            from core.vip import get_user_tier
            tier = get_user_tier(request.user)
            priority = int(getattr(tier, 'sort_order', 0) or 0) * 10 if tier else 0
        except Exception:
            priority = 0

        with db_tx.atomic():
            w = Wallet.objects.select_for_update().get(user=request.user)
            w.lock_funds(amount)
            withdrawal = Withdrawal.objects.create(
                user=request.user,
                cryptocurrency=crypto,
                amount=amount,
                fee=crypto.withdrawal_fee,
                net_amount=amount - crypto.withdrawal_fee,
                wallet_address=ser.validated_data['wallet_address'],
                network=crypto.network,
                funds_locked=True,
                priority=priority,
            )
            Transaction.objects.create(
                user=request.user,
                tx_type=Transaction.TxType.WITHDRAWAL,
                amount=amount,
                status=Transaction.Status.PENDING,
                description=f'Withdrawal to {withdrawal.wallet_address[:16]}…',
                reference_type='withdrawal',
                reference_id=str(withdrawal.id),
            )
        try:
            from accounts.models import ActivityEvent
            ActivityEvent.objects.create(
                user=request.user, event_type='withdraw', title='Withdrawal requested',
                description=str(amount), metadata={'withdrawal_id': str(withdrawal.id)},
            )
        except Exception:
            pass
        return Response(WithdrawalSerializer(withdrawal).data, status=201)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    filterset_fields = ['tx_type', 'status']

    def get_queryset(self):
        qs = Transaction.objects.filter(user=self.request.user)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(description__icontains=q)
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs


class EarningViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EarningSerializer

    def get_queryset(self):
        return Earning.objects.filter(user=self.request.user)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.mark_read()
        return Response(NotificationSerializer(n).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'updated': updated})


class WalletAddressViewSet(viewsets.ModelViewSet):
    serializer_class = UserWalletAddressSerializer

    def get_queryset(self):
        return UserWalletAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class KYCViewSet(viewsets.ModelViewSet):
    serializer_class = KYCSerializer
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        return KYCDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
