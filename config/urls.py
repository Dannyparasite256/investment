"""Root URL configuration for CryptoInvest."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.spa import spa_index

urlpatterns = [
    path('admin/', admin.site.urls),
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
    re_path(
        r'^app/assets/(?P<path>.*)$',
        serve,
        {'document_root': str(settings.BASE_DIR / 'frontend' / 'dist' / 'assets')},
    ),
    re_path(
        r'^app/(?P<path>.*\.(svg|png|ico|webmanifest|js|css|map))$',
        serve,
        {'document_root': str(settings.BASE_DIR / 'frontend' / 'dist')},
    ),
    re_path(r'^app(?:/.*)?$', spa_index, name='spa'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = f'{settings.SITE_NAME} Administration'
admin.site.site_title = f'{settings.SITE_NAME} Admin'
admin.site.index_title = 'Platform Management'
