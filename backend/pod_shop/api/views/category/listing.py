# path: pod_shop/api/views/category/listing.py

from django.db.models import Case, When, F, FloatField, OuterRef, Exists
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from pod_shop.api.serializers import CategoryListSerializer, ProductCategoryListSerializer, ProductSerializer
from pod_shop.models import Category, Product, ProductAttrItem
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
        return Category.objects.order_by('order')


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
            raise NotFound('Category not found')

        # Lấy danh sách sản phẩm thuộc danh mục
        p = Product.objects.filter(
            status='A',
            category=c
        ).order_by('-created_at')

        # Lọc theo brand
        brand_slug = request.GET.get('brand')
        if brand_slug:
            p = p.filter(brand__slug=brand_slug)

        # Lọc theo màu sắc
        color_value = request.GET.get('color')
        if color_value:
            p = p.filter(
                id__in=ProductAttrItem.objects.filter(
                    attr__name__iexact='Color',
                    value=color_value
                ).values_list('product_id', flat=True)
            )

        # Lọc theo kích thước
        size_color = request.GET.get('size')
        if size_color:
            p = p.filter(
                id__in=ProductAttrItem.objects.filter(
                    attr__name__iexact='Size',
                    value=size_color
                ).values_list('product_id', flat=True)
            )

        p = p.distinct()

        # Phân trang
        paginator = ItemsListPagination()
        page = paginator.paginate_queryset(p, request)
        serializer = ProductSerializer(page, many=True, context={'user': user, 'request': request})

        return paginator.get_paginated_response({
            'category': ProductCategoryListSerializer(c).data,
            'products': serializer.data
        })
    
