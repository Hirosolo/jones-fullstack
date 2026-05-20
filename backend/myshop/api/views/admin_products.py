"""
Admin Product CRUD API views.
Secured by X-Admin-Key header or JWT Bearer token authentication.
Only staff/admin users can access these endpoints.
"""
import os
from functools import wraps

from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from myshop.models import Product, Category, Brand, Tag


def admin_api_key_or_token_required(view_func):
    """
    Decorator to check for either API key or JWT token authentication.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check JWT token first
        if hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
        
        # Fall back to API key check
        admin_key = request.headers.get('X-Admin-Key', '')
        expected_key = getattr(settings, 'ADMIN_API_KEY', None) or os.environ.get('ADMIN_API_KEY', '')
        if expected_key and admin_key == expected_key:
            return view_func(request, *args, **kwargs)
        
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
    return wrapper


def _image_url(product):
    """Resolve the public URL of the product image."""
    try:
        if hasattr(product, 'productimage_set') and product.productimage_set.exists():
            return product.productimage_set.first().image.url
    except Exception:
        pass
    return ''


def _serialize_product(p, detail=False):
    """Serialize a Product instance to a dictionary."""
    data = {
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'code': p.code,
        'descShort': p.desc_short or '',
        'priceOrigin': float(p.price_origin),
        'pricePromo': float(p.price_promo) if p.price_promo else None,
        'stock': p.stock,
        'isAvailable': p.is_available,
        'categoryId': p.category.id if p.category else None,
        'categoryName': p.category.name if p.category else '',
        'brandId': p.brand.id if p.brand else None,
        'brandName': p.brand.name if p.brand else '',
        'tagIds': list(p.tags.values_list('id', flat=True)),
        'tags': list(p.tags.values('id', 'name', 'slug')),
        'image': _image_url(p),
        'timesPurchased': p.times_purchased,
        'metaTitle': p.meta_title or '',
        'metaDesc': p.meta_desc or '',
        'createdAt': p.created_at.isoformat() if p.created_at else '',
        'updatedAt': p.updated_at.isoformat() if p.updated_at else '',
    }
    if detail:
        data['desc'] = p.desc or ''
        data['sellerNotes'] = p.seller_notes or ''
    return data


@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_or_token_required
def admin_product_list(request):
    """List products with search + filter."""
    search = request.query_params.get('search', '').strip()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    category_id = request.query_params.get('category_id')
    brand_id = request.query_params.get('brand_id')

    qs = Product.objects.select_related('category', 'brand').prefetch_related('tags')

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search) | Q(code__icontains=search))
    if category_id:
        try:
            qs = qs.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass
    if brand_id:
        try:
            qs = qs.filter(brand_id=int(brand_id))
        except (ValueError, TypeError):
            pass

    qs = qs.order_by('-updated_at')
    total = qs.count()
    start = (page - 1) * page_size
    products = qs[start:start + page_size]

    items = [_serialize_product(p) for p in products]

    return Response({
        'total': total,
        'page': page,
        'pageSize': page_size,
        'numPages': (total + page_size - 1) // page_size if page_size else 1,
        'items': items,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_or_token_required
def admin_product_options(request):
    """Categories, brands + tags for the product form dropdowns."""
    categories = list(Category.objects.order_by('name').values('id', 'name', 'slug'))
    brands = list(Brand.objects.order_by('name').values('id', 'name', 'slug'))
    tags = list(Tag.objects.order_by('name').values('id', 'name', 'slug'))
    return Response({'categories': categories, 'brands': brands, 'tags': tags})


@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_or_token_required
def admin_product_detail(request, pk):
    try:
        p = Product.objects.select_related('category', 'brand').prefetch_related('tags').get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'product': _serialize_product(p, detail=True)})


def _apply_tags(product, data):
    """Apply tags to a product from request data."""
    if hasattr(data, 'getlist'):
        raw = data.getlist('tag_ids')
    else:
        raw = data.get('tag_ids')
    if raw is None:
        return False  # field absent → don't touch
    if isinstance(raw, str):
        raw = [t.strip() for t in raw.split(',') if t.strip()]
    ids = []
    for t in raw:
        try:
            ids.append(int(t))
        except (TypeError, ValueError):
            continue
    product.tags.set(Tag.objects.filter(id__in=ids))
    return True


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_or_token_required
def admin_product_create(request):
    """Create a new product."""
    data = request.data

    name = (data.get('name') or '').strip()
    if not name:
        return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

    desc = (data.get('desc') or '').strip()
    if not desc:
        return Response({'error': 'desc is required'}, status=status.HTTP_400_BAD_REQUEST)

    desc_short = (data.get('desc_short') or '').strip()
    if not desc_short:
        return Response({'error': 'desc_short is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        price_origin = float(data.get('price_origin', 0))
    except (ValueError, TypeError):
        return Response({'error': 'price_origin must be a number'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        stock = int(data.get('stock', 0))
    except (ValueError, TypeError):
        return Response({'error': 'stock must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    category = None
    category_id = data.get('category_id')
    if category_id:
        try:
            category = Category.objects.get(id=int(category_id))
        except (Category.DoesNotExist, ValueError):
            return Response({'error': 'Category not found'}, status=status.HTTP_400_BAD_REQUEST)

    brand = None
    brand_id = data.get('brand_id')
    if brand_id:
        try:
            brand = Brand.objects.get(id=int(brand_id))
        except (Brand.DoesNotExist, ValueError):
            return Response({'error': 'Brand not found'}, status=status.HTTP_400_BAD_REQUEST)

    price_promo = None
    price_promo_raw = data.get('price_promo')
    if price_promo_raw:
        try:
            price_promo = float(price_promo_raw)
        except (ValueError, TypeError):
            pass

    product = Product(
        name=name,
        desc=desc,
        desc_short=desc_short,
        price_origin=price_origin,
        price_promo=price_promo,
        stock=stock,
        is_available=str(data.get('is_available', 'true')).lower() in ('true', '1'),
        seller_notes=(data.get('seller_notes') or '').strip(),
        meta_title=(data.get('meta_title') or '')[:60],
        meta_desc=(data.get('meta_desc') or '')[:145],
        admin_notes=(data.get('admin_notes') or '').strip(),
        category=category,
        brand=brand,
    )

    product.save()
    _apply_tags(product, data)

    return Response({
        'message': 'Product created',
        'product': _serialize_product(product, detail=True),
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_or_token_required
def admin_product_update(request, pk):
    """Update an existing product."""
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data

    if data.get('name'):
        product.name = data['name'].strip()

    if 'desc' in data:
        product.desc = (data.get('desc') or '').strip()
    if 'desc_short' in data:
        product.desc_short = (data.get('desc_short') or '').strip()
    if 'seller_notes' in data:
        product.seller_notes = (data.get('seller_notes') or '').strip()
    if 'admin_notes' in data:
        product.admin_notes = (data.get('admin_notes') or '').strip()

    if 'price_origin' in data:
        try:
            product.price_origin = float(data['price_origin'])
        except (ValueError, TypeError):
            return Response({'error': 'price_origin must be a number'}, status=status.HTTP_400_BAD_REQUEST)

    if 'price_promo' in data:
        price_promo_raw = data.get('price_promo')
        if price_promo_raw:
            try:
                product.price_promo = float(price_promo_raw)
            except (ValueError, TypeError):
                return Response({'error': 'price_promo must be a number'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            product.price_promo = None

    if 'stock' in data:
        try:
            product.stock = int(data['stock'])
        except (ValueError, TypeError):
            return Response({'error': 'stock must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    if 'is_available' in data:
        product.is_available = str(data['is_available']).lower() in ('true', '1')

    if 'meta_title' in data:
        product.meta_title = (data.get('meta_title') or '')[:60]
    if 'meta_desc' in data:
        product.meta_desc = (data.get('meta_desc') or '')[:145]

    if 'category_id' in data:
        cid = data.get('category_id')
        if cid:
            try:
                product.category = Category.objects.get(id=int(cid))
            except (Category.DoesNotExist, ValueError):
                return Response({'error': 'Category not found'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            product.category = None

    if 'brand_id' in data:
        bid = data.get('brand_id')
        if bid:
            try:
                product.brand = Brand.objects.get(id=int(bid))
            except (Brand.DoesNotExist, ValueError):
                return Response({'error': 'Brand not found'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            product.brand = None

    product.save()
    _apply_tags(product, data)

    return Response({
        'message': 'Product updated',
        'product': _serialize_product(product, detail=True),
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])
@admin_api_key_or_token_required
def admin_product_delete(request, pk):
    """Delete a product."""
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    name = product.name
    product.delete()
    return Response({'message': f'Product "{name}" deleted'})
