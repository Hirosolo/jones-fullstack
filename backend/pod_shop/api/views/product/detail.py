# path: pod_shop/api/views/product/detail.py

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pod_shop.api.serializers import ProductDetailSerializer
from pod_shop.models import Product


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
    code = request.GET.get('code', '').strip()
    slug = request.GET.get('slug', '').strip()

    p = None
    if code:
        p = Product.objects.filter(code=code).first()
    elif slug:
        p = Product.objects.filter(slug=slug).first()

    if not p:
        return Response({
            'ok': False,
            'msg': 'Product not found',
        })

    # Chi tiết sản phẩm
    data = ProductDetailSerializer(p, context={'request': request}).data
    return Response(data)