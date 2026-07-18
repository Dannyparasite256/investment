from decimal import Decimal

from django import forms

from investments.models import InvestmentPlan
from wallets.display import (
    convert_from_usd,
    convert_to_usd,
    format_amount_for_code,
    get_currency_meta,
)


class InvestForm(forms.Form):
    """
    Investment amount is entered in the user's selected *display* currency
    (UGX, USD, BTC, …). On clean, it is converted to platform USD-equivalent
    for wallet debit / plan limit checks.
    """

    amount = forms.DecimalField(
        min_value=Decimal('0.00000001'),
        max_digits=18,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': 'any',
            'placeholder': '0.00',
            'id': 'invest-amount',
            'inputmode': 'decimal',
        }),
    )
    duration_days = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration in days'}),
    )
    auto_reinvest = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def __init__(self, plan: InvestmentPlan = None, currency_code: str = 'USD', *args, **kwargs):
        self.plan = plan
        self.currency_code = (currency_code or 'USD').strip() or 'USD'
        self.currency_meta = get_currency_meta(self.currency_code)
        super().__init__(*args, **kwargs)

        places = int(self.currency_meta.get('decimals', 2))
        symbol = self.currency_meta.get('symbol') or self.currency_code

        # Tighter decimals for whole-unit currencies (e.g. UGX)
        self.fields['amount'].decimal_places = places if places <= 8 else 8
        if places == 0:
            self.fields['amount'].min_value = Decimal('1')
            self.fields['amount'].widget.attrs['step'] = '1'
            self.fields['amount'].widget.attrs['inputmode'] = 'numeric'
        else:
            step = '0.' + ('0' * (places - 1)) + '1' if places > 0 else 'any'
            self.fields['amount'].widget.attrs['step'] = step if places <= 8 else 'any'

        self.fields['amount'].widget.attrs['placeholder'] = f'0{"." + "0" * places if places else ""} {symbol}'

        if plan:
            self.min_display = convert_from_usd(plan.min_deposit, self.currency_code)
            self.max_display = convert_from_usd(plan.max_deposit, self.currency_code)
            self.min_payload = format_amount_for_code(plan.min_deposit, self.currency_code)
            self.max_payload = format_amount_for_code(plan.max_deposit, self.currency_code)

            self.fields['amount'].widget.attrs['min'] = str(self.min_display)
            self.fields['amount'].widget.attrs['max'] = str(self.max_display)

            if not plan.duration_flexible:
                self.fields['duration_days'].widget = forms.HiddenInput()
            else:
                if plan.min_duration_days:
                    self.fields['duration_days'].widget.attrs['min'] = plan.min_duration_days
                if plan.max_duration_days:
                    self.fields['duration_days'].widget.attrs['max'] = plan.max_duration_days
            if not plan.allow_auto_reinvest:
                self.fields['auto_reinvest'].widget = forms.HiddenInput()
        else:
            self.min_display = Decimal('0')
            self.max_display = Decimal('0')
            self.min_payload = format_amount_for_code(0, self.currency_code)
            self.max_payload = format_amount_for_code(0, self.currency_code)

    def clean_amount(self):
        """
        Validate in display units, return platform USD-equivalent for create_investment.
        """
        amount_display = self.cleaned_data['amount']
        symbol = self.currency_meta.get('symbol') or self.currency_code

        if self.plan:
            min_d = convert_from_usd(self.plan.min_deposit, self.currency_code)
            max_d = convert_from_usd(self.plan.max_deposit, self.currency_code)
            min_label = format_amount_for_code(self.plan.min_deposit, self.currency_code)['label']
            max_label = format_amount_for_code(self.plan.max_deposit, self.currency_code)['label']

            if amount_display < min_d:
                raise forms.ValidationError(f'Minimum is {min_label}')
            if amount_display > max_d:
                raise forms.ValidationError(f'Maximum is {max_label}')

        amount_usd = convert_to_usd(amount_display, self.currency_code)
        if amount_usd <= 0:
            raise forms.ValidationError(f'Enter a valid amount in {symbol}')

        # Keep a tiny reverse-conversion floor so displayed min still invests successfully
        if self.plan and amount_display >= convert_from_usd(self.plan.min_deposit, self.currency_code):
            if amount_usd < self.plan.min_deposit:
                amount_usd = self.plan.min_deposit

        return amount_usd
