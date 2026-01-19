from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Resource URLs
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/<int:pk>/', views.resource_detail, name='resource_detail'),
    path('resources/create/', views.resource_create, name='resource_create'),
    path('resources/<int:pk>/update/', views.resource_update, name='resource_update'),
    path('resources/<int:pk>/delete/', views.resource_delete, name='resource_delete'),
    
    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Member URLs
    path('members/', views.member_list, name='member_list'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    path('members/create/', views.member_create, name='member_create'),
    path('members/<int:pk>/update/', views.member_update, name='member_update'),
    path('members/<int:pk>/delete/', views.member_delete, name='member_delete'),
    
    # Transaction URLs
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('checkout/', views.checkout_resource, name='checkout_resource'),
    path('checkin/<int:transaction_id>/', views.checkin_resource, name='checkin_resource'),
    
    # Stock Management URLs
    path('resources/<int:resource_id>/stock-log/', views.stock_log_create, name='stock_log_create'),
]