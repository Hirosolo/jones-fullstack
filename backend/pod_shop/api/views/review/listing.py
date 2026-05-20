# path: pod_shop/api/views/review/listing.py

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny

from pod_shop.api.serializers import ProductReviewSerializer
from pod_shop.models import Product, Review


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='product_code',
            type=OpenApiTypes.STR,
            description='Mã sản phẩm (code) để lấy danh sách đánh giá',
            required=False
        ),
        OpenApiParameter(
            name='product_slug',
            type=OpenApiTypes.STR,
            description='Slug sản phẩm để lấy danh sách đánh giá',
            required=False
        ),
        OpenApiParameter(
            name='rating',
            type=OpenApiTypes.INT,
            description='Lọc đánh giá theo mức độ đánh giá (1-5)',
            required=False,
            enum=[1, 2, 3, 4, 5]
        ),
        OpenApiParameter(
            name='ordering',
            type=OpenApiTypes.STR,
            description='Sắp xếp theo trường (created_at, -created_at, rating, -rating)',
            required=False,
            enum=['created_at', '-created_at', 'rating', '-rating']
        )
    ],
    responses={200: ProductReviewSerializer(many=True)},
    summary="Danh sách đánh giá sản phẩm",
    description="Trả về danh sách đánh giá của sản phẩm theo mã hoặc slug sản phẩm."
)
class ProductReviewListView(generics.ListAPIView):
    """
    API để lấy danh sách đánh giá sản phẩm theo mã sản phẩm
    """
    serializer_class = ProductReviewSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['rating']
    ordering_fields = ['-created_at', 'created_at', '-rating', 'rating']
    ordering = ['-created_at'] # Mặc định sắp xếp theo ngày tạo mới nhất
    permission_classes = [AllowAny]

    def get_queryset(self):
        product_code = self.request.query_params.get('product_code')
        product_slug = self.request.query_params.get('product_slug')

        if product_code:
            filter_kwargs = {'code': product_code}
        elif product_slug:
            filter_kwargs = {'slug': product_slug}
        else:
            raise NotFound("Missing product_code or product_slug.")

        try:
            product = Product.objects.get(**filter_kwargs)
        except Product.DoesNotExist:
            raise NotFound("Product not found.")

        return Review.objects.filter(product=product, status=True)
