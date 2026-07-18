from django.urls import path

from referrals import views

app_name = 'referrals'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]
