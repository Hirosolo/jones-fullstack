from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from articles.api.serializers import ArticleDetailSerializer
from articles.models import Article


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            description='Slug của bài viết cần xem chi tiết',
            required=True
        )
    ],
    responses={200: ArticleDetailSerializer},
    summary="Xem chi tiết bài viết",
    description="API trả về thông tin chi tiết của một bài viết dựa trên slug."
                " Nếu không tìm thấy sẽ trả về thông báo không tìm thấy."
)
class ArticleDetailView(GenericAPIView):
    """
    API chi tiết bài viết
    """
    serializer_class = ArticleDetailSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        slug = request.GET.get('slug', '')
        p = Article.objects.filter(slug=slug, status='published').first()
        if not p:
            raise NotFound('Không tìm thấy bài viết')
        serializer = self.get_serializer(p)
        return Response(serializer.data)

