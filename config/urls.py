"""Root URL configuration for CryptoInvest."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.spa import spa_asset, spa_index, spa_root_file


def ads_txt(_request):
    """Google AdSense publisher file — must be at domain root /ads.txt"""
    pub = getattr(settings, 'ADSENSE_CLIENT', 'ca-pub-4816791058478135').replace('ca-pub-', 'pub-')
    return HttpResponse(
        f'google.com, {pub}, DIRECT, f08c47fec0942fa0\n',
        content_type='text/plain; charset=utf-8',
    )


def robots_txt(_request):
    """Allow AdSense / Google crawlers to index the public site."""
    body = (
        'User-agent: *\n'
        'Allow: /\n'
        'Disallow: /admin/\n'
        'Disallow: /staff/\n'
        'Disallow: /accounts/\n'
        'Disallow: /api/\n'
        f'Sitemap: {getattr(settings, "SITE_URL", "").rstrip("/")}/sitemap.xml\n'
    )
    return HttpResponse(body, content_type='text/plain; charset=utf-8')


def adsense_html_verify(_request):
    """Serve AdSense HTML verification file when configured in .env."""
    name = getattr(settings, 'ADSENSE_HTML_VERIFY_NAME', '') or ''
    content = getattr(settings, 'ADSENSE_HTML_VERIFY_CONTENT', '') or ''
    if not name or not content:
        return HttpResponse('Not configured', status=404, content_type='text/plain')
    return HttpResponse(content, content_type='text/html; charset=utf-8')


urlpatterns = [
    # AdSense / crawler verification (root URLs)
    path('ads.txt', ads_txt, name='ads_txt'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('admin/', admin.site.urls),
]

# AdSense "Upload an HTML file" method — e.g. /adsenseXXXX.html
_adsense_html = getattr(settings, 'ADSENSE_HTML_VERIFY_NAME', '') or ''
if _adsense_html and '/' not in _adsense_html and '..' not in _adsense_html:
    urlpatterns.insert(
        2,
        path(_adsense_html, adsense_html_verify, name='adsense_html_verify'),
    )

urlpatterns += [
    path('staff/', include('staffpanel.urls')),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('wallets/', include('wallets.urls')),
    path('investments/', include('investments.urls')),
    path('transactions/', include('transactions.urls')),
    path('notifications/', include('notifications.urls')),
    path('referrals/', include('referrals.urls')),
    path('support/', include('support.urls')),
    path('pages/', include('cms.urls')),
    path('markets/', include('markets.urls')),
    path('api/v1/', include('api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='api-docs'),
    # Vue SPA shell at /app/ (build with: cd frontend && set VITE_BASE=/app/ && npm run build)
    re_path(r'^app/assets/(?P<path>.*)$', spa_asset, name='spa-assets'),
    re_path(
        r'^app/(?P<path>.*\.(svg|png|ico|webmanifest|js|css|map))$',
        spa_root_file,
        name='spa-root-files',
    ),
    re_path(r'^app(?:/.*)?$', spa_index, name='spa'),
    # User uploads (profile photos, KYC, deposit screenshots).
    # Required when DEBUG=False — e.g. PythonAnywhere without a /media/ Static files map.
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': str(settings.MEDIA_ROOT)},
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = f'{settings.SITE_NAME} Administration'
admin.site.site_title = f'{settings.SITE_NAME} Admin'
admin.site.index_title = 'Platform Management'
