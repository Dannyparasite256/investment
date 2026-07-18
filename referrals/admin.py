from django.contrib import admin

from referrals.models import ReferralCommission, ReferralProgram


@admin.register(ReferralProgram)
class ReferralProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'commission_percent', 'commission_on', 'is_active')


@admin.register(ReferralCommission)
class ReferralCommissionAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'amount', 'rate_percent', 'source', 'status', 'created_at')
    list_filter = ('status', 'source')
    search_fields = ('referrer__email', 'referred_user__email')
