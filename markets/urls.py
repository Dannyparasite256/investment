from django.urls import path

from markets import views

app_name = 'markets'

urlpatterns = [
    path('', views.market_overview, name='overview'),
    path('chart/', views.market_chart, name='chart'),
]
