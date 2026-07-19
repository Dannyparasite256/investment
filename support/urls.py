from django.urls import path

from support import views

app_name = 'support'

urlpatterns = [
    path('', views.ticket_list, name='list'),
    path('new/', views.ticket_create, name='create'),
    path('<uuid:pk>/', views.ticket_detail, name='detail'),
    path('<uuid:pk>/poll/', views.ticket_poll, name='poll'),
    path('<uuid:pk>/typing/', views.ticket_typing, name='typing'),
    path('<uuid:pk>/leave/', views.ticket_leave, name='leave'),
]
