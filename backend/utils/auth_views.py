import arrow
from django.conf import settings
from django.contrib.auth import login, logout
from django.http import HttpResponse
from django.shortcuts import render, redirect, resolve_url
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


def get_jwt_next(request):
    """
    Tạo JWT token và set cookie để tạo trạng thái đã đăng nhập trên NextJS.
    Giải pháp này chỉ hoạt động khi NextJS và Django chạy trên cùng một domain.
    """
    user = request.user
    if user.is_authenticated:
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        refresh_token = str(refresh)
        response = render(
            request,
            'next_auth/jwt.html',
            {'redirect_url': settings.NEXTJS_REDIRECT_URL}
        )
        exp = arrow.now().shift(days=+settings.NEXTJS_LOGIN_COOKIE_EXPIRE_DAYS).datetime
        response.set_cookie(
            key=settings.NEXTJS_JWT_KEY_NAME,
            value=token,
            expires=exp,
            httponly=False  # set False là để NextJS có thể đọc được cookie này qua JS
        )
        response.set_cookie(
            key=settings.NEXTJS_REFRESH_TOKEN_KEY_NAME,
            value=refresh_token,
            expires=exp,
            httponly=False
        )
        return response
    return HttpResponse('Error on login, please try again.')


# Định nghĩa serializer cho response của session view
class SessionResponseSerializer(serializers.Serializer):
    ok = serializers.BooleanField()


@extend_schema(
    summary="Get Session View",
    description="Đăng nhập Django session tương ứng với user JWT đã xác thực.",
    responses=SessionResponseSerializer  # Khai báo serializer cho response
)
@api_view(['GET'])
def get_session_view(request):
    """
    Sau khi đăng nhập với JWT tại Next thì cũng cần đăng nhập Django với user tương ứng.
    """
    user = request.user
    login(request, user, 'django.contrib.auth.backends.ModelBackend')
    # session = Session.objects.filter(user=user)
    return Response({'ok': True})


def logout_next(request):
    """
    Logout từ next (xóa cookies token), redirect đến view này để thoát đăng nhập của Django,
    sau đó redirect đến home để hoàn thành.
    """
    logout(request)
    redirect_url = resolve_url(settings.LOGOUT_REDIRECT_URL or '/')
    return redirect(redirect_url)