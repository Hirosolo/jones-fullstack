"""
Admin Panel URLs
"""
from django.urls import path
from utils import admin_panel_views

app_name = 'admin'

urlpatterns = [
    # Auth
    path('login/', admin_panel_views.AdminLoginView.as_view(template_name='admin/login.html'), name='login'),
    path('logout/', admin_panel_views.admin_logout, name='logout'),
    
    # Dashboard
    path('dashboard/', admin_panel_views.admin_dashboard, name='dashboard'),
    path('', admin_panel_views.admin_dashboard, name='index'),
    
    # Products
    path('products/', admin_panel_views.product_list, name='product_list'),
    path('products/create/', admin_panel_views.product_create, name='product_create'),
    path('products/<int:pk>/', admin_panel_views.product_detail, name='product_detail'),
    path('products/<int:pk>/delete/', admin_panel_views.product_delete, name='product_delete'),
    
    # Articles
    path('articles/', admin_panel_views.article_list, name='article_list'),
    path('articles/create/', admin_panel_views.article_create, name='article_create'),
    path('articles/<int:pk>/', admin_panel_views.article_detail, name='article_detail'),
    path('articles/<int:pk>/delete/', admin_panel_views.article_delete, name='article_delete'),
]
