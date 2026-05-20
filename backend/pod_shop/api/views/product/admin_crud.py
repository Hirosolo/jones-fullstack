"""
Admin Product CRUD API views.
Secured by X-Admin-Key header authentication.
"""
import os
from functools import wraps

from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pod_shop.models import Product, Category, Brand, Tag, ProductImage, ProductSlugAlias


def admin_api_key_required(view_func):
    """Decorator to require X-Admin-Key header for admin API endpoints."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key', '')
        expected_key = getattr(settings, 'ADMIN_API_KEY', None) or os.environ.get('ADMIN_API_KEY', '')
        if not expected_key or admin_key != expected_key:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_product_list(request):
    """List products with search, pagination, and filtering."""
    search = request.query_params.get('search', '').strip()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    status_filter = request.query_params.get('status', '')

    qs = Product.objects.select_related('brand', 'category').prefetch_related('images').all()

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search) | Q(slug__icontains=search))
    if status_filter:
        qs = qs.filter(status=status_filter)

    qs = qs.order_by('-created_at')
    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size
    products = qs[start:end]

    items = []
    for p in products:
        image_rows = list(p.images.filter(removed=False).order_by('order'))
        image_urls = [img.get_url() for img in image_rows if img.get_url()]
        primary_image = image_urls[0] if image_urls else None

        tag_list = list(p.tags.all().values('id', 'name', 'slug')) if hasattr(p, 'tags') else []

        items.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'code': p.code,
            'price': str(p.price),
            'fakePrice': str(p.fake_price) if p.fake_price else None,
            'status': p.status,
            'statusDisplay': p.get_status_display(),
            'category': {'id': p.category.id, 'name': p.category.name, 'slug': p.category.slug} if p.category else None,
            'brand': {'id': p.brand.id, 'name': p.brand.name, 'slug': p.brand.slug} if p.brand else None,
            'categorySlug': p.category.slug if p.category else '',
            'brandSlug': p.brand.slug if p.brand else '',
            'tagIds': [t['id'] for t in tag_list],
            'tagSlugs': [t['slug'] for t in tag_list],
            'tags': tag_list,
            'isFeatured': p.is_featured,
            'bestSeller': p.best_seller,
            'image': primary_image,
            'images': image_urls,
            'descShort': getattr(p, 'desc_short', '') or '',
            'desc': getattr(p, 'desc', '') or '',
            'metaTitle': getattr(p, 'meta_title', '') or '',
            'metaDesc': getattr(p, 'meta_desc', '') or '',
            'createdAt': p.created_at.isoformat() if p.created_at else None,
        })

    return Response({
        'total': total,
        'page': page,
        'pageSize': page_size,
        'numPages': (total + page_size - 1) // page_size,
        'items': items,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_product_options(request):
    """Get categories, brands, tags for product form dropdowns."""
    categories = list(Category.objects.all().order_by('name').values('id', 'name', 'slug'))
    brands = list(Brand.objects.all().order_by('name').values('id', 'name', 'slug', 'league'))
    tags = list(Tag.objects.all().order_by('name').values('id', 'name', 'slug'))
    return Response({
        'categories': categories,
        'brands': brands,
        'tags': tags,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_required
def admin_product_create(request):
    """Create a new product."""
    data = request.data

    # Validate required fields
    required = ['name', 'price', 'category_id', 'brand_id']
    for field in required:
        if not data.get(field):
            return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        category = Category.objects.get(id=data['category_id'])
        brand = Brand.objects.get(id=data['brand_id'])
    except (Category.DoesNotExist, Brand.DoesNotExist) as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    product = Product(
        name=data['name'],
        price=data['price'],
        fake_price=data.get('fake_price') or None,
        category=category,
        brand=brand,
        desc=data.get('desc', ''),
        desc_short=data.get('desc_short', ''),
        status=data.get('status', 'D'),
        is_featured=str(data.get('is_featured', 'false')).lower() in ('true', '1'),
        best_seller=str(data.get('best_seller', 'false')).lower() in ('true', '1'),
        meta_title=data.get('meta_title', ''),
        meta_desc=data.get('meta_desc', ''),
    )
    # Optional manual slug. Empty → AutoSlugField populates from name.
    # Non-empty → AutoSlugField uses it (appending -N if collision).
    slug_input = (data.get('slug') or '').strip()
    if slug_input:
        product.slug = slug_input
    product.save()

    # If a stale alias targets the slug we just minted (e.g. another
    # product was once named this), clear it so the alias never wins
    # against a current primary slug in the FE redirect map.
    ProductSlugAlias.objects.filter(old_slug=product.slug).delete()

    # Handle tags
    tag_ids = data.getlist('tag_ids') if hasattr(data, 'getlist') else data.get('tag_ids', [])
    if isinstance(tag_ids, str):
        tag_ids = [t.strip() for t in tag_ids.split(',') if t.strip()]
    if tag_ids:
        product.tags.set(Tag.objects.filter(id__in=tag_ids))

    # Handle external image URLs (preferred for admin URL-paste workflow)
    image_urls = data.getlist('image_urls') if hasattr(data, 'getlist') else data.get('image_urls', [])
    if isinstance(image_urls, str):
        image_urls = [u.strip() for u in image_urls.split(',') if u.strip()]
    image_urls = [u for u in image_urls if u]
    for idx, url in enumerate(image_urls):
        ProductImage.objects.create(product=product, image_url=url, order=idx)

    # Also accept direct file upload (for legacy multipart usage)
    image = request.FILES.get('image')
    if image:
        ProductImage.objects.create(product=product, image=image, order=len(image_urls))

    return Response({
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'code': product.code,
        'message': 'Product created successfully',
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_required
def admin_product_update(request, pk):
    """Update an existing product."""
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data

    if data.get('name'):
        product.name = data['name']
    if data.get('price'):
        product.price = data['price']
    if 'fake_price' in data:
        product.fake_price = data['fake_price'] or None
    if data.get('category_id'):
        try:
            product.category = Category.objects.get(id=data['category_id'])
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=status.HTTP_400_BAD_REQUEST)
    if data.get('brand_id'):
        try:
            product.brand = Brand.objects.get(id=data['brand_id'])
        except Brand.DoesNotExist:
            return Response({'error': 'Brand not found'}, status=status.HTTP_400_BAD_REQUEST)
    if 'desc' in data:
        product.desc = data['desc']
    if 'desc_short' in data:
        product.desc_short = data['desc_short']
    if 'status' in data:
        product.status = data['status']
    if 'is_featured' in data:
        product.is_featured = str(data['is_featured']).lower() in ('true', '1')
    if 'best_seller' in data:
        product.best_seller = str(data['best_seller']).lower() in ('true', '1')
    if 'meta_title' in data:
        product.meta_title = data['meta_title']
    if 'meta_desc' in data:
        product.meta_desc = data['meta_desc']

    # Manual slug edit. Field present + non-empty + different → reassign.
    # AutoSlugField (editable=True) honors explicit assignment, with
    # uniqueness collision auto-suffix if needed. The prior slug is
    # captured as a ProductSlugAlias so /p/<old>/ keeps 301-redirecting
    # via the FE middleware — without this, renaming a product slug would
    # 404 every URL Google had previously indexed for it.
    slug_changed = False
    previous_slug = product.slug
    if 'slug' in data:
        new_slug = (data.get('slug') or '').strip()
        if new_slug and new_slug != previous_slug:
            product.slug = new_slug
            slug_changed = True

    product.save()

    if slug_changed:
        # Capture the prior slug as a redirect source. update_or_create
        # handles the rare case where this slug was already aliased to
        # this same product (re-entering an old name) — we want the alias
        # to remain pointing here.
        ProductSlugAlias.objects.update_or_create(
            old_slug=previous_slug,
            defaults={'product': product},
        )
        # Drop any alias that conflicts with the brand-new primary slug
        # (could happen if this slug was the historical name of another
        # product and got cleaned up by AutoSlugField uniqueness).
        ProductSlugAlias.objects.filter(old_slug=product.slug).delete()

    # Handle tags
    tag_ids = data.getlist('tag_ids') if hasattr(data, 'getlist') else data.get('tag_ids')
    if tag_ids is not None:
        if isinstance(tag_ids, str):
            tag_ids = [t.strip() for t in tag_ids.split(',') if t.strip()]
        product.tags.set(Tag.objects.filter(id__in=tag_ids))

    # Handle external image URLs — if the field is present (even empty),
    # replace the product's image list to match exactly what admin submitted.
    if hasattr(data, 'getlist'):
        raw_image_urls = data.getlist('image_urls')
        has_image_urls_field = 'image_urls' in data
    else:
        raw_image_urls = data.get('image_urls')
        has_image_urls_field = raw_image_urls is not None
        if raw_image_urls is None:
            raw_image_urls = []

    if has_image_urls_field:
        if isinstance(raw_image_urls, str):
            raw_image_urls = [u.strip() for u in raw_image_urls.split(',') if u.strip()]
        cleaned = [u for u in raw_image_urls if u]
        # Replace existing image set
        product.images.all().delete()
        for idx, url in enumerate(cleaned):
            ProductImage.objects.create(product=product, image_url=url, order=idx)

    # Also accept direct file upload (legacy)
    image = request.FILES.get('image')
    if image:
        ProductImage.objects.create(product=product, image=image, order=product.images.count())

    return Response({
        'id': product.id,
        'name': product.name,
        'slug': product.slug,
        'message': 'Product updated successfully',
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_product_delete(request, pk):
    """Delete a product."""
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    name = product.name
    product.delete()

    return Response({
        'message': f'Product "{name}" deleted successfully',
    })
