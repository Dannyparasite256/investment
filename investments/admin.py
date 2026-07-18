from django.contrib import admin

from investments.models import Earning, Investment, InvestmentPlan, Reinvestment


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'status', 'min_deposit', 'max_deposit', 'duration_days',
        'profit_rate_percent', 'payout_frequency', 'risk_level', 'is_featured', 'investors_count',
    )
    list_filter = ('status', 'risk_level', 'payout_frequency', 'is_featured')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description', 'short_description', 'status', 'is_featured', 'icon', 'color', 'sort_order')}),
        ('Limits', {'fields': ('min_deposit', 'max_deposit', 'max_investments_per_user')}),
        ('Duration', {'fields': ('duration_days', 'duration_flexible', 'min_duration_days', 'max_duration_days')}),
        ('Profit Rules', {
            'fields': (
                'profit_method', 'profit_rate_percent', 'fixed_profit_amount',
                'return_percent_min', 'return_percent_max', 'payout_frequency', 'return_principal',
            ),
            'description': 'Configure how earnings are calculated — not hard-coded.',
        }),
        ('Options', {'fields': ('risk_level', 'allow_auto_reinvest', 'allow_manual_reinvest')}),
        ('Stats', {'fields': ('total_invested', 'investors_count')}),
    )
    readonly_fields = ('total_invested', 'investors_count')


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'plan', 'amount', 'status', 'total_earned',
        'payouts_count', 'auto_reinvest', 'started_at', 'matures_at',
    )
    list_filter = ('status', 'auto_reinvest', 'plan')
    search_fields = ('user__email', 'plan__name')
    readonly_fields = ('created_at', 'updated_at', 'started_at')
    date_hierarchy = 'started_at'


@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'investment', 'amount', 'period_number', 'is_reinvested')
    list_filter = ('is_reinvested',)
    search_fields = ('user__email',)


@admin.register(Reinvestment)
class ReinvestmentAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'amount', 'mode', 'source_investment', 'new_investment')
    list_filter = ('mode',)
