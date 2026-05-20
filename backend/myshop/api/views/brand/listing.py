# path: myshop/api/views/brand/listing.py

from django.db.models import Case, When, F, FloatField, OuterRef, Exists
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from myshop.api.serializers import BrandListSerializer, ProductBrandListSerializer, ProductSerializer
from myshop.models import Brand, Product, ProductVariant
from utils.api.common import ItemsListPagination


@extend_schema(
    summary="Danh sách thương hiệu sản phẩm",
    description="API trả về danh sách thương hiệu sản phẩm."
)
class BrandsListView(ListAPIView):
    """
    Lấy danh sách thương hiệu sản phẩm
    """
    serializer_class = BrandListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Brand.objects.order_by('-order')


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            description='Slug của thương hiệu cần xem chi tiết',
            required=True
        ),
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            description='Số trang cần lấy (mặc định là 1)',
            required=False
        ),
        OpenApiParameter(
            name='category',
            type=OpenApiTypes.STR,
            description='Slug danh mục sản phẩm để lọc',
            required=False
        ),
        OpenApiParameter(
            name='color',
            type=OpenApiTypes.STR,
            description='Value màu sắc để lọc',
            required=False
        ),
        OpenApiParameter(
            name='size',
            type=OpenApiTypes.STR,
            description='Value kích thước để lọc',
            required=False
        ),
        OpenApiParameter(
            name='minPrice',
            type=OpenApiTypes.FLOAT,
            description='Giá tối thiểu để lọc',
            required=False
        ),
        OpenApiParameter(
            name='maxPrice',
            type=OpenApiTypes.FLOAT,
            description='Giá tối đa để lọc',
            required=False
        ),
    ],
    responses={200: ProductBrandListSerializer},
    summary="Danh sách sản phẩm theo thương hiệu",
    description="API trả về danh sách sản phẩm thuộc thương hiệu dựa trên slug."
)
class BrandProductsListView(APIView):
    """
    Danh sách sản phẩm theo thương hiệu
    """
    serializer_class = ProductBrandListSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = request.user
        slug = request.GET.get('slug', '')
        b = get_object_or_404(Brand, slug=slug)

        # Kiểm tra xem thương hiệu có tồn tại không
        if not b:
            raise NotFound('Không tìm thấy thương hiệu sản phẩm')

        # Lấy danh sách sản phẩm thuộc thương hiệu
        p = Product.objects.filter(
            is_available=True,
            brand=b
        ).order_by('-created_at')

        # Lọc theo category
        category_slug = request.GET.get('category')
        if category_slug:
            p = p.filter(category__slug=category_slug)

        # Lọc theo màu sắc
        color_value = request.GET.get('color')
        if color_value:
            p = p.filter(variants_product_set__color__value=color_value)

        # Lọc theo kích thước
        size_color = request.GET.get('size')
        if size_color:
            p = p.filter(variants_product_set__size__value=size_color)

        # Lọc theo khoảng giá
        price_min = request.GET.get('minPrice')
        price_max = request.GET.get('maxPrice')

        if price_min or price_max:
            # Tạo subquery tính giá hiệu lực của từng variant
            variant_qs = ProductVariant.objects.filter(
                product=OuterRef('pk')
            ).annotate(
                effective_price=Case(
                    When(price_promo__isnull=False, then=F('price_promo')),
                    default=F('price_origin'),
                    output_field=FloatField()
                )
            )

            if price_min:
                variant_qs = variant_qs.filter(effective_price__gte=float(price_min))

            if price_max:
                variant_qs = variant_qs.filter(effective_price__lte=float(price_max))

            # Giữ lại sản phẩm có ít nhất 1 biến thể thỏa mãn giá
            p = p.filter(
                Exists(variant_qs)
            )

        p = p.distinct()

        # Phân trang danh sách sản phẩm
        paginator = ItemsListPagination()
        page = paginator.paginate_queryset(p, request)
        serializer = ProductSerializer(page, many=True, context={'user': user})
        return paginator.get_paginated_response({
            'brand': ProductBrandListSerializer(b).data,
            'products': serializer.data
        })
