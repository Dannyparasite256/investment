from django import forms

from investments.models import InvestmentPlan


class InvestForm(forms.Form):
    amount = forms.DecimalField(
        min_value=0.00000001,
        max_digits=18,
        decimal_places=8,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'step': 'any',
            'placeholder': '0.00',
            'id': 'invest-amount',
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

    def __init__(self, plan: InvestmentPlan = None, *args, **kwargs):
        self.plan = plan
        super().__init__(*args, **kwargs)
        if plan:
            self.fields['amount'].widget.attrs['min'] = str(plan.min_deposit)
            self.fields['amount'].widget.attrs['max'] = str(plan.max_deposit)
            if not plan.duration_flexible:
                self.fields['duration_days'].widget = forms.HiddenInput()
            else:
                if plan.min_duration_days:
                    self.fields['duration_days'].widget.attrs['min'] = plan.min_duration_days
                if plan.max_duration_days:
                    self.fields['duration_days'].widget.attrs['max'] = plan.max_duration_days
            if not plan.allow_auto_reinvest:
                self.fields['auto_reinvest'].widget = forms.HiddenInput()

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if self.plan:
            if amount < self.plan.min_deposit:
                raise forms.ValidationError(f'Minimum is {self.plan.min_deposit}')
            if amount > self.plan.max_deposit:
                raise forms.ValidationError(f'Maximum is {self.plan.max_deposit}')
        return amount
