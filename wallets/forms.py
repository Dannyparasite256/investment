from django import forms

from wallets.models import UserWalletAddress


class WalletAddressForm(forms.ModelForm):
    class Meta:
        model = UserWalletAddress
        fields = ('cryptocurrency', 'address', 'label', 'is_default')
        widgets = {
            'cryptocurrency': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wallet address'}),
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Label (e.g. My Binance)'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
