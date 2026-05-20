import arrow
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from profiles.models import Profile
from utils.common import get_random_code2


class CustomUsernameValidator(RegexValidator):
    # không chứa khoảng trắng, không chứa ký tự unicode, có thể chứa _,
    # có tối đa 1 dấu _, có tối đa 1 dấu ., không chứa 2 dấu . hoặc _ liên tiếp
    # username dài từ 6 đến 26 ký tự, không chứa ký tự đặc biệt,
    regex = r'^(?=[a-zA-Z0-9._]{6,26}$)(?!.*[_.]{2})[^_.].*[^_.]$'
    message = 'Tên người dùng dài 6-26 ký tự, chỉ gồm chữ, số, dấu . và _'
    flags = 0


@api_view(['POST'])
def sign_up(request):
    """
    Đăng ký tài khoản mới.
    """
    data = request.data
    username = data.get('username', '')
    email = data.get('email', '')
    password = data.get('password', '')
    password2 = data.get('password_2', '')

    if request.method == 'POST':
        with transaction.atomic():
            # Kiểm tra xem username đã tồn tại chưa
            if User.objects.filter(username=username).exists():
                return Response({
                    'ok': False,
                    'msg': 'Tên người dùng này đã tồn tại.'
                })
            # Kiểm tra xem email đã tồn tại chưa
            if User.objects.filter(email__iexact=email).exists():
                return Response({
                    'ok': False,
                    'msg': 'Email này đã tồn tại.'
                })
            # Kiểm tra xem mật khẩu 2 có khớp không
            if password != password2:
                return Response({
                    'ok': False,
                    'msg': 'Mật khẩu không khớp.'
                })

            # Tạo tài khoản mới
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.save()

            # Tạo profile tương ứng
            Profile.objects.create(
                user=user,
                email=email,
                code=get_random_code2(13, 'n')
            )

            return Response({
                'ok': True,
                'msg': 'Tạo tài khoản thành công.'
            })

    return Response({
        'ok': False,
        'msg': 'Method not allowed.'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def sign_in(request):
    """
    Đăng nhập tài khoản.
    """
    data = request.data
    username = data.get('username', '')
    password = data.get('password', '')

    if request.method == 'POST':
        # Kiểm tra xem tài khoản có tồn tại không
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'ok': False,
                'msg': 'Tài khoản không tồn tại.'
            })

        # Kiểm tra mật khẩu
        if not user.check_password(password):
            return Response({
                'ok': False,
                'msg': 'Mật khẩu không đúng.'
            })

        # Đăng nhập thành công
        return Response({
            'ok': True,
            'msg': 'Đăng nhập thành công.'
        })

    return Response({
        'ok': False,
        'msg': 'Method not allowed.'
    })


@api_view(['POST'])
def reset_password(request):
    """
    Đặt lại mật khẩu.
    """
    data = request.data
    email = data.get('email', '')

    if request.method == 'POST':
        # Kiểm tra xem email có tồn tại không
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'ok': False,
                'msg': 'Email không tồn tại.'
            })

        # Tạo mật khẩu mới
        new_password = get_random_code2(8, 'a')
        user.set_password(new_password)
        user.save()

        return Response({
            'ok': True,
            'msg': 'Mật khẩu đã được đặt lại. Mật khẩu mới là: {}'.format(new_password)
        })

    return Response({
        'ok': False,
        'msg': 'Method not allowed.'
    })


@api_view(['POST'])
def change_password(request):
    """
    Đổi mật khẩu.
    """
    data = request.data
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    new_password2 = data.get('new_password2', '')

    if request.method == 'POST':
        user = request.user

    # Kiểm tra mật khẩu cũ
    if not user.check_password(old_password):
        return Response({
            'ok': False,
            'msg': 'Mật khẩu cũ không đúng.'
        })

    # Kiểm tra mật khẩu mới
    if new_password != new_password2:
        return Response({
            'ok': False,
            'msg': 'Mật khẩu mới không khớp.'
        })

    # Đổi mật khẩu
    user.set_password(new_password)
    user.save()

    return Response({
        'ok': True,
        'msg': 'Đổi mật khẩu thành công.'
    })


@api_view(['POST'])
def sign_out(request):
    """
    Đăng xuất tài khoản.
    """
    if request.method == 'POST':
        # Xóa session
        request.session.flush()

        return Response({
            'ok': True,
            'msg': 'Đăng xuất thành công.'
        })

    return Response({
        'ok': False,
        'msg': 'Method not allowed.'
    })