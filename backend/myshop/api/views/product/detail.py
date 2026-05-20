# path: myshop/api/views/product/detail.py

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from myshop.api.serializers import ProductDetailSerializer
from myshop.models import Product


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='code',
            type=OpenApiTypes.STR,
            description='Mã sản phẩm cần xem chi tiết',
            required=False
        ),
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            description='Slug sản phẩm (nếu không có code thì sẽ tìm theo slug)',
            required=False
        )
    ],
    responses={200: ProductDetailSerializer},
    summary="Xem chi tiết sản phẩm",
    description="API trả về thông tin chi tiết của một sản phẩm dựa trên mã hoặc slug sản phẩm."
                " Nếu không tìm thấy sẽ trả về thông báo không tìm thấy."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail_view(request, slug=None):
    """
    API chi tiết sản phẩm
    """
    user = request.user
    from icecream import ic
    ic(user)
    code = request.GET.get('code', '').strip()
    url_slug = slug  # Slug từ URL path
    query_slug = request.GET.get('slug', '').strip()  # Slug từ query parameter

    p = None
    if code:
        p = Product.objects.filter(code=code).first()
    elif url_slug:  # Ưu tiên slug từ URL
        p = Product.objects.filter(slug=url_slug).first()
    elif query_slug:  # Fallback sang query parameter
        p = Product.objects.filter(slug=query_slug).first()

    if not p:
        return Response({
            'ok': False,
            'msg': 'Không tìm thấy sản phẩm'
        })

    # Chi tiết sản phẩm
    data = ProductDetailSerializer(p, context={'user': user}).data
    return Response(data)

