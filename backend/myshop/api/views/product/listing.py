# path: myshop/api/views/product/listing.py

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from myshop.api.serializers import ProductSerializer
from myshop.models import Product


@extend_schema(
    responses={200: ProductSerializer(many=True)},
    summary="Danh sách sản phẩm nổi bật",
    description="Trả về danh sách sản phẩm nổi bật (có giá khuyến mãi hoặc bán chạy)."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def featured_products_view(request):
    """
    API trả về danh sách sản phẩm nổi bật
    - Có giá khuyến mãi hoặc được mua nhiều lần
    """
    user = request.user
    qs = Product.objects.filter(
        Q(price_promo__isnull=False) | Q(times_purchased__gte=5),
        is_available=True
    ).order_by('-times_purchased')[:12]  # Có thể tùy chỉnh số lượng

    data = ProductSerializer(qs, many=True, context={'user': user}).data
    return Response(data)


@extend_schema(
    responses={200: ProductSerializer(many=True)},
    summary="Danh sách sản phẩm bán chạy",
    description="Trả về danh sách sản phẩm bán chạy nhất dựa trên số lần mua."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def best_selling_products_view(request):
    """
    API trả về danh sách sản phẩm bán chạy nhất
    """
    user = request.user
    qs = Product.objects.filter(is_available=True).order_by('-times_purchased')[:12]
    data = ProductSerializer(qs, many=True, context={'user': user}).data
    return Response(data)


class ProductListView(ListAPIView):
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer
