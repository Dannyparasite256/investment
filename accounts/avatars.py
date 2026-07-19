"""Profile picture helpers: upload storage + import from Google/X avatar URLs."""
from __future__ import annotations

import logging
import mimetypes
import re
import urllib.error
import urllib.request
from pathlib import Path

from django.core.files.base import ContentFile

logger = logging.getLogger('accounts')

# X serves _normal (48px); prefer larger variants when available
_X_SIZE_RE = re.compile(r'_(normal|bigger|mini|200x200|400x400)(\.\w+)$', re.I)


def prefer_high_res_avatar(url: str) -> str:
    url = (url or '').strip()
    if not url:
        return ''
    # Google user content often supports size query
    if 'googleusercontent.com' in url:
        if '=s' in url:
            return re.sub(r'=s\d+-c', '=s256-c', url)
        if url.endswith('=s96-c'):
            return url.replace('=s96-c', '=s256-c')
        return url
    # X/Twitter CDN
    if 'twimg.com' in url or 'pbs.twimg.com' in url:
        return _X_SIZE_RE.sub(r'_400x400\2', url)
    return url


def download_avatar_bytes(url: str, timeout: int = 15) -> tuple[bytes, str]:
    """Return (content, extension) for a remote image URL."""
    url = prefer_high_res_avatar(url)
    if not url.startswith(('http://', 'https://')):
        raise ValueError('Invalid avatar URL')
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'CryptoInvest-Avatar/1.0',
            'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
        },
        method='GET',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        content_type = (resp.headers.get('Content-Type') or '').split(';')[0].strip().lower()
    if not data or len(data) < 32:
        raise ValueError('Empty image from provider')
    if len(data) > 5 * 1024 * 1024:
        raise ValueError('Image too large (max 5MB)')
    ext = mimetypes.guess_extension(content_type) or Path(url.split('?')[0]).suffix or '.jpg'
    if ext in ('.jpe', '.jpeg'):
        ext = '.jpg'
    if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
        # sniff magic
        if data[:3] == b'\xff\xd8\xff':
            ext = '.jpg'
        elif data[:8] == b'\x89PNG\r\n\x1a\n':
            ext = '.png'
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            ext = '.gif'
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            ext = '.webp'
        else:
            ext = '.jpg'
    return data, ext


def apply_remote_avatar(user, url: str, *, force: bool = False, source: str = 'social') -> bool:
    """
    Store remote avatar URL on the user and optionally download into profile_picture.

    - Always updates user.avatar_url when url is present
    - Downloads into profile_picture if empty or force=True
    Returns True if profile_picture was written.
    """
    url = (url or '').strip()
    if not url:
        return False

    user.avatar_url = url[:500]
    wrote_file = False

    if force or not user.profile_picture:
        try:
            data, ext = download_avatar_bytes(url)
            name = f'{source}_{user.pk}{ext}'
            # Replace existing file cleanly
            if user.profile_picture:
                user.profile_picture.delete(save=False)
            user.profile_picture.save(name, ContentFile(data), save=False)
            wrote_file = True
        except Exception as exc:
            logger.info('Avatar download skipped for user=%s: %s', user.pk, exc)

    update_fields = ['avatar_url']
    if wrote_file:
        update_fields.append('profile_picture')
    user.save(update_fields=update_fields)
    return wrote_file


def import_avatar_from_social(user, provider: str, *, force: bool = True) -> bool:
    """Pull avatar from a linked SocialAccount (google / x)."""
    from accounts.models import SocialAccount

    provider = (provider or '').lower().strip()
    if provider == 'twitter':
        provider = 'x'
    social = (
        SocialAccount.objects.filter(user=user, provider=provider)
        .exclude(avatar_url='')
        .order_by('-updated_at')
        .first()
    )
    if not social or not social.avatar_url:
        raise ValueError(f'No {provider.title()} photo linked. Sign in with {provider.title()} first.')
    return apply_remote_avatar(user, social.avatar_url, force=force, source=provider)


def clear_profile_picture(user) -> None:
    if user.profile_picture:
        user.profile_picture.delete(save=False)
    user.profile_picture = None
    user.avatar_url = ''
    user.save(update_fields=['profile_picture', 'avatar_url'])
