from django.urls import path

from utils import auth_views

app_name = 'utils'

urlpatterns = [
    # Kết nối đăng nhập với NextJS
    path('django/auth/next/jwt/', auth_views.get_jwt_next, name='get_next_jwt'),
    path('django/auth/next/session/', auth_views.get_session_view, name='get_session'),
    path('django/auth/next/logout/', auth_views.logout_next, name='logout_next'),
]
