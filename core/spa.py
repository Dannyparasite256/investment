"""Serve the Vue SPA build (frontend/dist) for app shell routes."""
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET
from django.views.static import serve as static_serve


def _dist() -> Path:
    return Path(settings.BASE_DIR) / 'frontend' / 'dist'


def _no_store(response):
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@require_GET
def spa_index(request, path=''):
    """
    Return the SPA index.html for client-side routes.
    Always revalidate — prevents service-worker / browser cache from pinning an
    old shell that references deleted asset hashes after deploy.
    """
    dist = _dist()
    index = dist / 'index.html'
    if not index.exists():
        raise Http404(
            'Vue SPA not built. Run: cd frontend && npm install && npm run build'
        )
    response = FileResponse(index.open('rb'), content_type='text/html; charset=utf-8')
    return _no_store(response)


@require_GET
def spa_asset(request, path=''):
    """Serve /app/assets/* with long cache (hashed filenames)."""
    response = static_serve(
        request, path, document_root=str(_dist() / 'assets')
    )
    # Content-hashed bundles can be cached; keep moderate TTL for PA free tier
    response['Cache-Control'] = 'public, max-age=86400'
    return response


@require_GET
def spa_root_file(request, path=''):
    """Serve /app/sw.js, manifest, favicon, etc. Never cache the service worker."""
    response = static_serve(request, path, document_root=str(_dist()))
    lower = path.lower()
    if lower.endswith('sw.js') or lower.endswith('registersw.js') or 'workbox' in lower:
        return _no_store(response)
    response['Cache-Control'] = 'public, max-age=3600'
    return response