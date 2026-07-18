from django.urls import path

from transactions import views

app_name = 'transactions'

urlpatterns = [
    path('deposits/', views.deposit_list, name='deposit_list'),
    path('deposits/new/', views.deposit_create, name='deposit_create'),
    path('deposits/<uuid:pk>/', views.deposit_detail, name='deposit_detail'),
    path('withdrawals/', views.withdraw_list, name='withdraw_list'),
    path('withdrawals/new/', views.withdraw_create, name='withdraw_create'),
    path('withdrawals/<uuid:pk>/cancel/', views.withdraw_cancel, name='withdraw_cancel'),
    path('history/', views.history, name='history'),
    path('receipts/<uuid:pk>/', views.transaction_receipt, name='receipt'),
    path('crypto/<int:pk>/info/', views.crypto_deposit_info, name='crypto_info'),
    path('crypto/<int:pk>/saved-addresses/', views.saved_addresses_for_crypto, name='saved_addresses'),
]
