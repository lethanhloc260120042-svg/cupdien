from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('subscriptions/', views.manage_subscriptions, name='manage_subscriptions'),
    path('subscriptions/delete/<int:sub_id>/', views.delete_subscription, name='delete_subscription'),
    path('test-notify/', views.test_notify, name='test_notify'),
    path('api/areas/', views.get_areas, name='get_areas'),
    path('outage/<int:outage_id>/', views.outage_detail, name='outage_detail'),
]
