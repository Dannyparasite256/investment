from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import currency_views, platform_views, receipt_views, staff_views, views

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
router.register('support', platform_views.SupportTicketViewSet, basename='support')
router.register('watchlist', platform_views.WatchlistViewSet, basename='watchlist')
router.register('alerts', platform_views.PriceAlertViewSet, basename='alerts')

urlpatterns = [
    path('auth/token/', views.CustomAuthToken.as_view(), name='api-token'),
    path('auth/register/', platform_views.RegisterView.as_view(), name='api-register'),
    path('me/', views.MeView.as_view(), name='api-me'),
    path('profile/', platform_views.ProfileView.as_view(), name='api-profile'),
    path('profile/password/', platform_views.ChangePasswordView.as_view(), name='api-change-password'),
    path('wallet/', views.WalletView.as_view(), name='api-wallet'),
    # Currency (real-time conversion)
    path('currencies/', currency_views.CurrencyOptionsView.as_view(), name='api-currencies'),
    path('balances/', currency_views.BalancesView.as_view(), name='api-balances-v1'),
    path('display-currency/', currency_views.SetDisplayCurrencyView.as_view(), name='api-display-currency'),
    # Receipts
    path('receipts/deposit/<uuid:pk>/', receipt_views.DepositReceiptView.as_view(), name='api-deposit-receipt'),
    path('receipts/withdrawal/<uuid:pk>/', receipt_views.WithdrawalReceiptView.as_view(), name='api-withdrawal-receipt'),
    path('receipts/transaction/<uuid:pk>/', receipt_views.TransactionReceiptView.as_view(), name='api-tx-receipt'),
    # User platform
    path('referrals/', platform_views.ReferralsView.as_view(), name='api-referrals'),
    path('referrals/leaderboard/', platform_views.LeaderboardView.as_view(), name='api-leaderboard'),
    path('vip/', platform_views.VIPView.as_view(), name='api-vip'),
    path('portfolio/', platform_views.PortfolioView.as_view(), name='api-portfolio'),
    path('signals/', platform_views.SignalsView.as_view(), name='api-signals'),
    path('activity/', platform_views.ActivityView.as_view(), name='api-activity'),
    path('markets/pairs/', platform_views.MarketPairsView.as_view(), name='api-market-pairs'),
    path('faq/', platform_views.FAQListView.as_view(), name='api-faq'),
    path('pages/<slug:slug>/', platform_views.CMSPageDetailView.as_view(), name='api-cms-page'),
    path('calculator/', platform_views.CalculatorView.as_view(), name='api-calculator'),
    path('statements/', platform_views.StatementsView.as_view(), name='api-statements'),
    path('risk-quiz/', platform_views.RiskQuizView.as_view(), name='api-risk-quiz'),
    path('dashboard-stats/', platform_views.DashboardStatsView.as_view(), name='api-dashboard-stats'),
    path('search/', platform_views.SearchView.as_view(), name='api-search'),
    path('fee-preview/', platform_views.FeePreviewView.as_view(), name='api-fee-preview'),
    # Staff admin
    path('staff/dashboard/', staff_views.StaffDashboardView.as_view(), name='api-staff-dashboard'),
    path('staff/deposits/', staff_views.StaffDepositListView.as_view(), name='api-staff-deposits'),
    path('staff/deposits/<uuid:pk>/<str:action>/', staff_views.StaffDepositActionView.as_view(), name='api-staff-deposit-action'),
    path('staff/withdrawals/', staff_views.StaffWithdrawalListView.as_view(), name='api-staff-withdrawals'),
    path('staff/withdrawals/<uuid:pk>/<str:action>/', staff_views.StaffWithdrawalActionView.as_view(), name='api-staff-withdrawal-action'),
    path('staff/kyc/', staff_views.StaffKYCListView.as_view(), name='api-staff-kyc'),
    path('staff/kyc/<uuid:pk>/<str:action>/', staff_views.StaffKYCActionView.as_view(), name='api-staff-kyc-action'),
    path('staff/users/', staff_views.StaffUserListView.as_view(), name='api-staff-users'),
    path('staff/tickets/', staff_views.StaffTicketListView.as_view(), name='api-staff-tickets'),
    path('staff/tickets/<uuid:pk>/', staff_views.StaffTicketDetailView.as_view(), name='api-staff-ticket-detail'),
    path('', include(router.urls)),
]
