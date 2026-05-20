# path: pod_shop/api/views/brand/listing.py

from django.db.models import Case, When, F, FloatField, OuterRef, Exists
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from pod_shop.api.serializers import BrandListSerializer, ProductBrandListSerializer, ProductSerializer
from pod_shop.models import Brand, Product, ProductAttrItem
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
        return Brand.objects.order_by('order')


@extend_schema(
    summary="Brand groups (taxonomy aggregated by league)",
    description="Public read-only endpoint trả về danh sách brands gom theo `league` "
                "(Sport, Rock Band, Music...). Header mega-menu và trang /b dùng dữ liệu này."
)
class BrandGroupsView(APIView):
    """
    Aggregate brands grouped by their `league` field.
    Brands without a league are bucketed under "Other".
    Group display order = min(brand.order) within the group; brand display
    order inside each group = (order asc, name asc).
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        groups = {}
        for b in Brand.objects.all().order_by('order', 'name'):
            league = (b.league or '').strip() or 'Other'
            groups.setdefault(league, []).append({
                'id': b.id,
                'name': b.name,
                'slug': b.slug,
                'url': f'/b/{b.slug}',
                'order': b.order,
            })

        result = []
        for idx, (league_name, brands) in enumerate(groups.items()):
            sorted_brands = sorted(brands, key=lambda x: (x['order'], x['name'].lower()))
            min_order = min((b['order'] for b in brands), default=idx + 1)
            result.append({
                'name': league_name,
                'order': min_order,
                'items': sorted_brands,
            })

        result.sort(key=lambda g: (g['order'], g['name'].lower()))
        # Re-assign sequential order so the FE can sort/anchor predictably.
        for i, g in enumerate(result, start=1):
            g['order'] = i

        return Response({'groups': result})


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
            raise NotFound('Brand not found')

        # Lấy danh sách sản phẩm thuộc thương hiệu
        p = Product.objects.filter(
            status='A',
            brand=b
        ).order_by('-created_at')

        # Lọc theo category
        category_slug = request.GET.get('category')
        if category_slug:
            p = p.filter(category__slug=category_slug)

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
            'brand': ProductBrandListSerializer(b).data,
            'products': serializer.data
        })
