"""OAuth start + callback views for Google and X social signup/login."""
import logging
import secrets

from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from accounts.models import ActivityEvent, SocialAccount, User
from accounts.oauth import (
    build_authorize_url,
    enabled_providers,
    fetch_profile,
    make_pkce_pair,
    make_state,
    oauth_enabled,
)
from accounts.security import record_login
from accounts.security_models import LoginHistory
from core.models import AuditLog
from core.utils import create_audit_log
from notifications.models import Notification, notify
from wallets.models import Wallet

logger = logging.getLogger('accounts')

PROVIDER_ALIASES = {
    'google': SocialAccount.Provider.GOOGLE,
    'x': SocialAccount.Provider.X,
    'twitter': SocialAccount.Provider.X,
}


def _normalize_provider(provider: str) -> str | None:
    key = (provider or '').lower().strip()
    if key in PROVIDER_ALIASES:
        return 'x' if key == 'twitter' else key
    return None


def _callback_url(request, provider: str) -> str:
    """
    Absolute OAuth callback URL.

    Prefer SITE_URL so PythonAnywhere (TLS terminated at proxy) does not
    send http://… to Google/X while consoles are registered with https://…
    Optional overrides: GOOGLE_OAUTH_REDIRECT_URI / X_OAUTH_REDIRECT_URI
    """
    from django.conf import settings

    provider = (provider or '').lower()
    if provider == 'google':
        override = (getattr(settings, 'GOOGLE_OAUTH_REDIRECT_URI', '') or '').strip()
        if override:
            return override
    if provider in ('x', 'twitter'):
        override = (getattr(settings, 'X_OAUTH_REDIRECT_URI', '') or '').strip()
        if override:
            return override

    path = reverse('accounts:oauth_callback', args=['x' if provider == 'twitter' else provider])
    site = (getattr(settings, 'SITE_URL', '') or '').rstrip('/')
    if site:
        return f'{site}{path}'
    # Fallback: force https when the request looks public
    url = request.build_absolute_uri(path)
    if url.startswith('http://') and not settings.DEBUG:
        url = 'https://' + url[len('http://'):]
    return url


@require_GET
def oauth_start(request, provider: str):
    """Redirect user to Google / X authorization screen."""
    provider = _normalize_provider(provider)
    if not provider or not oauth_enabled(provider):
        messages.error(request, 'This social login is not configured yet.')
        return redirect('accounts:login')

    # Logged-in users may start OAuth to link Google/X for avatar import
    state = make_state()
    request.session['oauth_state'] = state
    request.session['oauth_provider'] = provider
    request.session['oauth_next'] = request.GET.get('next') or (
        reverse('accounts:profile') if request.user.is_authenticated else ''
    )
    request.session['oauth_link_mode'] = bool(request.user.is_authenticated)
    # Preserve referral for new social signups
    ref = (request.GET.get('ref') or request.session.get('pending_referral') or '').strip().upper()
    if ref:
        request.session['pending_referral'] = ref

    code_challenge = ''
    if provider == 'x':
        verifier, challenge = make_pkce_pair()
        request.session['oauth_code_verifier'] = verifier
        code_challenge = challenge

    redirect_uri = _callback_url(request, provider)
    logger.info('OAuth start provider=%s redirect_uri=%s', provider, redirect_uri)
    try:
        url = build_authorize_url(
            provider,
            redirect_uri=redirect_uri,
            state=state,
            code_challenge=code_challenge,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('accounts:login')
    return redirect(url)


@require_GET
def oauth_status(request):
    """
    Safe diagnostics for OAuth setup (no secrets).
    Open: /accounts/oauth/status/
    """
    from django.conf import settings

    def mask(val: str) -> str:
        val = (val or '').strip()
        if not val:
            return '(empty)'
        if len(val) <= 8:
            return val[:2] + '…' + val[-2:]
        return val[:4] + '…' + val[-4:] + f' (len={len(val)})'

    google_id = getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '') or ''
    x_id = getattr(settings, 'X_OAUTH_CLIENT_ID', '') or ''
    ctx = {
        'site_url': getattr(settings, 'SITE_URL', ''),
        'providers': enabled_providers(),
        'google_client_id_mask': mask(google_id),
        'x_client_id_mask': mask(x_id),
        'google_callback': _callback_url(request, 'google'),
        'x_callback': _callback_url(request, 'x'),
        'x_hint': (
            'X OAuth 2.0 Client ID is usually longer than 25 chars. '
            'If yours is exactly 25 characters, you may have pasted the API Key '
            'instead of the OAuth 2.0 Client ID from User authentication settings.'
            if x_id and len(x_id) == 25 else ''
        ),
    }
    return render(request, 'accounts/oauth_status.html', ctx)


