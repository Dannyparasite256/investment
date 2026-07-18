from decimal import Decimal

from django import forms
from django.conf import settings

from transactions.models import Deposit, Withdrawal
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
    class Meta:
        model = Withdrawal
        fields = ('cryptocurrency', 'amount', 'wallet_address')
        widgets = {
            'cryptocurrency': forms.Select(attrs={
                'class': 'form-select', 'id': 'id_cryptocurrency',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': 'any', 'min': '0',
                'placeholder': '0.00', 'id': 'id_amount',
            }),
            'wallet_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your withdrawal address',
                'id': 'id_wallet_address',
            }),
        }

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['cryptocurrency'].queryset = Cryptocurrency.objects.filter(is_active=True)
        self.fields['cryptocurrency'].empty_label = '— Select currency —'
        self.fields['cryptocurrency'].required = True

    def clean(self):
        cleaned = super().clean()
        amount = cleaned.get('amount')
        crypto = cleaned.get('cryptocurrency')
        if not amount or not crypto:
            return cleaned

        min_w = crypto.min_withdrawal or Decimal(str(settings.MIN_WITHDRAWAL))
        max_w = crypto.max_withdrawal or Decimal(str(settings.MAX_WITHDRAWAL))
        if amount < min_w:
            self.add_error('amount', f'Minimum withdrawal is {min_w} {crypto.symbol}')
        if amount > max_w:
            self.add_error('amount', f'Maximum withdrawal is {max_w} {crypto.symbol}')

        if self.user:
            wallet, _ = Wallet.objects.get_or_create(user=self.user)
            if amount > wallet.available_balance:
                self.add_error('amount', f'Insufficient balance. Available: {wallet.available_balance}')

        address = (cleaned.get('wallet_address') or '').strip()
        if len(address) < 10:
            self.add_error('wallet_address', 'Please enter a valid wallet address.')
        cleaned['wallet_address'] = address
        cleaned['fee'] = crypto.withdrawal_fee or Decimal('0')
        return cleaned
