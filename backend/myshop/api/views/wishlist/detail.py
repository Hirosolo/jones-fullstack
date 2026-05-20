# path: myshop/api/views/wishlist/detail.py

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from myshop.models import Product, WishList


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='product_code',
            type=OpenApiTypes.STR,
            description='Mã sản phẩm (code) để kiểm tra trong danh sách yêu thích',
            required=False
        ),
        OpenApiParameter(
            name='product_slug',
            type=OpenApiTypes.STR,
            description='Slug sản phẩm để kiểm tra trong danh sách yêu thích',
            required=False
        ),
    ],
    responses={200: OpenApiTypes.OBJECT},
    summary="Kiểm tra sản phẩm trong danh sách yêu thích",
    description="Kiểm tra xem sản phẩm có trong danh sách yêu thích của người dùng hay không."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_item_wishlist(request):
    """
    Kiểm tra xem sản phẩm có trong danh sách yêu thích của người dùng hay không.
    Yêu cầu người dùng đã đăng nhập.
    """
    user = request.user
    product_code = request.GET.get('product_code')
    product_slug = request.GET.get('product_slug')

    # Lấy sản phẩm theo code hoặc slug
    if product_code:
        product = Product.objects.filter(code=product_code, is_available=True).first()
    elif product_slug:
        product = Product.objects.filter(slug=product_slug, is_available=True).first()
    else:
        return Response({
            'ok': False,
            'detail': 'Missing product_code or product_slug'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not product:
        return Response({
            'ok': False,
            'detail': 'Product not found or not available'
        }, status=status.HTTP_404_NOT_FOUND)

    wishlist_item = WishList.objects.filter(user=user, product=product, removed=False).first()
    total_items = WishList.objects.filter(user=user, removed=False).count()

    return Response({
        'ok': bool(wishlist_item),
        'num': total_items
    })
