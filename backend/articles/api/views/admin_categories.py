"""
Admin Article Category CRUD API views.
"""
import os
from functools import wraps

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from articles.models import ArticleCategory, Article


def admin_api_key_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key', '')
        expected_key = getattr(settings, 'ADMIN_API_KEY', None) or os.environ.get('ADMIN_API_KEY', '')
        if not expected_key or admin_key != expected_key:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        return view_func(request, *args, **kwargs)
    return wrapper


def _serialize(cat):
    num_articles = Article.objects.filter(category=cat, status='published').count()
    return {
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'desc': cat.desc or '',
        'order': cat.order,
        'metaTitle': cat.meta_title or '',
        'metaDesc': cat.meta_desc or '',
        'numArticles': num_articles,
    }


@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_article_category_list(request):
    categories = ArticleCategory.objects.all().order_by('order', 'name')
    return Response({'items': [_serialize(c) for c in categories]})


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
@admin_api_key_required
def admin_article_category_create(request):
    data = request.data
    name = (data.get('name') or '').strip()
    if not name:
        return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

    cat = ArticleCategory(
        name=name,
        desc=data.get('desc', '') or '',
        order=int(data.get('order', 0) or 0),
        meta_title=(data.get('metaTitle') or data.get('meta_title') or '')[:60],
        meta_desc=(data.get('metaDesc') or data.get('meta_desc') or '')[:145],
    )
    cat.save()
    return Response({'message': 'Category created', 'category': _serialize(cat)}, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
@admin_api_key_required
def admin_article_category_update(request, pk):
    try:
        cat = ArticleCategory.objects.get(pk=pk)
    except ArticleCategory.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data
    if data.get('name'):
        cat.name = data['name'].strip()
    if 'desc' in data:
        cat.desc = data.get('desc') or ''
    if 'order' in data:
        try:
            cat.order = int(data['order'] or 0)
        except (TypeError, ValueError):
            pass
    if 'metaTitle' in data or 'meta_title' in data:
        cat.meta_title = ((data.get('metaTitle') or data.get('meta_title') or '')[:60])
    if 'metaDesc' in data or 'meta_desc' in data:
        cat.meta_desc = ((data.get('metaDesc') or data.get('meta_desc') or '')[:145])

    cat.save()
    return Response({'message': 'Category updated', 'category': _serialize(cat)})


@api_view(['DELETE'])
@permission_classes([AllowAny])
@admin_api_key_required
def admin_article_category_delete(request, pk):
    try:
        cat = ArticleCategory.objects.get(pk=pk)
    except ArticleCategory.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    # Detach articles from this category (same behavior as the old Blob route).
    Article.objects.filter(category=cat).update(category=None)
    name = cat.name
    cat.delete()
    return Response({'message': f'Category "{name}" deleted'})
