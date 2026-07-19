"""Serializers for platform features used by the Vue SPA."""
from rest_framework import serializers

from accounts.models import ActivityEvent, KYCDocument, User
from cms.models import CMSPage, FAQ
from core.platform_models import PriceAlert, TradingSignal, VIPTier, WatchlistItem
from referrals.models import ReferralCommission
from support.models import SupportTicket, TicketMessage
from wallets.models import UserWalletAddress


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'phone', 'email_verified',
            'is_kyc_verified', 'two_factor_enabled', 'referral_code', 'referral_earnings',
            'country', 'country_code', 'date_joined', 'preferred_theme', 'preferred_ui_theme',
            'preferred_language', 'preferred_currency', 'preferred_timezone',
            'email_alerts', 'sms_alerts', 'tour_completed',
        )
        read_only_fields = (
            'id', 'email', 'email_verified', 'is_kyc_verified', 'two_factor_enabled',
            'referral_code', 'referral_earnings', 'date_joined',
        )


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, default='')
    last_name = serializers.CharField(required=False, allow_blank=True, default='')
    referral_code = serializers.CharField(required=False, allow_blank=True, default='')


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    receipt_status = serializers.CharField(read_only=True)

    class Meta:
        model = TicketMessage
        fields = (
            'id', 'body', 'is_staff_reply', 'created_at', 'sender', 'sender_name',
            'delivered_at', 'read_at', 'receipt_status',
        )
        read_only_fields = fields

    def get_sender_name(self, obj):
        u = obj.sender
        name = f'{u.first_name} {u.last_name}'.strip()
        return name or u.email


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    message_count = serializers.IntegerField(source='messages.count', read_only=True)

    class Meta:
        model = SupportTicket
        fields = (
            'id', 'subject', 'category', 'status', 'priority', 'created_at', 'updated_at',
            'messages', 'message_count',
        )
        read_only_fields = ('status', 'priority', 'created_at', 'updated_at', 'messages', 'message_count')


class SupportTicketCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=200)
    body = serializers.CharField()
    category = serializers.CharField(required=False, default='general')


class TicketReplySerializer(serializers.Serializer):
    body = serializers.CharField()


class ReferralCommissionSerializer(serializers.ModelSerializer):
    referred_email = serializers.EmailField(source='referred_user.email', read_only=True)

    class Meta:
        model = ReferralCommission
        fields = (
            'id', 'amount', 'rate_percent', 'base_amount', 'source', 'level',
            'status', 'created_at', 'referred_email',
        )


class WatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchlistItem
        fields = ('id', 'symbol', 'label', 'created_at')
        read_only_fields = ('id', 'created_at')


class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = (
            'id', 'symbol', 'label', 'target_price', 'direction',
            'is_active', 'triggered_at', 'last_price', 'created_at',
        )
        read_only_fields = ('id', 'is_active', 'triggered_at', 'last_price', 'created_at')


class TradingSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingSignal
        fields = (
            'id', 'title', 'symbol', 'side', 'entry_note', 'target',
            'stop_loss', 'created_at',
        )


class ActivityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityEvent
        fields = ('id', 'event_type', 'title', 'description', 'metadata', 'created_at')


class VIPTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = VIPTier
        fields = (
            'id', 'name', 'slug', 'min_total_invested', 'badge_color',
            'deposit_fee_percent', 'withdrawal_fee_percent', 'referral_bonus_boost',
            'sort_order', 'is_active',
        )


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('id', 'question', 'answer', 'category', 'sort_order')


class CMSPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CMSPage
        fields = (
            'id', 'title', 'slug', 'page_type', 'content',
            'meta_description', 'sort_order',
        )


class WalletAddressSerializer(serializers.ModelSerializer):
    crypto_symbol = serializers.CharField(source='cryptocurrency.symbol', read_only=True)

    class Meta:
        model = UserWalletAddress
        fields = (
            'id', 'cryptocurrency', 'crypto_symbol', 'address', 'label',
            'is_default', 'is_verified', 'created_at',
        )
        read_only_fields = ('is_verified', 'created_at')


class KYCDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = (
            'id', 'document_type', 'document_number', 'front_image', 'back_image',
            'selfie_image', 'status', 'rejection_reason', 'created_at',
        )
        read_only_fields = ('status', 'rejection_reason', 'created_at')
