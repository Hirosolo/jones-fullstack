# path: utils/api/views/static_page/detail.py

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from utils.api.serializers import StaticPageSerializer
from utils.models import StaticPage


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            description='Slug của trang tĩnh cần xem chi tiết',
            required=True
        )
    ],
    responses={200: StaticPageSerializer},
    summary='Xem chi tiết trang tĩnh',
    description='API trả về thông tin chi tiết của một trang tĩnh dựa trên slug.'
                ' Nếu không tìm thấy sẽ trả về thông báo không tìm thấy.'
)
class StaticPageDetailView(GenericAPIView):
    """
    API chi tiết trang tĩnh
    """
    serializer_class = StaticPageSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        slug = request.GET.get('slug', '')
        p = StaticPage.objects.filter(slug=slug, status='P').first()
        if not p:
            raise NotFound('Page not found')
        serializer = self.get_serializer(p)
        return Response(serializer.data)

