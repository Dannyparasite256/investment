from django.urls import path

from accounts import oauth_views, views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('oauth/status/', oauth_views.oauth_status, name='oauth_status'),
    path('oauth/<str:provider>/', oauth_views.oauth_start, name='oauth_start'),
    path('oauth/<str:provider>/callback/', oauth_views.oauth_callback, name='oauth_callback'),
    path('verify-email/<str:token>/', views.verify_email_view, name='verify_email'),
    path('resend-verification/', views.resend_verification_view, name='resend_verification'),
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('kyc/', views.kyc_view, name='kyc'),
    path('2fa/setup/', views.setup_2fa_view, name='setup_2fa'),
    path('2fa/verify/', views.verify_2fa_view, name='verify_2fa'),
    path('2fa/disable/', views.disable_2fa_view, name='disable_2fa'),
]
