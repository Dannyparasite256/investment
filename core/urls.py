from django.urls import path

from core import features_views, ux_views, views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/stats/', views.dashboard_stats_api, name='dashboard_stats'),
    path('api/balances/', views.balances_api, name='balances_api'),
    path('theme/', views.set_theme, name='set_theme'),
    path('ui-theme/', views.set_ui_theme, name='set_ui_theme'),
    path('display-currency/', views.set_display_currency, name='set_display_currency'),
    path('portfolio/', features_views.portfolio_performance, name='portfolio'),
    path('vip/', features_views.vip_status, name='vip'),
    path('watchlist/', features_views.watchlist_view, name='watchlist'),
    path('watchlist/<uuid:pk>/delete/', features_views.watchlist_delete, name='watchlist_delete'),
    path('alerts/', features_views.price_alerts_view, name='alerts'),
    path('alerts/<uuid:pk>/delete/', features_views.alert_delete, name='alert_delete'),
    path('activity/', features_views.activity_timeline, name='activity'),
    path('signals/', features_views.signals_list, name='signals'),
    path('tour/complete/', features_views.complete_tour, name='tour_complete'),
    path('language/', features_views.set_language, name='set_language'),
    path('affiliate/', features_views.affiliate_landing_preview, name='affiliate'),
    path('manifest.json', features_views.manifest_json, name='manifest'),
    path('sw.js', features_views.service_worker, name='service_worker'),
    # UX suite
    path('search/', ux_views.global_search, name='search'),
    path('statements/', ux_views.statement_export, name='statements'),
    path('risk-quiz/', ux_views.risk_questionnaire, name='risk_quiz'),
    path('api/fee-preview/', ux_views.fee_preview_api, name='fee_preview'),
    path('api/prices/', ux_views.live_prices_api, name='live_prices'),
    path('api/command-palette/', ux_views.command_palette_data, name='command_palette'),
    path('receipts/deposit/<uuid:pk>/', ux_views.deposit_receipt, name='deposit_receipt'),
    path('receipts/withdrawal/<uuid:pk>/', ux_views.withdraw_receipt, name='withdraw_receipt'),
]
