# path: myshop/api/views/category/listing.py

from django.db.models import Case, When, F, FloatField, OuterRef, Exists
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from myshop.api.serializers import CategoryListSerializer, ProductCategoryListSerializer, ProductSerializer
from myshop.models import Category, Product, ProductVariant
from utils.api.common import ItemsListPagination


@extend_schema(
    summary="Danh sách danh mục sản phẩm",
    description="API trả về danh sách danh mục sản phẩm."
)
class CategoriesListView(ListAPIView):
    """
    Lấy danh sách danh mục sản phẩm
    """
    serializer_class = CategoryListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Category.objects.order_by('-order')


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            description='Slug của danh mục cần xem chi tiết',
            required=True
        ),
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            description='Số trang cần lấy (mặc định là 1)',
            required=False
        ),
        OpenApiParameter(
            name='brand',
            type=OpenApiTypes.STR,
            description='Slug brand sản phẩm để lọc',
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
    responses={200: ProductCategoryListSerializer},
    summary="Danh sách sản phẩm theo danh mục",
    description="API trả về danh sách sản phẩm thuộc danh mục dựa trên slug."
)
class CategoryProductsListView(APIView):
    """
    Danh sách sản phẩm theo danh mục
    """
    serializer_class = ProductCategoryListSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = request.user
        slug = request.GET.get('slug', '')
        c = get_object_or_404(Category, slug=slug)
        
        # Kiểm tra xem danh mục có tồn tại không
        if not c:
            raise NotFound('Không tìm thấy danh mục sản phẩm')

        # Lấy danh sách sản phẩm thuộc danh mục
        p = Product.objects.filter(
            is_available=True,
            category=c
        ).order_by('-created_at')

        # Lọc theo brand
        brand_slug = request.GET.get('brand')
        if brand_slug:
            p = p.filter(brand__slug=brand_slug)

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

        # Phân trang
        paginator = ItemsListPagination()
        page = paginator.paginate_queryset(p, request)
        serializer = ProductSerializer(page, many=True, context={'user': user})
        return paginator.get_paginated_response({
            'category': ProductCategoryListSerializer(c).data,
            'products': serializer.data
        })
    
