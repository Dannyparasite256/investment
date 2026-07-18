from django.contrib import admin

from .models import AuditLog, CurrencyRate, SiteConfiguration
from .platform_models import (
    GeoRule,
    PlatformBackup,
    PortfolioSnapshot,
    PriceAlert,
    PromoCode,
    TermsAcceptance,
    TermsVersion,
    TradingSignal,
    VIPTier,
    WatchlistItem,
    WebhookEndpoint,
)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'user', 'ip_address', 'object_type', 'message')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'message', 'ip_address', 'object_id')
    readonly_fields = (
        'user', 'action', 'ip_address', 'user_agent', 'path', 'method',
        'object_type', 'object_id', 'message', 'extra', 'created_at', 'updated_at',
    )
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'min_withdrawal', 'max_withdrawal', 'referral_bonus_percent', 'maintenance_mode')


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'rate_to_usd', 'symbol', 'is_active')
    list_editable = ('rate_to_usd', 'is_active')


@admin.register(VIPTier)
class VIPTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'min_total_invested', 'deposit_fee_percent', 'withdrawal_fee_percent', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'bonus_percent', 'bonus_fixed', 'uses_count', 'max_uses', 'is_active', 'expires_at')
    search_fields = ('code',)


@admin.register(TermsVersion)
class TermsVersionAdmin(admin.ModelAdmin):
    list_display = ('version', 'title', 'is_current', 'published_at')


@admin.register(TermsAcceptance)
class TermsAcceptanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'terms', 'ip_address', 'created_at')
    search_fields = ('user__email',)


@admin.register(GeoRule)
class GeoRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'mode', 'is_active')


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'symbol', 'direction', 'target_price', 'is_active', 'triggered_at')


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'symbol', 'label')


@admin.register(TradingSignal)
class TradingSignalAdmin(admin.ModelAdmin):
    list_display = ('title', 'symbol', 'side', 'is_published', 'created_at')


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'is_active')


@admin.register(PlatformBackup)
class PlatformBackupAdmin(admin.ModelAdmin):
    list_display = ('filename', 'size_bytes', 'created_by', 'created_at')


@admin.register(PortfolioSnapshot)
class PortfolioSnapshotAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'equity', 'balance', 'invested', 'profit')
    list_filter = ('date',)
