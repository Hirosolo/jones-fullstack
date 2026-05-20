from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from profiles.api.serializers import SocialAccountSerializer
from profiles.models import Profile


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='code',
            type=OpenApiTypes.STR,
            description='Mã thành viên',
            required=False
        )
    ],
    examples=[
        OpenApiExample(
            name="Example request",
            description="Xem thông tin tài khoản",
            value={},
            request_only=True,
        ),
    ],
    responses={200: SocialAccountSerializer},
    summary="Xem thông tin tài khoản",
    description="API trả về thông tin chi tiết của tài khoản người dùng"
)
@api_view(['GET'])
def get_account_detail(request):
    """
    Lấy thông tin tài khoản người dùng.
    """
    user: User = request.user
    profile: Profile = user.profile

    sa_ls = SocialAccount.objects.filter(user=user)


    return Response({
        'user': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'phone': profile.phone,
            'code': profile.code,
        },
        'social_accounts': SocialAccountSerializer(sa_ls, many=True).data,
    })
