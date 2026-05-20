# path: pod_shop/api/views/tags/listing.py

from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from pod_shop.api.serializers import TagListSerializer, ProductTagListSerializer, ProductSerializer
from pod_shop.models import Tag, Product, ProductAttrItem
from utils.api.common import ItemsListPagination


@extend_schema(
    summary="Danh sách thẻ sản phẩm",
    description="API trả về danh sách thẻ sản phẩm."
)
class TagsListView(ListAPIView):
    """
    Lấy danh sách thẻ sản phẩm
    """
    serializer_class = TagListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Tag.objects.all()


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            description='Slug của thẻ cần xem chi tiết',
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
    ],
    responses={200: ProductTagListSerializer},
    summary="Danh sách sản phẩm theo thẻ",
    description="API trả về danh sách sản phẩm thuộc thẻ dựa trên slug."
)
class TagProductsListView(APIView):
    """
    Danh sách sản phẩm theo thẻ
    """
    serializer_class = ProductTagListSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = request.user
        slug = request.GET.get('slug', '')
        t = get_object_or_404(Tag, slug=slug)

        # Kiểm tra xem thẻ có tồn tại không
        if not t:
            raise NotFound('Không tìm thấy thẻ sản phẩm')

        # Lấy danh sách sản phẩm thuộc thẻ
        p = Product.objects.filter(
            status='A',
            tags=t
        ).order_by('-created_at')

        # Lọc theo category
        category_slug = request.GET.get('category')
        if category_slug:
            p = p.filter(category__slug=category_slug)

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

        # Phân trang danh sách sản phẩm
        paginator = ItemsListPagination()
        page = paginator.paginate_queryset(p, request)
        serializer = ProductSerializer(page, many=True, context={'user': user, 'request': request})
        return paginator.get_paginated_response({
            'tags': ProductTagListSerializer(t).data,
            'products': serializer.data
        })

