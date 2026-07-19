from django.contrib import admin
from django.utils.html import format_html

from wallets.display import format_amount_for_code, get_default_display_code
from wallets.models import Cryptocurrency, UserWalletAddress, Wallet, WalletLedger


@admin.register(Cryptocurrency)
class CryptocurrencyAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'name', 'network', 'deposit_address', 'usd_price',
        'is_active', 'min_deposit', 'min_withdrawal', 'sort_order',
    )
    list_filter = ('network', 'is_active')
    search_fields = ('symbol', 'name', 'deposit_address')
    list_editable = ('is_active', 'sort_order', 'deposit_address', 'usd_price')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'user_currency', 'balance_user', 'balance', 'locked_balance',
        'total_deposited', 'total_withdrawn', 'total_profit', 'total_invested',
    )
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Pref')
    def user_currency(self, obj):
        return get_default_display_code(obj.user)

    @admin.display(description='Balance (user)')
    def balance_user(self, obj):
        code = get_default_display_code(obj.user)
        return format_amount_for_code(obj.balance, code)['label']


@admin.register(UserWalletAddress)
class UserWalletAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'cryptocurrency', 'address', 'label', 'is_default', 'is_verified')
    list_filter = ('cryptocurrency', 'is_default')
    search_fields = ('user__email', 'address')


@admin.register(WalletLedger)
class WalletLedgerAdmin(admin.ModelAdmin):
    list_display = (
        'created_at', 'wallet', 'entry_type', 'amount_user', 'amount',
        'balance_user', 'balance_after', 'description',
    )
    list_filter = ('entry_type',)
    search_fields = ('wallet__user__email', 'description', 'reference_id')
    readonly_fields = [f.name for f in WalletLedger._meta.fields]

    @admin.display(description='Amount (user)')
    def amount_user(self, obj):
        user = getattr(obj.wallet, 'user', None)
        if not user:
            return str(obj.amount)
        code = get_default_display_code(user)
        return format_amount_for_code(obj.amount, code)['label']

    @admin.display(description='Balance (user)')
    def balance_user(self, obj):
        user = getattr(obj.wallet, 'user', None)
        if not user:
            return str(obj.balance_after)
        code = get_default_display_code(user)
        return format_amount_for_code(obj.balance_after, code)['label']

    def has_add_permission(self, request):
        return False
