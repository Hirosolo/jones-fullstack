
# path: articles/api/serializers.py

from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.template.defaultfilters import truncatechars
from django.utils.html import strip_tags
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from bs4 import BeautifulSoup

from articles.models import (ArticleCategory, ArticleTag, Article)
from utils.api.common import OpenGraphSerializer
from utils.common import safe_static


def _image_field_url(image_field):
    if not image_field or not getattr(image_field, 'name', ''):
        return ''
    try:
        return urljoin(settings.MEDIA_URL, image_field.url)
    except Exception:
        return ''


def _first_content_image(obj):
    for content in (getattr(obj, 'content_safe', ''), getattr(obj, 'content', '')):
        if not content:
            continue

        try:
            image = BeautifulSoup(content, 'html.parser').find('img')
        except Exception:
            continue

        src = image.get('src') if image else ''
        if src:
            return src.strip()
    return ''


def _article_featured_image_url(obj):
    return (
        _image_field_url(obj.featured_image)
        or (obj.featured_image_url or '').strip()
        or _image_field_url(obj.meta_image)
        or _first_content_image(obj)
        or ''
    )


class ArticleCategorySerializer(serializers.ModelSerializer):
    """
    Serializer cho model ArticleCategory
    """
    open_graph = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    full_url = SerializerMethodField()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj):
        """
        Lấy dữ liệu Open Graph cho danh mục bài viết
        """
        default_og_image = safe_static('img/default.png')

        # Lấy tiêu đề và mô tả Open Graph
        title = obj.meta_title if obj.meta_title else obj.name
        desc = (
            obj.meta_desc if obj.meta_desc
            else truncatechars(strip_tags(obj.desc_safe), 145)
            if obj.desc_safe else settings.SITE_DESC
        )

        return {
            'title': title,
            'description': desc,
            'images': default_og_image,
            'url': obj.full_url()
        }

    @extend_schema_field(serializers.CharField)
    def get_url(self, obj) -> str:
        return obj.get_absolute_url()

    @extend_schema_field(serializers.CharField)
    def get_full_url(self, obj) -> str:
        return obj.full_url()

    class Meta:
        model = ArticleCategory
        fields = (
            'name', 'desc_safe', 'slug', 'order',
            'meta_title', 'meta_desc', 'url', 'full_url', 'open_graph'
        )


class ArticleTagSerializer(serializers.ModelSerializer):
    """
    Serializer cho model ArticleTag
    """
    open_graph = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    full_url = SerializerMethodField()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj):
        """
        Lấy dữ liệu Open Graph cho tag bài viết
        """
        default_og_image = safe_static('img/default.png')

        # Lấy tiêu đề và mô tả Open Graph
        title = obj.meta_title if obj.meta_title else obj.name
        desc = (
            obj.meta_desc if obj.meta_desc
            else truncatechars(strip_tags(obj.desc_safe), 145)
            if obj.desc_safe else settings.SITE_DESC
        )

        return {
            'title': title,
            'description': desc,
            'images': default_og_image,
            'url': obj.full_url()
        }

    @extend_schema_field(serializers.CharField)
    def get_url(self, obj) -> str:
        return obj.get_absolute_url()

    @extend_schema_field(serializers.CharField)
    def get_full_url(self, obj) -> str:
        return obj.full_url()

    class Meta:
        model = ArticleTag
        fields = (
        'name', 'desc_safe', 'slug', 'order',
        'meta_title', 'meta_desc', 'url', 'full_url', 'open_graph'
        )


