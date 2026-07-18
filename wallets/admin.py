from django.contrib import admin

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
    list_display = ('user', 'balance', 'locked_balance', 'total_deposited', 'total_withdrawn', 'total_profit', 'total_invested')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserWalletAddress)
class UserWalletAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'cryptocurrency', 'address', 'label', 'is_default', 'is_verified')
    list_filter = ('cryptocurrency', 'is_default')
    search_fields = ('user__email', 'address')


@admin.register(WalletLedger)
class WalletLedgerAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'wallet', 'entry_type', 'amount', 'balance_after', 'description')
    list_filter = ('entry_type',)
    search_fields = ('wallet__user__email', 'description', 'reference_id')
    readonly_fields = [f.name for f in WalletLedger._meta.fields]

    def has_add_permission(self, request):
        return False
