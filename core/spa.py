"""Serve the Vue SPA build (frontend/dist) for app shell routes."""
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


def _dist() -> Path:
    return Path(settings.BASE_DIR) / 'frontend' / 'dist'


@require_GET
def spa_index(request, path=''):
    """
    Return the SPA index.html for client-side routes.
    Static assets under /app-assets/ are mapped separately in urls.
    """
    dist = _dist()
    index = dist / 'index.html'
    if not index.exists():
        raise Http404(
            'Vue SPA not built. Run: cd frontend && npm install && npm run build'
        )
    return FileResponse(index.open('rb'), content_type='text/html')