@require_GET
def oauth_callback(request, provider: str):
    """Handle OAuth redirect: create/link user and log in."""
    provider = _normalize_provider(provider)
    if not provider:
        messages.error(request, 'Unknown login provider.')
        return redirect('accounts:login')

    err = request.GET.get('error')
    if err:
        desc = request.GET.get('error_description') or err
        logger.warning('OAuth callback error provider=%s error=%s desc=%s', provider, err, desc)
        if provider == 'x':
            messages.error(
                request,
                'X login failed. In the X Developer Portal, set Callback URI to '
                f'{_callback_url(request, "x")} '
                'and enable OAuth 2.0 (Type: Web App, Read permissions). '
                f'Detail: {desc}',
            )
        else:
            messages.error(request, f'Social login cancelled or failed: {desc}')
        return redirect('accounts:login')

    state = request.GET.get('state') or ''
    code = request.GET.get('code') or ''
    expected = request.session.get('oauth_state')
    sess_provider = request.session.get('oauth_provider')
    if not code or not state or state != expected or sess_provider != provider:
        messages.error(request, 'Invalid or expired social login session. Please try again.')
        return redirect('accounts:login')

    code_verifier = request.session.pop('oauth_code_verifier', '') if provider == 'x' else ''
    # Clear one-time state
    request.session.pop('oauth_state', None)
    request.session.pop('oauth_provider', None)
    link_mode = request.session.pop('oauth_link_mode', False)
    next_url = request.session.pop('oauth_next', '') or reverse('core:dashboard')

    try:
        profile = fetch_profile(
            provider,
            code=code,
            redirect_uri=_callback_url(request, provider),
            code_verifier=code_verifier,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('accounts:profile' if request.user.is_authenticated else 'accounts:login')

    if not profile.provider_user_id:
        messages.error(request, 'Could not read your social profile.')
        return redirect('accounts:profile' if request.user.is_authenticated else 'accounts:login')

    # Link social account + avatar to the already-logged-in user
    if request.user.is_authenticated and link_mode:
        try:
            _link_social_to_user(request.user, profile)
            messages.success(
                request,
                f'{provider.title()} linked. You can use their photo on your profile.',
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect('accounts:profile')

    try:
        user, created = _login_or_register_from_profile(request, profile)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('accounts:login')

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    # Session flag for withdrawal re-auth (Google confirmation window)
    if provider == 'google':
        from django.utils import timezone
        request.session['social_reauth_at'] = timezone.now().isoformat()
        request.session['social_reauth_provider'] = 'google'
    record_login(
        request, user=user, result=LoginHistory.Result.SUCCESS,
        auth_method=provider,
    )
    create_audit_log(
        request=request, user=user,
        action=AuditLog.Action.LOGIN if not created else AuditLog.Action.REGISTER,
        message=f'{"Signed up" if created else "Logged in"} with {provider}',
    )
    ActivityEvent.objects.create(
        user=user,
        event_type='register' if created else 'login',
        title='Account created via social' if created else f'Logged in with {provider.title()}',
        description=f'Provider: {provider}',
        metadata={'provider': provider},
    )
    if created:
        messages.success(request, f'Welcome! Your account was created with {provider.title()}.')
    else:
        messages.success(request, f'Welcome back, {user.display_name}!')

    if not next_url.startswith('/'):
        next_url = reverse('core:dashboard')
    return redirect(next_url)


def _link_social_to_user(user, profile):
    """Attach Google/X identity to an existing logged-in account and import avatar."""
    from accounts.avatars import apply_remote_avatar

    provider = PROVIDER_ALIASES[profile.provider]
    by_uid = SocialAccount.objects.filter(
        provider=provider, provider_user_id=profile.provider_user_id,
    ).select_related('user').first()
    if by_uid and by_uid.user_id != user.pk:
        raise ValueError(f'This {profile.provider.title()} account is already linked to another user.')

    fields = {
        'email': profile.email or '',
        'username': profile.username or '',
        'display_name': profile.display_name or '',
        'avatar_url': profile.avatar_url or '',
        'extra_data': profile.raw or {},
        'provider_user_id': profile.provider_user_id,
    }
    social = by_uid or SocialAccount.objects.filter(user=user, provider=provider).first()
    if social:
        for k, v in fields.items():
            setattr(social, k, v)
        social.user = user
        social.save()
    else:
        SocialAccount.objects.create(user=user, provider=provider, **fields)

    if profile.provider == 'google':
        from accounts.social_features import mark_google_verified
        mark_google_verified(user)
    if profile.avatar_url:
        apply_remote_avatar(user, profile.avatar_url, force=True, source=profile.provider)
    # Treat link as recent re-auth for withdrawals
    if profile.provider == 'google':
        # session set in callback after this returns
        pass


@transaction.atomic
def _login_or_register_from_profile(request, profile):
    """
    Link existing SocialAccount, or match by email, or create a new user.
    Returns (user, created).
    """
    provider = PROVIDER_ALIASES[profile.provider]
    social = (
        SocialAccount.objects.select_related('user')
        .filter(provider=provider, provider_user_id=profile.provider_user_id)
        .first()
    )
    if social:
        # Refresh profile metadata
        social.email = profile.email or social.email
        social.username = profile.username or social.username
        social.display_name = profile.display_name or social.display_name
        social.avatar_url = profile.avatar_url or social.avatar_url
        social.extra_data = profile.raw or social.extra_data
        social.save()
        user = social.user
        if not user.is_active:
            raise ValueError('This account is suspended. Contact support.')
        if profile.provider == 'google':
            from accounts.social_features import mark_google_verified
            mark_google_verified(user)
        if profile.avatar_url:
            try:
                from accounts.avatars import apply_remote_avatar
                # Refresh photo on each Google/X login
                apply_remote_avatar(user, profile.avatar_url, force=True, source=profile.provider)
            except Exception:
                pass
        return user, False

    user = None
    created = False
    # Link by real email when Google provides one (not the synthetic X address)
    if profile.email and not profile.email.endswith('@users.noreply.x.com'):
        user = User.objects.filter(email__iexact=profile.email).first()

    if user is None:
        email = profile.email
        if not email:
            email = f'{provider}_{profile.provider_user_id}@oauth.local'
        # Ensure unique
        base_email = email
        n = 0
        while User.objects.filter(email__iexact=email).exists():
            n += 1
            local, _, domain = base_email.partition('@')
            email = f'{local}+{n}@{domain}'

        user = User(
            email=email.lower(),
            first_name=profile.first_name or '',
            last_name=profile.last_name or '',
            email_verified=not email.endswith(('@users.noreply.x.com', '@oauth.local')),
            google_verified=(profile.provider == 'google'),
            last_login_method=profile.provider,
        )
        user.set_unusable_password()
        # Referral
        ref = (request.session.pop('pending_referral', None) or '').strip().upper()
        if ref:
            referrer = User.objects.filter(referral_code__iexact=ref).exclude(email=user.email).first()
            if referrer:
                user.referred_by = referrer
        user.save()
        Wallet.objects.get_or_create(user=user)
        created = True
        if profile.provider == 'google':
            from accounts.social_features import mark_google_verified
            mark_google_verified(user)
        if user.referred_by_id:
            notify(
                user.referred_by, 'New referral',
                f'{user.email} signed up with your link ({provider}).',
                level=Notification.Level.SUCCESS, category=Notification.Category.REFERRAL,
                link='/referrals/',
            )
        notify(
            user, 'Welcome!',
            f'Welcome to the platform. You signed in with {provider.title()}.',
            category=Notification.Category.SYSTEM,
        )
    else:
        if not user.is_active:
            raise ValueError('This account is suspended. Contact support.')
        # Fill empty names from social profile
        updated = []
        if not user.first_name and profile.first_name:
            user.first_name = profile.first_name
            updated.append('first_name')
        if not user.last_name and profile.last_name:
            user.last_name = profile.last_name
            updated.append('last_name')
        if profile.email and not profile.email.endswith('@users.noreply.x.com') and not user.email_verified:
            user.email_verified = True
            updated.append('email_verified')
        if profile.provider == 'google' and not user.google_verified:
            user.google_verified = True
            updated.append('google_verified')
        if updated:
            user.save(update_fields=updated)
        if profile.provider == 'google':
            from accounts.social_features import mark_google_verified
            mark_google_verified(user)

    SocialAccount.objects.create(
        user=user,
        provider=provider,
        provider_user_id=profile.provider_user_id,
        email=profile.email or '',
        username=profile.username or '',
        display_name=profile.display_name or '',
        avatar_url=profile.avatar_url or '',
        extra_data=profile.raw or {},
    )
    if profile.avatar_url:
        try:
            from accounts.avatars import apply_remote_avatar
            apply_remote_avatar(
                user, profile.avatar_url,
                force=created or not bool(user.profile_picture),
                source=profile.provider,
            )
        except Exception:
            logger.info('Could not import social avatar for %s', user.email)
    return user, created
