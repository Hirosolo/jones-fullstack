"""
Admin Article CRUD API views.
Secured by X-Admin-Key header or JWT Bearer token authentication.
Only staff/admin users can access these endpoints.
"""
import os
from functools import wraps

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from articles.models import Article, ArticleCategory, ArticleTag


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


def _image_url(article):
    """Resolve the public URL of the featured image (pasted URL > uploaded file)."""
    if article.featured_image_url:
        return article.featured_image_url
    try:
        return article.featured_image.url if article.featured_image else ''
    except Exception:
        return ''


def _serialize_article(a, detail=False):
    data = {
        'id': a.id,
        'title': a.title,
        'slug': a.slug,
        'code': a.code,
        'excerpt': a.excerpt or '',
        'featuredImage': _image_url(a),
        'categoryId': a.category.id if a.category else None,
        'categorySlug': a.category.slug if a.category else '',
        'categoryName': a.category.name if a.category else '',
        'tagIds': list(a.tags.values_list('id', flat=True)),
        'tagSlugs': list(a.tags.values_list('slug', flat=True)),
        'tags': list(a.tags.values('id', 'name', 'slug')),
        'authorName': a.author_name or '',
        'status': a.status,
        'featured': a.featured,
        'publishedAt': a.published_at.isoformat() if a.published_at else '',
        'createdAt': a.created_at.isoformat() if a.created_at else '',
        'updatedAt': a.updated_at.isoformat() if a.updated_at else '',
        'metaTitle': a.meta_title or '',
        'metaDesc': a.meta_desc or '',
    }
    if detail:
        data['content'] = a.content or ''
    return data


@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_or_token_required
def admin_article_list(request):
    """List articles with search + status filter."""
    search = request.query_params.get('search', '').strip()
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    status_filter = request.query_params.get('status', '')

    qs = Article.objects.select_related('category').prefetch_related('tags')

    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(slug__icontains=search) | Q(code__icontains=search))
    if status_filter:
        qs = qs.filter(status=status_filter)

    qs = qs.order_by('-created_at')
    total = qs.count()
    start = (page - 1) * page_size
    articles = qs[start:start + page_size]

    items = [_serialize_article(a) for a in articles]

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
def admin_article_options(request):
    """Categories + tags for the article form dropdowns."""
    categories = list(ArticleCategory.objects.order_by('name').values('id', 'name', 'slug'))
    tags = list(ArticleTag.objects.order_by('name').values('id', 'name', 'slug'))
    return Response({'categories': categories, 'tags': tags})


@api_view(['GET'])
@permission_classes([AllowAny])
@admin_api_key_or_token_required
def admin_article_detail(request, pk):
    try:
        a = Article.objects.select_related('category').prefetch_related('tags').get(pk=pk)
    except Article.DoesNotExist:
        return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'article': _serialize_article(a, detail=True)})


def _apply_tags(article, data):
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
    article.tags.set(ArticleTag.objects.filter(id__in=ids))
    return True


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_or_token_required
def admin_article_create(request):
    data = request.data

    title = (data.get('title') or '').strip()
    if not title:
        return Response({'error': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)

    category = None
    category_id = data.get('category_id')
    if category_id:
        try:
            category = ArticleCategory.objects.get(id=int(category_id))
        except (ArticleCategory.DoesNotExist, ValueError):
            return Response({'error': 'Category not found'}, status=status.HTTP_400_BAD_REQUEST)

    status_val = data.get('status') or 'draft'
    if status_val not in ('draft', 'published'):
        status_val = 'draft'

    published_at = None
    if status_val == 'published':
        pub_raw = data.get('published_at') or ''
        if pub_raw:
            try:
                published_at = timezone.datetime.fromisoformat(pub_raw.replace('Z', '+00:00'))
            except ValueError:
                published_at = timezone.now()
        else:
            published_at = timezone.now()

    article = Article(
        title=title,
        excerpt=data.get('excerpt', '') or '',
        content=data.get('content', '') or '',
        featured_image_url=(data.get('featured_image_url') or '').strip(),
        author_name=(data.get('author_name') or '').strip(),
        status=status_val,
        featured=str(data.get('featured', 'false')).lower() in ('true', '1'),
        published_at=published_at,
        meta_title=(data.get('meta_title') or '')[:60],
        meta_desc=(data.get('meta_desc') or '')[:145],
        category=category,
    )

    image = request.FILES.get('featured_image')
    if image:
        article.featured_image = image

    article.save()
    _apply_tags(article, data)

    return Response({
        'message': 'Article created',
        'article': _serialize_article(article, detail=True),
    }, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@admin_api_key_or_token_required
def admin_article_update(request, pk):
    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data

    if data.get('title'):
        article.title = data['title'].strip()

    if 'excerpt' in data:
        article.excerpt = data.get('excerpt') or ''
    if 'content' in data:
        article.content = data.get('content') or ''
    if 'author_name' in data:
        article.author_name = (data.get('author_name') or '').strip()
    if 'featured_image_url' in data:
        article.featured_image_url = (data.get('featured_image_url') or '').strip()
    if 'featured' in data:
        article.featured = str(data['featured']).lower() in ('true', '1')
    if 'meta_title' in data:
        article.meta_title = (data.get('meta_title') or '')[:60]
    if 'meta_desc' in data:
        article.meta_desc = (data.get('meta_desc') or '')[:145]

    if 'category_id' in data:
        cid = data.get('category_id')
        if cid:
            try:
                article.category = ArticleCategory.objects.get(id=int(cid))
            except (ArticleCategory.DoesNotExist, ValueError):
                return Response({'error': 'Category not found'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            article.category = None

    if 'status' in data:
        new_status = data['status']
        if new_status in ('draft', 'published'):
            was_draft = article.status == 'draft'
            article.status = new_status
            if new_status == 'published' and (was_draft or not article.published_at):
                pub_raw = data.get('published_at') or ''
                if pub_raw:
                    try:
                        article.published_at = timezone.datetime.fromisoformat(pub_raw.replace('Z', '+00:00'))
                    except ValueError:
                        article.published_at = timezone.now()
                else:
                    article.published_at = timezone.now()

    image = request.FILES.get('featured_image')
    if image:
        article.featured_image = image

    article.save()
    _apply_tags(article, data)

    return Response({
        'message': 'Article updated',
        'article': _serialize_article(article, detail=True),
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])
@admin_api_key_or_token_required
def admin_article_delete(request, pk):
    try:
        article = Article.objects.get(pk=pk)
    except Article.DoesNotExist:
        return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)

    title = article.title
    article.delete()
    return Response({'message': f'Article "{title}" deleted'})
