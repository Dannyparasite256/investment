"""Authentication, profile, KYC, and 2FA views."""
import base64
import io
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_http_methods, require_POST
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_ratelimit.decorators import ratelimit

from accounts.forms import (
    ChangePasswordForm,
    KYCForm,
    LoginForm,
    PasswordResetConfirmForm,
    PasswordResetRequestForm,
    ProfileForm,
    RegisterForm,
    TwoFactorVerifyForm,
)
from accounts.models import ActivityEvent, KYCDocument, PasswordResetToken, User
from accounts.security import record_login
from accounts.security_models import LoginHistory
from core.models import AuditLog
from core.utils import create_audit_log
from notifications.models import Notification, notify

logger = logging.getLogger('accounts')


def _send_verification_email(user, request):
    token = user.generate_email_token()
    link = request.build_absolute_uri(reverse('accounts:verify_email', args=[token]))
    subject = f'Verify your email — {settings.SITE_NAME}'
    body = (
        f'Hi {user.get_full_name()},\n\n'
        f'Please verify your email by clicking the link below:\n{link}\n\n'
        f'If you did not create an account, ignore this email.\n\n'
        f'— {settings.SITE_NAME}'
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)


@ratelimit(key='ip', rate='10/h', method='POST', block=True)
@require_http_methods(['GET', 'POST'])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    initial = {}
    ref = request.GET.get('ref', '').strip().upper()
    if ref:
        initial['referral_code'] = ref
    form = RegisterForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        _send_verification_email(user, request)
        create_audit_log(request=request, user=user, action=AuditLog.Action.REGISTER, message='User registered')
        ActivityEvent.objects.create(
            user=user, event_type='register', title='Account created', description='Welcome aboard',
        )
        if user.referred_by_id:
            notify(
                user.referred_by, 'New referral',
                f'{user.email} signed up with your link.',
                level=Notification.Level.SUCCESS, category=Notification.Category.REFERRAL,
                link='/referrals/',
            )
        notify(user, 'Welcome!', f'Welcome to {settings.SITE_NAME}. Please verify your email.', category=Notification.Category.SYSTEM)
        messages.success(request, 'Account created! Check your email to verify your address.')
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        record_login(request, user=user, result=LoginHistory.Result.SUCCESS)
        return redirect('core:dashboard')
    # Keep referral in session for social signup buttons
    if ref:
        request.session['pending_referral'] = ref
    from accounts.oauth import enabled_providers
    return render(request, 'accounts/register.html', {
        'form': form,
        'oauth': enabled_providers(),
        'ref': ref or '',
    })


