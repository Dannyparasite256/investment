from django.urls import path

from investments import views

app_name = 'investments'

urlpatterns = [
    path('', views.plan_list, name='plans'),
    path('my/', views.my_investments, name='my'),
    path('earnings/', views.earnings_history, name='earnings'),
    path('calculator/', views.calculator, name='calculator'),
    path('plan/<slug:slug>/', views.plan_detail, name='plan_detail'),
    path('plan/<slug:slug>/invest/', views.invest, name='invest'),
    path('<uuid:pk>/', views.investment_detail, name='detail'),
    path('<uuid:pk>/reinvest/', views.reinvest_view, name='reinvest'),
]
