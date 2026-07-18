from django.urls import path

from cms import views

app_name = 'cms'

urlpatterns = [
    path('faq/', views.faq_list, name='faq'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('p/<slug:slug>/', views.page_detail, name='page'),
]