class ArticleAuthorSerializer(serializers.ModelSerializer):
    """
    Serializer cho model User (tác giả).
    Username luôn trả về viết hoa theo quy ước brand.
    """
    username = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('username', 'full_name')

    @extend_schema_field(serializers.CharField)
    def get_username(self, obj):
        return (obj.username or '').upper()

    @extend_schema_field(serializers.CharField)
    def get_full_name(self, obj):
        profile = getattr(obj, 'user_profile_set', None)
        if profile and profile.full_name():
            return profile.full_name()
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Article
    """
    url = serializers.SerializerMethodField()
    full_url = SerializerMethodField()
    category = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField)
    def get_author(self, obj):
        """
        Author hiển thị cố định là ADMIN.WEB theo quy ước brand.
        """
        return {'username': 'ADMIN.WEB', 'full_name': ''}

    @extend_schema_field(serializers.CharField)
    def get_category(self, obj):
        """
        Lấy thông tin danh mục
        """
        return {
            'name': obj.category.name,
            'slug': obj.category.slug
        }

    @extend_schema_field(serializers.CharField)
    def get_tags(self, obj):
        """
        Lấy thông tin tags
        """
        return [
            {
                'name': tag.name,
                'slug': tag.slug
            } for tag in obj.tags.all()
        ]

    @extend_schema_field(serializers.CharField)
    def get_featured_image(self, obj):
        """
        Lấy URL của hình ảnh đại diện. Ưu tiên file upload, fallback sang URL
        ngoài mà admin dán từ Media Library.
        """
        return _article_featured_image_url(obj)

    @extend_schema_field(serializers.CharField)
    def get_url(self, obj) -> str:
        return obj.get_absolute_url()

    @extend_schema_field(serializers.CharField)
    def get_full_url(self, obj) -> str:
        return obj.full_url()

    class Meta:
        model = Article
        fields = (
            'code', 'title', 'slug', 'excerpt_safe', 'author', 'category', 'tags', 'featured', 'featured_image',
            'published_at', 'created_at', 'updated_at', 'url', 'full_url'
        )


class ArticleRelatedSerializer(serializers.ModelSerializer):
    """
    Serializer bài viết liên quan
    """
    featured_image = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    full_url = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_featured_image(self, obj):
        """
        Lấy URL của hình ảnh đại diện. Ưu tiên file upload, fallback sang URL
        ngoài mà admin dán từ Media Library.
        """
        return _article_featured_image_url(obj)

    @extend_schema_field(serializers.CharField)
    def get_url(self, obj) -> str:
        return obj.get_absolute_url()

    @extend_schema_field(serializers.CharField)
    def get_full_url(self, obj) -> str:
        return obj.full_url()

    class Meta:
        """
        Cài đặt các thông tin về model
        """
        model = Article
        fields = [
            'code', 'title', 'excerpt_safe', 'featured_image', 'published_at', 'url', 'full_url'
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer chi tiết cho model Article
    """
    category = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    full_url = SerializerMethodField()
    open_graph = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    related_articles = serializers.SerializerMethodField()

    @extend_schema_field(serializers.DictField)
    def get_author(self, obj):
        """
        Author hiển thị cố định là ADMIN.WEB theo quy ước brand.
        """
        return {'username': 'ADMIN.WEB', 'full_name': ''}

    @extend_schema_field(serializers.CharField)
    def get_category(self, obj):
        """
        Lấy thông tin danh mục
        """
        if not obj.category:
            return None
        return {
            'name': obj.category.name,
            'slug': obj.category.slug
        }

    @extend_schema_field(serializers.CharField)
    def get_tags(self, obj):
        """
        Lấy thông tin tags
        """
        return [
            {
                'name': tag.name,
                'slug': tag.slug
            } for tag in obj.tags.all()
        ]

    @extend_schema_field(serializers.CharField)
    def get_featured_image(self, obj):
        """
        Lấy URL của hình ảnh đại diện. Ưu tiên file upload, fallback sang URL
        ngoài mà admin dán từ Media Library.
        """
        return _article_featured_image_url(obj)

    @extend_schema_field(serializers.CharField)
    def get_url(self, obj) -> str:
        return obj.get_absolute_url()

    @extend_schema_field(serializers.CharField)
    def get_full_url(self, obj) -> str:
        return obj.full_url()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj: Article):
        """
        Lấy dữ liệu Open Graph cho bài viết
        """
        default_og_image = safe_static('img/default.png')  # Ảnh mặc định
        meta_image_url = _image_field_url(obj.meta_image)
        featured_image_url = _article_featured_image_url(obj)
        images = [meta_image_url or featured_image_url or default_og_image]

        # Lấy tiêu đề và mô tả Open Graph
        title = obj.meta_title if obj.meta_title else obj.title
        desc = (
            obj.meta_desc if obj.meta_desc
            else truncatechars(strip_tags(obj.excerpt_safe), 145) if obj.excerpt_safe
            else settings.SITE_DESC
        )

        return {
            'title': title,
            'description': desc,
            'images': images,
            'url': obj.full_url()
        }

    @extend_schema_field(ArticleRelatedSerializer(many=True))
    def get_related_articles(self, obj):
        """
        Lấy danh sách bài viết liên quan:
        - Cùng danh mục hoặc có ít nhất 1 tag giống
        - Trạng thái đã xuất bản
        - Không phải chính nó
        - Sắp xếp theo thời gian công bố giảm dần
        """
        # Lấy danh mục và tags của bài viết hiện tại
        category = obj.category
        tags = obj.tags.all()

        # Lọc bài viết liên quan
        related_qs = Article.objects.filter(
            status='published',
            published_at__isnull=False
        ).exclude(id=obj.id).filter(
            Q(category=category) | Q(tags__in=tags)
        ).distinct().order_by('-published_at')[:5]

        return ArticleRelatedSerializer(related_qs, many=True).data

    class Meta:
        model = Article
        fields = (
            'code', 'title', 'slug', 'author', 'excerpt_safe', 'content_safe', 'category', 'tags', 'featured_image',
            'published_at', 'created_at', 'updated_at', 'url', 'full_url', 'open_graph', 'related_articles'
        )
