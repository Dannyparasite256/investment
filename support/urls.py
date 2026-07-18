from django.urls import path

from support import views

app_name = 'support'

urlpatterns = [
    path('', views.ticket_list, name='list'),
    path('new/', views.ticket_create, name='create'),
    path('<uuid:pk>/', views.ticket_detail, name='detail'),
]
