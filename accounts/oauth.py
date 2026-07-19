"""Google + X (Twitter) OAuth 2.0 helpers for Django UI signup/login."""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from django.conf import settings

logger = logging.getLogger('accounts')


@dataclass
class OAuthProfile:
    provider: str
    provider_user_id: str
    email: str = ''
    first_name: str = ''
    last_name: str = ''
    username: str = ''
    display_name: str = ''
    avatar_url: str = ''
    raw: dict | None = None


def oauth_enabled(provider: str) -> bool:
    provider = (provider or '').lower()
    if provider == 'google':
        return bool(getattr(settings, 'GOOGLE_OAUTH_CLIENT_ID', '') and getattr(settings, 'GOOGLE_OAUTH_CLIENT_SECRET', ''))
    if provider in ('x', 'twitter'):
        return bool(getattr(settings, 'X_OAUTH_CLIENT_ID', '') and getattr(settings, 'X_OAUTH_CLIENT_SECRET', ''))
    return False


def enabled_providers() -> dict[str, bool]:
    return {
        'google': oauth_enabled('google'),
        'x': oauth_enabled('x'),
    }


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def make_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for OAuth PKCE (S256)."""
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode('ascii')).digest())
    return verifier, challenge


def make_state() -> str:
    return secrets.token_urlsafe(24)


def http_json(method: str, url: str, *, data: dict | None = None, headers: dict | None = None, form: bool = False) -> dict:
    hdrs = {'Accept': 'application/json', 'User-Agent': 'CryptoInvest-OAuth/1.0'}
    if headers:
        hdrs.update(headers)
    body = None
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode('utf-8')
            hdrs.setdefault('Content-Type', 'application/x-www-form-urlencoded')
        else:
            body = json.dumps(data).encode('utf-8')
            hdrs.setdefault('Content-Type', 'application/json')
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode('utf-8')
            if not raw:
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        err_body = ''
        try:
            err_body = exc.read().decode('utf-8', errors='replace')[:500]
        except Exception:
            pass
        logger.warning('OAuth HTTP %s %s: %s %s', method, url, exc.code, err_body)
        raise ValueError(f'OAuth provider error ({exc.code}). {err_body}') from exc
    except Exception as exc:
        logger.warning('OAuth request failed %s %s: %s', method, url, exc)
        raise ValueError('Could not reach OAuth provider. Try again.') from exc


# ---------------------------------------------------------------------------
# Google
# ---------------------------------------------------------------------------

def google_authorize_url(*, redirect_uri: str, state: str) -> str:
    params = {
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
        'include_granted_scopes': 'true',
    }
    return 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)


def google_fetch_profile(*, code: str, redirect_uri: str) -> OAuthProfile:
    token = http_json(
        'POST',
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
            'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        },
        form=True,
    )
    access = token.get('access_token')
    if not access:
        raise ValueError('Google did not return an access token.')
    info = http_json(
        'GET',
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {access}'},
    )
    email = (info.get('email') or '').strip().lower()
    if not email:
        raise ValueError('Google account has no email address.')
    return OAuthProfile(
        provider='google',
        provider_user_id=str(info.get('sub') or ''),
        email=email,
        first_name=(info.get('given_name') or '').strip()[:150],
        last_name=(info.get('family_name') or '').strip()[:150],
        display_name=(info.get('name') or '').strip()[:200],
        avatar_url=(info.get('picture') or '')[:500],
        raw=info,
    )


# ---------------------------------------------------------------------------
# X (Twitter) OAuth 2.0 + PKCE
# ---------------------------------------------------------------------------

def x_authorize_url(*, redirect_uri: str, state: str, code_challenge: str) -> str:
    # Scopes must be space-separated; encode spaces as %20 (not +) for X.
    # users.read is required for login; tweet.read is commonly required by X app setup.
    params = {
        'response_type': 'code',
        'client_id': settings.X_OAUTH_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': 'users.read tweet.read offline.access',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    qs = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    # Prefer x.com (twitter.com still works but X portal docs use x.com)
    return 'https://x.com/i/oauth2/authorize?' + qs


def x_fetch_profile(*, code: str, redirect_uri: str, code_verifier: str) -> OAuthProfile:
    # Confidential client: Basic auth with client_id:client_secret
    basic = base64.b64encode(
        f'{settings.X_OAUTH_CLIENT_ID}:{settings.X_OAUTH_CLIENT_SECRET}'.encode('utf-8')
    ).decode('ascii')
    token = http_json(
        'POST',
        'https://api.x.com/2/oauth2/token',
        data={
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri,
            'code_verifier': code_verifier,
            # client_id required in body for some X app types even with Basic auth
            'client_id': settings.X_OAUTH_CLIENT_ID,
        },
        headers={'Authorization': f'Basic {basic}'},
        form=True,
    )
    access = token.get('access_token')
    if not access:
        raise ValueError('X did not return an access token.')
    me = http_json(
        'GET',
        'https://api.x.com/2/users/me?' + urllib.parse.urlencode({
            'user.fields': 'id,name,username,profile_image_url',
        }),
        headers={'Authorization': f'Bearer {access}'},
    )
    data = me.get('data') or {}
    uid = str(data.get('id') or '')
    if not uid:
        raise ValueError('X did not return a user id.')
    username = (data.get('username') or '').strip()
    name = (data.get('name') or username or 'X User').strip()
    # X free tier often has no email — use stable synthetic address for account key.
    email = f'x_{uid}@users.noreply.x.com'
    parts = name.split(None, 1)
    first = parts[0][:150] if parts else ''
    last = parts[1][:150] if len(parts) > 1 else ''
    return OAuthProfile(
        provider='x',
        provider_user_id=uid,
        email=email,
        first_name=first,
        last_name=last,
        username=username[:150],
        display_name=name[:200],
        avatar_url=(data.get('profile_image_url') or '')[:500],
        raw=data,
    )


def build_authorize_url(provider: str, *, redirect_uri: str, state: str, code_challenge: str = '') -> str:
    provider = provider.lower()
    if provider == 'google':
        return google_authorize_url(redirect_uri=redirect_uri, state=state)
    if provider in ('x', 'twitter'):
        if not code_challenge:
            raise ValueError('PKCE challenge required for X login.')
        return x_authorize_url(redirect_uri=redirect_uri, state=state, code_challenge=code_challenge)
    raise ValueError('Unknown OAuth provider.')


def fetch_profile(provider: str, *, code: str, redirect_uri: str, code_verifier: str = '') -> OAuthProfile:
    provider = provider.lower()
    if provider == 'google':
        return google_fetch_profile(code=code, redirect_uri=redirect_uri)
    if provider in ('x', 'twitter'):
        return x_fetch_profile(code=code, redirect_uri=redirect_uri, code_verifier=code_verifier)
    raise ValueError('Unknown OAuth provider.')


def profile_to_dict(p: OAuthProfile) -> dict[str, Any]:
    return {
        'provider': p.provider,
        'provider_user_id': p.provider_user_id,
        'email': p.email,
        'first_name': p.first_name,
        'last_name': p.last_name,
        'username': p.username,
        'display_name': p.display_name,
        'avatar_url': p.avatar_url,
    }
