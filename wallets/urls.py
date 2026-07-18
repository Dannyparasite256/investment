from django.urls import path

from wallets import views

app_name = 'wallets'

urlpatterns = [
    path('', views.wallet_overview, name='overview'),
    path('addresses/add/', views.address_create, name='address_add'),
    path('addresses/<uuid:pk>/delete/', views.address_delete, name='address_delete'),
]
