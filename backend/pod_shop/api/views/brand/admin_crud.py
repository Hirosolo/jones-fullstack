"""
Admin Brand CRUD API views.
Secured by X-Admin-Key header authentication.
"""
import os
from functools import wraps

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pod_shop.models import Brand, Product


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
def admin_brand_list(request):
    """List all brands with product counts."""
    brands = Brand.objects.all().order_by('order', 'name')

    items = []
    for b in brands:
        num_products = Product.objects.filter(brand=b, status='A').count()

        items.append({
            'id': b.id,
            'name': b.name,
            'slug': b.slug,
            'logo': b.get_logo_url() or None,
            'order': b.order,
            'league': b.league or '',
            'numProducts': num_products,
        })

    return Response({
        'total': len(items),
        'items': items,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_required
def admin_brand_create(request):
    """Create a new brand."""
    data = request.data

    name = data.get('name', '').strip()
    if not name:
        return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

    if Brand.objects.filter(name__iexact=name).exists():
        return Response({'error': f'Brand "{name}" already exists'}, status=status.HTTP_400_BAD_REQUEST)

    brand = Brand(
        name=name,
        desc=data.get('desc', ''),
        order=int(data.get('order', 1)),
        league=data.get('league', '') or '',
        logo_url=(data.get('logo_url') or '').strip(),
    )

    # Handle logo upload (preferred: logo_url string; fallback: file upload)
    logo = request.FILES.get('logo')
    if logo:
        brand.logo = logo

    brand.save()

    return Response({
        'id': brand.id,
        'name': brand.name,
        'slug': brand.slug,
        'message': f'Brand "{brand.name}" created successfully',
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_required
def admin_brand_update(request, pk):
    """Update an existing brand."""
    try:
        brand = Brand.objects.get(pk=pk)
    except Brand.DoesNotExist:
        return Response({'error': 'Brand not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data

    if data.get('name'):
        new_name = data['name'].strip()
        # Check uniqueness (exclude current brand)
        if Brand.objects.filter(name__iexact=new_name).exclude(pk=pk).exists():
            return Response({'error': f'Brand "{new_name}" already exists'}, status=status.HTTP_400_BAD_REQUEST)
        brand.name = new_name

    if 'desc' in data:
        brand.desc = data['desc']

    if 'order' in data:
        brand.order = int(data['order'])

    if 'league' in data:
        brand.league = data['league'] or ''

    if 'logo_url' in data:
        brand.logo_url = (data['logo_url'] or '').strip()

    # Handle logo upload (files override URL)
    logo = request.FILES.get('logo')
    if logo:
        brand.logo = logo

    brand.save()

    return Response({
        'id': brand.id,
        'name': brand.name,
        'slug': brand.slug,
        'message': f'Brand "{brand.name}" updated successfully',
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_brand_delete(request, pk):
    """Delete a brand. Prevents deletion if products are linked."""
    try:
        brand = Brand.objects.get(pk=pk)
    except Brand.DoesNotExist:
        return Response({'error': 'Brand not found'}, status=status.HTTP_404_NOT_FOUND)

    # Check if any products use this brand
    product_count = Product.objects.filter(brand=brand).count()
    if product_count > 0:
        return Response({
            'error': f'Cannot delete "{brand.name}" — {product_count} product(s) still use this brand. '
                     f'Reassign or delete those products first.',
        }, status=status.HTTP_400_BAD_REQUEST)

    name = brand.name
    brand.delete()

    return Response({
        'message': f'Brand "{name}" deleted successfully',
    })
