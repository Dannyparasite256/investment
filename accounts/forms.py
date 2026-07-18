"""Account forms: registration, login, profile, KYC, 2FA, password."""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password

from accounts.models import KYCDocument, User


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create password', 'autocomplete': 'new-password'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password', 'autocomplete': 'new-password'}),
    )
    referral_code = forms.CharField(
        required=False,
        label='Referral Code',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional referral code'}),
    )
    agree_terms = forms.BooleanField(
        label='I agree to the Terms of Service and Privacy Policy',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address', 'autocomplete': 'email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        code = (cleaned.get('referral_code') or '').strip().upper()
        if code:
            try:
                cleaned['referrer'] = User.objects.get(referral_code=code)
            except User.DoesNotExist:
                self.add_error('referral_code', 'Invalid referral code.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.email = self.cleaned_data['email']
        referrer = self.cleaned_data.get('referrer')
        if referrer:
            user.referred_by = referrer
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address', 'autocomplete': 'email', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'current-password'}),
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if email and password:
            self.user_cache = authenticate(self.request, username=email.lower().strip(), password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Invalid email or password.')
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


class ProfileForm(forms.ModelForm):
    preferred_currency = forms.ChoiceField(
        required=True,
        label='Display currency',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_preferred_currency'}),
    )

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone', 'country', 'date_of_birth',
            'profile_picture', 'preferred_theme', 'preferred_currency',
        )
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'preferred_theme': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        choices = []
        try:
            from wallets.display import get_default_display_code, get_display_currencies_for_user
            if user and user.pk:
                for o in get_display_currencies_for_user(user):
                    choices.append((o['code'], o['label']))
                initial = get_default_display_code(user)
            else:
                from wallets.models import Cryptocurrency
                for c in Cryptocurrency.objects.filter(is_active=True):
                    choices.append((c.symbol, f'{c.name} ({c.symbol})'))
                choices.append(('USD', 'USD (platform value)'))
                initial = choices[0][0] if choices else 'USD'
        except Exception:
            choices = [('USD', 'USD')]
            initial = 'USD'
        self.fields['preferred_currency'].choices = choices
        self.fields['preferred_currency'].initial = (
            user.preferred_currency if user and user.preferred_currency else initial
        )


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your account email'}),
    )


class PasswordResetConfirmForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='New password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}),
    )
    new_password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
    )


class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class KYCForm(forms.ModelForm):
    class Meta:
        model = KYCDocument
        fields = ('document_type', 'document_number', 'front_image', 'back_image', 'selfie_image')
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document number'}),
            'front_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'back_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'selfie_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class TwoFactorVerifyForm(forms.Form):
    token = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center letter-spacing',
            'placeholder': '000000',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
        }),
    )
