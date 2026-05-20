# path: pod_shop/api/views/product/listing.py

from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pod_shop.api.serializers import ProductSerializer
from pod_shop.models import Product


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
    from django.core.cache import cache
    
    # Smart caching - try cache first
    cache_key = 'featured_products_api'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return Response(cached_data)
    
    user = request.user
    # Optimized query with select_related and prefetch_related
    qs = Product.objects.filter(
        status='A', 
        is_featured=True
    ).select_related(
        'category', 
        'brand'
    ).prefetch_related(
        'tags',
        'images'
    ).order_by('-created_at')[:12]
    
    data = ProductSerializer(qs, many=True, context={'user': user, 'request': request}).data
    
    # Only cache if we have data (prevent caching empty responses)
    if data:
        cache.set(cache_key, data, 60 * 10)  # Cache for 10 minutes
    
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
    from django.core.cache import cache
    
    # Smart caching - try cache first
    cache_key = 'bestseller_products_api'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return Response(cached_data)
    
    user = request.user
    # Optimized query with select_related and prefetch_related
    qs = Product.objects.filter(
        status='A', 
        best_seller=True
    ).select_related(
        'category', 
        'brand'
    ).prefetch_related(
        'tags',
        'images'
    ).order_by('-times_purchased')[:12]
    
    data = ProductSerializer(qs, many=True, context={'user': user, 'request': request}).data
    
    # Only cache if we have data (prevent caching empty responses)
    if data:
        cache.set(cache_key, data, 60 * 10)  # Cache for 10 minutes
    
    return Response(data)


@extend_schema(
    responses={200: ProductSerializer(many=True)},
    summary="Danh sách sản phẩm mới nhất",
    description="Trả về danh sách 5 sản phẩm mới nhất dựa trên ngày tạo."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def latest_products_view(request):
    """
    API trả về danh sách 5 sản phẩm mới nhất
    """
    user = request.user
    # Optimized query with select_related and prefetch_related
    qs = Product.objects.filter(
        status='A'
    ).select_related(
        'category', 
        'brand'
    ).prefetch_related(
        'tags',
        'images'
    ).order_by('-created_at')[:5]
    
    data = ProductSerializer(qs, many=True, context={'user': user, 'request': request}).data
    
    return Response(data)


@extend_schema(
    responses={200: ProductSerializer(many=True)},
    summary="Best sellers this week (rotates weekly)",
    description=(
        "Top 8 sản phẩm theo score = review_count × avg_rating, từ pool top 24, "
        "shuffle deterministic theo ISO week → cùng tuần ra cùng kết quả, "
        "tuần mới rotate. Cache 24h."
    ),
)
@api_view(['GET'])
@permission_classes([AllowAny])
def weekly_bestsellers_view(request):
    """Top weekly bestsellers — rotates each ISO week using a deterministic seed."""
    import random
    from datetime import date

    from django.core.cache import cache
    from django.db.models import Avg, Count, F, FloatField
    from django.db.models.functions import Coalesce

    iso_year, iso_week, _ = date.today().isocalendar()
    cache_key = f'weekly_bestsellers_api:y{iso_year}:w{iso_week}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    pool_size = 30
    take = 10

    qs = (
        Product.objects.filter(status='A')
        .select_related('category', 'brand')
        .prefetch_related('tags', 'images')
        .annotate(
            r_count=Count(
                'product_review_set',
                filter=Q(product_review_set__status=True),
                distinct=True,
            ),
            r_avg=Coalesce(
                Avg(
                    'product_review_set__rating',
                    filter=Q(product_review_set__status=True),
                ),
                0.0,
                output_field=FloatField(),
            ),
        )
        .annotate(score=F('r_count') * F('r_avg'))
        .order_by('-score', '-times_purchased', '-created_at')
    )
    pool = list(qs[:pool_size])

    rng = random.Random(f'{iso_year}-{iso_week}')
    rng.shuffle(pool)
    selected = pool[:take]

    data = ProductSerializer(
        selected, many=True, context={'user': request.user, 'request': request}
    ).data

    if data:
        cache.set(cache_key, data, 60 * 60 * 24)

    return Response(data)


@extend_schema(
    responses={200: ProductSerializer(many=True)},
    summary="Tìm kiếm sản phẩm",
    description="Trả về danh sách sản phẩm khớp với query q (theo name, slug, hoặc desc_short)."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def search_products_view(request):
    """Full-text-ish search across active products for the header search bar."""
    q = (request.query_params.get('q', '') or '').strip()
    if not q:
        return Response({'items': [], 'total': 0, 'current': 1, 'numPages': 1})

    try:
        page = max(int(request.query_params.get('page', 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = max(int(request.query_params.get('page_size', 10)), 1)
    except ValueError:
        page_size = 10

    qs = Product.objects.filter(status='A').filter(
        Q(name__icontains=q) | Q(slug__icontains=q) | Q(desc_short__icontains=q)
    ).select_related('category', 'brand').prefetch_related('tags', 'images').order_by('-created_at')

    total = qs.count()
    num_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    paged = qs[start:start + page_size]
    items = ProductSerializer(paged, many=True, context={'user': request.user, 'request': request}).data
    return Response({'items': items, 'total': total, 'current': page, 'numPages': num_pages})


@extend_schema(
    summary="Slug + updatedAt + images của TẤT CẢ sản phẩm active (cho sitemap.xml + image sitemap)",
    description=(
        "Endpoint lightweight: slug, updated_at và danh sách image paths "
        "(theo `order`) cho sản phẩm status='A'. Cache 30 phút. Dùng để "
        "build product-sitemap.xml + emit `<image:image>` blocks giúp "
        "Google index đúng tất cả ảnh thuộc URL product."
    ),
)
@api_view(['GET'])
@permission_classes([AllowAny])
def sitemap_products_view(request):
    """All active product slugs + images for sitemap generation."""
    from django.core.cache import cache

    try:
        page = max(int(request.query_params.get('page', 1)), 1)
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = min(max(int(request.query_params.get('page_size', 500)), 1), 1000)
    except (ValueError, TypeError):
        page_size = 500

    # Bumped cache key (v2) when image list was added — old cache entries
    # without `images` would silently break the FE sitemap.
    cache_key = f'sitemap_products_api_v2:p{page}:s{page_size}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    qs = (
        Product.objects.filter(status='A')
        .prefetch_related('images')
        .order_by('-updated_at')
    )
    total = qs.count()
    num_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    products = qs[start:start + page_size]

    items = []
    for p in products:
        imgs = []
        for img in p.images.filter(removed=False).order_by('order'):
            url = img.image_url or (str(img.image) if img.image else '')
            if url:
                imgs.append(url)
        items.append({
            'slug': p.slug,
            'updatedAt': p.updated_at.isoformat() if p.updated_at else None,
            'images': imgs,
        })

    data = {
        'items': items,
        'total': total,
        'current': page,
        'numPages': num_pages,
    }
    cache.set(cache_key, data, 60 * 30)
    return Response(data)
