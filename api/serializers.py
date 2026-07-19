from rest_framework import serializers

from accounts.models import KYCDocument, User
from investments.models import Earning, Investment, InvestmentPlan
from notifications.models import Notification
from transactions.models import Deposit, Transaction, Withdrawal
from wallets.models import Cryptocurrency, UserWalletAddress, Wallet


class UserSerializer(serializers.ModelSerializer):
    is_staff_panel = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone', 'email_verified',
            'is_kyc_verified', 'two_factor_enabled', 'referral_code', 'referral_earnings',
            'country', 'country_code', 'date_joined', 'preferred_theme', 'preferred_ui_theme',
            'preferred_language', 'preferred_currency', 'preferred_timezone',
            'email_alerts', 'sms_alerts', 'risk_score', 'tour_completed',
            'is_staff', 'is_superuser', 'role', 'is_staff_panel',
            'avatar_url', 'display_name',
        )
        read_only_fields = fields

    def get_is_staff_panel(self, obj):
        if getattr(obj, 'is_superuser', False) or getattr(obj, 'is_staff', False):
            return True
        return getattr(obj, 'role', '') in ('support', 'manager', 'admin')

    def get_avatar_url(self, obj):
        return obj.avatar_display_url or ''

    def get_display_name(self, obj):
        return obj.display_name or obj.email


class WalletSerializer(serializers.ModelSerializer):
    available_balance = serializers.DecimalField(max_digits=18, decimal_places=8, read_only=True)

    class Meta:
        model = Wallet
        fields = (
            'balance', 'locked_balance', 'available_balance', 'total_deposited',
            'total_withdrawn', 'total_profit', 'total_invested',
        )


class CryptocurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Cryptocurrency
        fields = (
            'id', 'symbol', 'name', 'network', 'decimals', 'min_deposit',
            'min_withdrawal', 'max_withdrawal', 'withdrawal_fee', 'deposit_address', 'is_active',
        )


class InvestmentPlanSerializer(serializers.ModelSerializer):
    expected_return = serializers.CharField(source='expected_return_display', read_only=True)

    class Meta:
        model = InvestmentPlan
        fields = (
            'id', 'name', 'slug', 'description', 'short_description', 'min_deposit', 'max_deposit',
            'duration_days', 'profit_method', 'profit_rate_percent', 'return_percent_min',
            'return_percent_max', 'expected_return', 'payout_frequency', 'risk_level', 'status',
            'is_featured', 'allow_auto_reinvest', 'allow_manual_reinvest', 'return_principal',
        )


class InvestmentSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    progress_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = Investment
        fields = (
            'id', 'plan', 'plan_name', 'amount', 'status', 'profit_rate_percent',
            'payout_frequency', 'duration_days', 'total_earned', 'auto_reinvest',
            'payouts_count', 'expected_payouts', 'started_at', 'matures_at',
            'completed_at', 'progress_percent', 'next_payout_at',
        )
        read_only_fields = fields


class InvestCreateSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=8)
    auto_reinvest = serializers.BooleanField(default=False)
    duration_days = serializers.IntegerField(required=False, allow_null=True)


class DepositSerializer(serializers.ModelSerializer):
    crypto_symbol = serializers.CharField(source='cryptocurrency.symbol', read_only=True)

    class Meta:
        model = Deposit
        fields = (
            'id', 'cryptocurrency', 'crypto_symbol', 'amount', 'transaction_hash',
            'screenshot', 'network', 'status', 'created_at', 'reviewed_at', 'rejection_reason',
        )
        read_only_fields = ('status', 'network', 'reviewed_at', 'rejection_reason')


class WithdrawalSerializer(serializers.ModelSerializer):
    crypto_symbol = serializers.CharField(source='cryptocurrency.symbol', read_only=True)

    class Meta:
        model = Withdrawal
        fields = (
            'id', 'cryptocurrency', 'crypto_symbol', 'amount', 'fee', 'net_amount',
            'wallet_address', 'network', 'status', 'created_at', 'rejection_reason',
        )
        read_only_fields = ('fee', 'net_amount', 'network', 'status', 'rejection_reason')


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id', 'tx_type', 'amount', 'status', 'description', 'created_at',
            'reference_type', 'reference_id', 'fee', 'currency',
        )


class EarningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Earning
        fields = ('id', 'investment', 'amount', 'period_number', 'is_reinvested', 'created_at')


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'level', 'category', 'is_read', 'link', 'created_at')


class UserWalletAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWalletAddress
        fields = ('id', 'cryptocurrency', 'address', 'label', 'is_default', 'is_verified', 'created_at')


class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = (
            'id', 'document_type', 'document_number', 'front_image', 'back_image',
            'selfie_image', 'status', 'rejection_reason', 'created_at',
        )
        read_only_fields = ('status', 'rejection_reason')
