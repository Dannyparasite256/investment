from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views

router = DefaultRouter()
router.register('cryptocurrencies', views.CryptocurrencyViewSet, basename='crypto')
router.register('plans', views.InvestmentPlanViewSet, basename='plan')
router.register('investments', views.InvestmentViewSet, basename='investment')
router.register('deposits', views.DepositViewSet, basename='deposit')
router.register('withdrawals', views.WithdrawalViewSet, basename='withdrawal')
router.register('transactions', views.TransactionViewSet, basename='transaction')
router.register('earnings', views.EarningViewSet, basename='earning')
router.register('notifications', views.NotificationViewSet, basename='notification')
router.register('wallet-addresses', views.WalletAddressViewSet, basename='wallet-address')
router.register('kyc', views.KYCViewSet, basename='kyc')

urlpatterns = [
    path('auth/token/', views.CustomAuthToken.as_view(), name='api-token'),
    path('me/', views.MeView.as_view(), name='api-me'),
    path('wallet/', views.WalletView.as_view(), name='api-wallet'),
    path('', include(router.urls)),
]
