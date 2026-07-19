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
    attachment_url = serializers.SerializerMethodField()
    reply_to_id = serializers.SerializerMethodField()
    reply_to = serializers.SerializerMethodField()
    body = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessage
        fields = (
            'id', 'body', 'is_staff_reply', 'created_at', 'sender', 'sender_name',
            'delivered_at', 'read_at', 'receipt_status', 'attachment', 'attachment_url',
            'reply_to_id', 'reply_to',
            'is_starred', 'is_pinned', 'edited_at', 'is_deleted',
        )
        read_only_fields = fields

    def get_body(self, obj):
        if obj.is_deleted:
            return '🚫 This message was deleted'
        return obj.body

    def get_attachment_url(self, obj):
        if obj.is_deleted:
            return ''
        if obj.attachment:
            try:
                return obj.attachment.url
            except Exception:
                return ''
        return ''

    def get_sender_name(self, obj):
        u = obj.sender
        name = f'{u.first_name} {u.last_name}'.strip()
        return name or u.email

    def get_reply_to_id(self, obj):
        return str(obj.reply_to_id) if obj.reply_to_id else None

    def get_reply_to(self, obj):
        parent = obj.reply_to
        if not parent:
            return None
        u = parent.sender
        name = f'{u.first_name} {u.last_name}'.strip() or u.email
        body = parent.body or ''
        if getattr(parent, 'is_deleted', False):
            body = '🚫 This message was deleted'
        elif body == '(attachment)':
            body = '📎 Attachment'
        return {
            'id': str(parent.id),
            'body': body[:200],
            'is_staff_reply': parent.is_staff_reply,
            'sender_name': name,
        }


class SupportTicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    muted = serializers.SerializerMethodField()
    pinned = serializers.SerializerMethodField()
    sla_due_at = serializers.DateTimeField(read_only=True)
    first_response_at = serializers.DateTimeField(read_only=True)
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = (
            'id', 'subject', 'category', 'status', 'priority', 'created_at', 'updated_at',
            'messages', 'message_count', 'unread_count', 'last_message',
            'muted', 'pinned', 'sla_due_at', 'first_response_at', 'assigned_to_name',
        )
        read_only_fields = fields

    def _msgs(self, obj):
        cache = getattr(obj, '_prefetched_objects_cache', None) or {}
        if 'messages' in cache:
            return list(cache['messages'])
        return list(obj.messages.all())

    def get_message_count(self, obj):
        return len(self._msgs(obj))

    def get_unread_count(self, obj):
        # Customer view: unread staff replies
        return sum(1 for m in self._msgs(obj) if m.is_staff_reply and not m.read_at and not m.is_deleted)

    def get_last_message(self, obj):
        from support.services import last_message_dict
        msgs = self._msgs(obj)
        return last_message_dict(msgs[-1] if msgs else None)

    def get_muted(self, obj):
        return bool(obj.muted_by_user)

    def get_pinned(self, obj):
        return bool(obj.pinned_by_user)

    def get_assigned_to_name(self, obj):
        if not obj.assigned_to_id:
            return ''
        u = obj.assigned_to
        return (u.get_full_name() or u.email) if u else ''


class SupportTicketCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=200)
    body = serializers.CharField()
    category = serializers.CharField(required=False, default='general')


class TicketReplySerializer(serializers.Serializer):
    body = serializers.CharField(required=False, allow_blank=True)
    attachment = serializers.FileField(required=False, allow_null=True)
    reply_to = serializers.UUIDField(required=False, allow_null=True)


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
