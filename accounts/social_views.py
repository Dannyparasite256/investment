"""Social account management, sessions, public profile, invites."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.models import SocialAccount, User
from accounts.security_models import LoginHistory
from accounts.social_features import (
    referral_share_text,
    send_invite_email,
    social_risk_signals,
    x_share_intent_url,
)


@login_required
@require_http_methods(['GET', 'POST'])
def social_connections(request):
    """Link/unlink Google & X, share tools, security preferences overview."""
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'unlink':
            provider = (request.POST.get('provider') or '').lower()
            if provider not in ('google', 'x'):
                messages.error(request, 'Unknown provider.')
            else:
                has_password = request.user.has_usable_password()
                other = request.user.social_accounts.exclude(provider=provider).exists()
                if not has_password and not other:
                    messages.error(
                        request,
                        'Set a password or keep another social login before unlinking this one.',
                    )
                else:
                    deleted, _ = SocialAccount.objects.filter(
                        user=request.user, provider=provider,
                    ).delete()
                    if provider == 'google':
                        request.user.google_verified = False
                        request.user.save(update_fields=['google_verified'])
                    if deleted:
                        messages.success(request, f'{provider.title()} disconnected.')
                    else:
                        messages.info(request, f'No {provider.title()} account was linked.')
            return redirect('accounts:social_connections')
        if action == 'invite':
            try:
                send_invite_email(
                    request.user,
                    request.POST.get('email', ''),
                    request.POST.get('note', ''),
                )
                messages.success(request, 'Invite email sent.')
            except Exception as exc:
                messages.error(request, str(exc) or 'Could not send invite.')
            return redirect('accounts:social_connections')

    links = {s.provider: s for s in request.user.social_accounts.all()}
    share_text, share_link, x_intent = referral_share_text(request.user, request)
    logins = LoginHistory.objects.filter(
        user=request.user, result=LoginHistory.Result.SUCCESS,
    )[:15]
    return render(request, 'accounts/social_connections.html', {
        'links': links,
        'share_text': share_text,
        'share_link': share_link,
        'x_share_url': x_intent,
        'logins': logins,
        'signals': social_risk_signals(request.user),
        'oauth_google_url': reverse('accounts:oauth_start', args=['google']),
        'oauth_x_url': reverse('accounts:oauth_start', args=['x']),
    })


@login_required
@require_GET
def security_sessions(request):
    """Login history with auth method."""
    logins = LoginHistory.objects.filter(user=request.user)[:40]
    return render(request, 'accounts/security_sessions.html', {
        'logins': logins,
        'last_method': request.user.last_login_method or 'password',
    })


@require_GET
def public_profile(request, code: str):
    """Opt-in public referral profile."""
    user = get_object_or_404(
        User.objects.filter(public_profile_enabled=True),
        referral_code__iexact=code,
    )
    share_text, share_link, x_intent = referral_share_text(user, request)
    x_acc = user.social_accounts.filter(provider='x').first()
    return render(request, 'accounts/public_profile.html', {
        'profile_user': user,
        'avatar_url': user.avatar_display_url,
        'x_handle': x_acc.username if x_acc else '',
        'google_verified': user.google_verified or user.email_verified,
        'share_link': share_link,
        'x_share_url': x_intent,
        'ref_code': user.referral_code,
    })


@login_required
@require_POST
def share_signal_x(request, pk):
    """Redirect to X intent for a published trading signal."""
    from core.platform_models import TradingSignal
    signal = get_object_or_404(TradingSignal, pk=pk, is_published=True)
    text = f'{signal.side.upper()} {signal.symbol}: {signal.title}'
    if signal.target:
        text += f' · Target {signal.target}'
    url = request.build_absolute_uri(reverse('core:signals'))
    return redirect(x_share_intent_url(text, url))
