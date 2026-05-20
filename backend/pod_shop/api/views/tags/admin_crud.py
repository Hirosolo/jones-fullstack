"""
Admin Tag CRUD API views.
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

from pod_shop.models import Tag, Product


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
def admin_tag_list(request):
    """List all tags with active-product counts. Sort: most-used first."""
    # Count active products per tag via the through table.
    usage = {}
    for p in Product.objects.filter(status='A').prefetch_related('tags'):
        for t in p.tags.all():
            usage[t.id] = usage.get(t.id, 0) + 1

    tags = Tag.objects.all()
    items = []
    for t in tags:
        items.append({
            'id': t.id,
            'name': t.name,
            'slug': t.slug,
            'desc': t.desc or '',
            'numProducts': usage.get(t.id, 0),
        })

    # Auto-sort: most-used first, alphabetical tiebreak — same rule the
    # admin UI and public Popular-Tags block rely on.
    items.sort(key=lambda x: (-x['numProducts'], x['name'].lower()))

    return Response({
        'total': len(items),
        'items': items,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_required
def admin_tag_create(request):
    """Create a new tag."""
    data = request.data

    name = (data.get('name') or '').strip()
    if not name:
        return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

    if Tag.objects.filter(name__iexact=name).exists():
        return Response({'error': f'Tag "{name}" already exists'}, status=status.HTTP_400_BAD_REQUEST)

    tag = Tag(
        name=name,
        desc=data.get('desc', '') or '',
    )
    tag.save()

    return Response({
        'id': tag.id,
        'name': tag.name,
        'slug': tag.slug,
        'desc': tag.desc or '',
        'numProducts': 0,
        'message': f'Tag "{tag.name}" created successfully',
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_required
def admin_tag_update(request, pk):
    """Update an existing tag."""
    try:
        tag = Tag.objects.get(pk=pk)
    except Tag.DoesNotExist:
        return Response({'error': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data

    if data.get('name'):
        new_name = data['name'].strip()
        if Tag.objects.filter(name__iexact=new_name).exclude(pk=pk).exists():
            return Response({'error': f'Tag "{new_name}" already exists'}, status=status.HTTP_400_BAD_REQUEST)
        tag.name = new_name

    if 'desc' in data:
        tag.desc = data['desc'] or ''

    tag.save()

    return Response({
        'id': tag.id,
        'name': tag.name,
        'slug': tag.slug,
        'desc': tag.desc or '',
        'message': f'Tag "{tag.name}" updated successfully',
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_tag_delete(request, pk):
    """Delete a tag. The through-table rows are removed automatically by CASCADE."""
    try:
        tag = Tag.objects.get(pk=pk)
    except Tag.DoesNotExist:
        return Response({'error': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)

    name = tag.name
    tag.delete()

    return Response({
        'message': f'Tag "{name}" deleted successfully',
    })