@ratelimit(key='ip', rate='20/h', method='POST', block=True)
@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    form = LoginForm(request=request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.two_factor_enabled:
            request.session['pre_2fa_user_id'] = user.pk
            request.session['pre_2fa_remember'] = form.cleaned_data.get('remember_me', True)
            return redirect('accounts:verify_2fa')
        login(request, user)
        if not form.cleaned_data.get('remember_me'):
            request.session.set_expiry(0)
        record_login(request, user=user, result=LoginHistory.Result.SUCCESS, auth_method='password')
        create_audit_log(request=request, user=user, action=AuditLog.Action.LOGIN, message='User logged in')
        ActivityEvent.objects.create(user=user, event_type='login', title='Logged in')
        messages.success(request, f'Welcome back, {user.display_name}!')
        next_url = request.GET.get('next') or reverse('core:dashboard')
        return redirect(next_url)
    if request.method == 'POST' and not form.is_valid():
        email = (request.POST.get('username') or '')[:254]
        record_login(request, email=email, result=LoginHistory.Result.FAILED)
    from accounts.oauth import enabled_providers
    return render(request, 'accounts/login.html', {
        'form': form,
        'oauth': enabled_providers(),
        'next': request.GET.get('next') or '',
    })


@require_http_methods(['GET', 'POST'])
def verify_2fa_view(request):
    user_id = request.session.get('pre_2fa_user_id')
    if not user_id:
        return redirect('accounts:login')
    user = get_object_or_404(User, pk=user_id)
    form = TwoFactorVerifyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        token = form.cleaned_data['token']
        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if device and device.verify_token(token):
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if not request.session.pop('pre_2fa_remember', True):
                request.session.set_expiry(0)
            request.session.pop('pre_2fa_user_id', None)
            create_audit_log(request=request, user=user, action=AuditLog.Action.LOGIN, message='2FA login success')
            return redirect('core:dashboard')
        messages.error(request, 'Invalid authentication code.')
    return render(request, 'accounts/verify_2fa.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    create_audit_log(request=request, user=request.user, action=AuditLog.Action.LOGOUT, message='User logged out')
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')


def verify_email_view(request, token):
    user = get_object_or_404(User, email_verification_token=token)
    if not user.email_verified:
        user.email_verified = True
        user.email_verification_token = ''
        user.save(update_fields=['email_verified', 'email_verification_token'])
        create_audit_log(request=request, user=user, action=AuditLog.Action.EMAIL_VERIFY, message='Email verified')
        notify(user, 'Email Verified', 'Your email has been verified successfully.', level=Notification.Level.SUCCESS)
        messages.success(request, 'Email verified successfully!')
    return redirect('core:dashboard')


@login_required
@require_POST
def resend_verification_view(request):
    if request.user.email_verified:
        messages.info(request, 'Email already verified.')
    else:
        _send_verification_email(request.user, request)
        messages.success(request, 'Verification email sent.')
    return redirect('accounts:profile')


@ratelimit(key='ip', rate='5/h', method='POST', block=True)
@require_http_methods(['GET', 'POST'])
def password_reset_request_view(request):
    form = PasswordResetRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].lower().strip()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            pr = PasswordResetToken.create_for_user(user)
            link = request.build_absolute_uri(reverse('accounts:password_reset_confirm', args=[pr.token]))
            send_mail(
                f'Password reset — {settings.SITE_NAME}',
                f'Use this link to reset your password (valid 24h):\n{link}\n',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
            create_audit_log(request=request, user=user, action=AuditLog.Action.PASSWORD_RESET, message='Password reset requested')
        messages.success(request, 'If an account exists with that email, a reset link has been sent.')
        return redirect('accounts:login')
    return render(request, 'accounts/password_reset_request.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def password_reset_confirm_view(request, token):
    pr = get_object_or_404(PasswordResetToken, token=token)
    if not pr.is_valid():
        messages.error(request, 'This reset link is invalid or has expired.')
        return redirect('accounts:password_reset')
    form = PasswordResetConfirmForm(user=pr.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        pr.used = True
        pr.save(update_fields=['used'])
        create_audit_log(request=request, user=pr.user, action=AuditLog.Action.PASSWORD_RESET, message='Password reset completed')
        messages.success(request, 'Password updated. You can now log in.')
        return redirect('accounts:login')
    return render(request, 'accounts/password_reset_confirm.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def profile_view(request):
    # Avatar actions (import from Google/X, remove)
    if request.method == 'POST' and request.POST.get('avatar_action'):
        action = request.POST.get('avatar_action')
        try:
            from accounts.avatars import clear_profile_picture, import_avatar_from_social
            if action == 'import_google':
                import_avatar_from_social(request.user, 'google', force=True)
                messages.success(request, 'Profile photo updated from Google.')
            elif action == 'import_x':
                import_avatar_from_social(request.user, 'x', force=True)
                messages.success(request, 'Profile photo updated from X.')
            elif action == 'remove':
                clear_profile_picture(request.user)
                messages.info(request, 'Profile photo removed.')
            else:
                messages.error(request, 'Unknown photo action.')
        except ValueError as exc:
            messages.error(request, str(exc))
        except Exception:
            messages.error(request, 'Could not update profile photo. Try again.')
        return redirect('accounts:profile')

    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        # If user uploaded a new picture, keep avatar_url as fallback only
        create_audit_log(request=request, user=request.user, action=AuditLog.Action.PROFILE_UPDATE, message='Profile updated')
        messages.success(request, 'Profile updated.')
        if request.headers.get('HX-Request'):
            return render(request, 'accounts/partials/profile_form.html', {'form': form})
        response = redirect('accounts:profile')
        # Persist appearance cookies so guests/next request stay in sync
        theme = getattr(user, 'preferred_theme', None) or 'dark'
        ui_theme = getattr(user, 'preferred_ui_theme', None) or 'classic'
        if theme in ('dark', 'light'):
            response.set_cookie('theme', theme, max_age=365 * 24 * 3600, samesite='Lax', path='/')
        if ui_theme in ('classic', 'premium'):
            response.set_cookie('ui_theme', ui_theme, max_age=365 * 24 * 3600, samesite='Lax', path='/')
        return response
    kyc_latest = request.user.kyc_documents.order_by('-created_at').first()
    # Refresh user from DB so avatar fields are current
    request.user.refresh_from_db()
    social_links = {
        s.provider: s for s in request.user.social_accounts.all()
    }
    from accounts.social_features import referral_share_text, social_risk_signals
    share_text, share_link, x_intent = referral_share_text(request.user, request)
    return render(request, 'accounts/profile.html', {
        'form': form,
        'kyc_latest': kyc_latest,
        'referral_link': share_link,
        'social_links': social_links,
        'avatar_url': request.user.avatar_display_url,
        'x_share_url': x_intent,
        'share_text': share_text,
        'signals': social_risk_signals(request.user),
        'public_profile_url': request.build_absolute_uri(
            reverse('accounts:public_profile', args=[request.user.referral_code])
        ) if request.user.public_profile_enabled else '',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def change_password_view(request):
    form = ChangePasswordForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        create_audit_log(request=request, user=request.user, action=AuditLog.Action.PASSWORD_CHANGE, message='Password changed')
        messages.success(request, 'Password changed successfully.')
        return redirect('accounts:profile')
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def kyc_view(request):
    pending = request.user.kyc_documents.filter(
        status__in=[KYCDocument.Status.PENDING, KYCDocument.Status.UNDER_REVIEW]
    ).exists()
    if request.user.is_kyc_verified:
        messages.info(request, 'Your identity is already verified.')
        return redirect('accounts:profile')
    form = KYCForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        if pending:
            messages.warning(request, 'You already have a KYC submission under review.')
            return redirect('accounts:kyc')
        doc = form.save(commit=False)
        doc.user = request.user
        doc.save()
        create_audit_log(request=request, user=request.user, action=AuditLog.Action.KYC_SUBMIT, message='KYC submitted', object_id=str(doc.id))
        notify(request.user, 'KYC Submitted', 'Your documents are under review.', category=Notification.Category.KYC)
        messages.success(request, 'KYC documents submitted for review.')
        return redirect('accounts:profile')
    history = request.user.kyc_documents.all()[:5]
    return render(request, 'accounts/kyc.html', {'form': form, 'history': history, 'pending': pending})


@login_required
@require_http_methods(['GET', 'POST'])
def setup_2fa_view(request):
    user = request.user
    device, created = TOTPDevice.objects.get_or_create(user=user, name='default', defaults={'confirmed': False})
    if request.method == 'POST':
        form = TwoFactorVerifyForm(request.POST)
        if form.is_valid() and device.verify_token(form.cleaned_data['token']):
            device.confirmed = True
            device.save()
            user.two_factor_enabled = True
            user.save(update_fields=['two_factor_enabled'])
            create_audit_log(request=request, user=user, action=AuditLog.Action.TWO_FA_ENABLE, message='2FA enabled')
            notify(user, '2FA Enabled', 'Two-factor authentication is now active.', level=Notification.Level.SUCCESS, category=Notification.Category.SECURITY)
            messages.success(request, 'Two-factor authentication enabled.')
            return redirect('accounts:profile')
        messages.error(request, 'Invalid code. Scan the QR and try again.')
    else:
        form = TwoFactorVerifyForm()

    # QR as data URI
    qr_uri = device.config_url
    try:
        import qrcode
        img = qrcode.make(qr_uri)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
    except Exception:
        qr_b64 = ''

    return render(request, 'accounts/setup_2fa.html', {
        'form': form,
        'qr_b64': qr_b64,
        'secret': device.bin_key.hex() if hasattr(device, 'bin_key') else '',
        'config_url': qr_uri,
    })


@login_required
@require_POST
def disable_2fa_view(request):
    user = request.user
    TOTPDevice.objects.filter(user=user).delete()
    user.two_factor_enabled = False
    user.save(update_fields=['two_factor_enabled'])
    create_audit_log(request=request, user=user, action=AuditLog.Action.TWO_FA_DISABLE, message='2FA disabled')
    messages.success(request, 'Two-factor authentication disabled.')
    return redirect('accounts:profile')
