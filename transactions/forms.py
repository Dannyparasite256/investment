from decimal import Decimal

from django import forms
from django.conf import settings

from core.utils import quantize_amount
from transactions.models import Deposit, Withdrawal
from wallets.display import (
    convert_from_usd,
    convert_to_usd,
    crypto_units_to_usd,
    format_amount_for_code,
    get_currency_meta,
    usd_to_crypto_units,
)
from wallets.models import Cryptocurrency, Wallet


class DepositForm(forms.ModelForm):
    promo_code = forms.CharField(
        required=False,
        label='Promo code',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional promo code',
            'id': 'id_promo_code',
        }),
    )

    class Meta:
        model = Deposit
        fields = ('cryptocurrency', 'amount', 'transaction_hash', 'screenshot', 'promo_code')
        widgets = {
            'cryptocurrency': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_cryptocurrency',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': 'any', 'min': '0',
                'placeholder': '0.00', 'id': 'id_amount',
            }),
            'transaction_hash': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction hash / TxID',
                'id': 'id_transaction_hash',
            }),
            'screenshot': forms.ClearableFileInput(attrs={
                'class': 'form-control', 'accept': 'image/*', 'id': 'id_screenshot',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cryptocurrency'].queryset = Cryptocurrency.objects.filter(is_active=True)
        self.fields['cryptocurrency'].empty_label = '— Select currency —'
        self.fields['cryptocurrency'].required = True

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None:
            raise forms.ValidationError('Enter the deposit amount in the selected crypto.')
        crypto = self.cleaned_data.get('cryptocurrency')
        if crypto and amount < crypto.min_deposit:
            raise forms.ValidationError(
                f'Minimum deposit is {crypto.min_deposit} {crypto.symbol}'
            )
        return amount

    def clean_transaction_hash(self):
        tx = (self.cleaned_data.get('transaction_hash') or '').strip()
        if len(tx) < 6:
            raise forms.ValidationError('Enter a valid transaction hash / TxID (at least 6 characters).')
        # Only block if already approved with same hash
        if Deposit.objects.filter(
            transaction_hash__iexact=tx,
            status=Deposit.Status.APPROVED,
        ).exists():
            raise forms.ValidationError('This transaction hash was already used for an approved deposit.')
        return tx

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('cryptocurrency'):
            self.add_error('cryptocurrency', 'Select the cryptocurrency / network you sent funds on.')
        return cleaned


class WithdrawalForm(forms.ModelForm):
    """
    Amount is entered in the user's selected *display* currency (UGX, USD, BTC…).
    On clean, amount is converted to platform USD-equivalent for wallet lock/debit.
    """

    class Meta:
        model = Withdrawal
        fields = ('cryptocurrency', 'amount', 'wallet_address')
        widgets = {
            'cryptocurrency': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_cryptocurrency',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg', 'step': 'any', 'min': '0',
                'placeholder': '0.00', 'id': 'id_amount', 'inputmode': 'decimal',
            }),
            'wallet_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your withdrawal address',
                'id': 'id_wallet_address',
            }),
        }

    def __init__(self, user=None, currency_code: str = 'USD', *args, **kwargs):
        self.user = user
        self.currency_code = (currency_code or 'USD').strip() or 'USD'
        self.currency_meta = get_currency_meta(self.currency_code)
        super().__init__(*args, **kwargs)

        qs = Cryptocurrency.objects.filter(is_active=True).order_by('sort_order', 'symbol')
        self.fields['cryptocurrency'].queryset = qs
        self.fields['cryptocurrency'].empty_label = '— Select payout network —'
        self.fields['cryptocurrency'].required = True
        self.fields['cryptocurrency'].label = 'Payout crypto / network'
        self.fields['amount'].label = f'Amount ({self.currency_meta.get("symbol") or self.currency_code})'

        places = int(self.currency_meta.get('decimals', 2))
        if places == 0:
            self.fields['amount'].widget.attrs['step'] = '1'
            self.fields['amount'].widget.attrs['inputmode'] = 'numeric'
        symbol = self.currency_meta.get('symbol') or self.currency_code
        self.fields['amount'].widget.attrs['placeholder'] = f'0{"." + "0" * places if places else ""}'

        # Default payout network: preferred crypto if set, else first USDT, else first active
        if not self.is_bound:
            pref_crypto = qs.filter(symbol__iexact=self.currency_code).first()
            if pref_crypto:
                self.fields['cryptocurrency'].initial = pref_crypto.pk
            else:
                usdt = qs.filter(symbol__icontains='USDT').first()
                if usdt:
                    self.fields['cryptocurrency'].initial = usdt.pk

    def clean(self):
        cleaned = super().clean()
        amount_display = cleaned.get('amount')
        crypto = cleaned.get('cryptocurrency')
        symbol = self.currency_meta.get('symbol') or self.currency_code

        if amount_display is None or not crypto:
            return cleaned

        if amount_display <= 0:
            self.add_error('amount', f'Enter a positive amount in {symbol}')
            return cleaned

        # Soft-refresh prices for accurate conversion
        try:
            from core.price_feed import ensure_fresh_prices
            ensure_fresh_prices()
            crypto.refresh_from_db()
        except Exception:
            pass

        price = Decimal(str(crypto.usd_price or 0))
        if price <= 0:
            self.add_error(
                'cryptocurrency',
                f'No live rate for {crypto.symbol}. Please wait a moment and try again.',
            )
            return cleaned

        # Display currency → platform USD
        amount_usd = convert_to_usd(amount_display, self.currency_code)
        if amount_usd <= 0:
            self.add_error('amount', f'Enter a valid amount in {symbol}')
            return cleaned

        # Crypto units that will be paid out (gross, before fee concept on platform)
        try:
            crypto_amount = usd_to_crypto_units(amount_usd, crypto)
        except ValueError as exc:
            self.add_error('cryptocurrency', str(exc))
            return cleaned

        min_c = Decimal(str(crypto.min_withdrawal or 0))
        max_c = Decimal(str(crypto.max_withdrawal or 0))
        # Fallback global USD limits when crypto limits missing
        if min_c <= 0:
            min_c = usd_to_crypto_units(Decimal(str(settings.MIN_WITHDRAWAL)), crypto)
        if max_c <= 0:
            max_c = usd_to_crypto_units(Decimal(str(settings.MAX_WITHDRAWAL)), crypto)

        if crypto_amount < min_c:
            min_disp = format_amount_for_code(crypto_units_to_usd(min_c, crypto), self.currency_code)
            self.add_error(
                'amount',
                f'Minimum withdrawal is {min_disp["label"]} '
                f'({min_c} {crypto.symbol})',
            )
        if max_c > 0 and crypto_amount > max_c:
            max_disp = format_amount_for_code(crypto_units_to_usd(max_c, crypto), self.currency_code)
            self.add_error(
                'amount',
                f'Maximum withdrawal is {max_disp["label"]} '
                f'({max_c} {crypto.symbol})',
            )

        if self.user:
            wallet, _ = Wallet.objects.get_or_create(user=self.user)
            if amount_usd > wallet.available_balance:
                avail = format_amount_for_code(wallet.available_balance, self.currency_code)
                self.add_error(
                    'amount',
                    f'Insufficient balance. Available: {avail["label"]}',
                )

        address = (cleaned.get('wallet_address') or '').strip()
        if len(address) < 10:
            self.add_error('wallet_address', 'Please enter a valid wallet address.')
        cleaned['wallet_address'] = address

        # Fees in platform USD: network fee (crypto units → USD) + VIP %
        from core.vip import apply_withdrawal_fee
        network_fee_usd = crypto_units_to_usd(crypto.withdrawal_fee or 0, crypto)
        fee_usd, fee_pct = apply_withdrawal_fee(self.user, amount_usd, network_fee_usd)
        if fee_usd >= amount_usd:
            self.add_error('amount', 'Amount is too small after network / VIP fees.')

        # Model stores platform USD amounts (wallet ledger)
        cleaned['amount'] = quantize_amount(amount_usd, 8)
        cleaned['fee'] = quantize_amount(fee_usd, 8)
        cleaned['net_amount'] = quantize_amount(amount_usd - fee_usd, 8)
        # Extra context for view / transaction metadata
        cleaned['display_amount'] = amount_display
        cleaned['display_currency'] = self.currency_code
        cleaned['crypto_amount'] = crypto_amount
        cleaned['crypto_fee_units'] = Decimal(str(crypto.withdrawal_fee or 0))
        cleaned['rate_usd'] = price
        cleaned['fee_percent'] = fee_pct
        return cleaned
