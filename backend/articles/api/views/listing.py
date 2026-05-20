# path: articles/api/views/listing.py

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from articles.api.serializers import ArticleSerializer, ArticleCategorySerializer, ArticleTagSerializer, \
    ArticleAuthorSerializer
from articles.models import Article, ArticleCategory, ArticleTag


class ArticlePagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response({
            'ok': True,
            'data': {
                'page_obj': {
                    'number': self.page.number,
                    'paginator': {
                        'num_pages': self.page.paginator.num_pages,
                        'count': self.page.paginator.count,
                    },
                    'has_next': self.page.has_next(),
                    'has_previous': self.page.has_previous(),
                    'next_page_number': self.page.next_page_number() if self.page.has_next() else None,
                    'previous_page_number': self.page.previous_page_number() if self.page.has_previous() else None,
                },
                'results': data
            }
        })


@extend_schema(
    summary="Danh sách tất cả bài viết",
    description="Danh sách tất cả các bài viết được công khai"
)
class ArticleListView(ListAPIView):
    """
    Danh sách tất cả các bài viết được công khai.
    Nếu không tìm thấy thì trả về thông báo không tìm thấy
    """
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]
    pagination_class = ArticlePagination

    def get_queryset(self):
        qs = (Article.objects.filter(status='published')
              .exclude(published_at=None)
              .order_by('-published_at'))
        return qs


@extend_schema(
    summary="Danh sách bài viết nổi bật",
    description="Danh sách các bài viết được đánh dấu là nổi bật"
)
class ArticleFeaturedListView(ListAPIView):
    """
    Danh sách các bài viết được đánh dấu là nổi bật
    """
    serializer_class = ArticleSerializer
    permission_classes = [AllowAny]
    pagination_class = ArticlePagination

    def get_queryset(self):
        qs = (Article.objects.filter(status='published', featured=True)
              .exclude(published_at=None)
              .order_by('-published_at'))
        return qs


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            description='Slug của danh mục cần xem',
            required=True
        )
    ],
    summary="Chi tiết danh mục + danh sách bài viết",
    description="Trả về thông tin danh mục kèm danh sách các bài viết thuộc danh mục đó, có phân trang"
)
class ArticleCategoryListView(APIView):
    """
    Danh sách các bài viết theo danh mục
    """
    permission_classes = [AllowAny]

    def get(self, request):
        slug = request.GET.get('slug', '')
        category = get_object_or_404(ArticleCategory, slug=slug)

        # Lọc bài viết đã xuất bản thuộc danh mục
        articles = Article.objects.filter(
            category=category,
            status='published'
        ).exclude(published_at=None).order_by('-published_at')

        # Phân trang
        paginator = ArticlePagination()
        page = paginator.paginate_queryset(articles, request)
        serialized_articles = ArticleSerializer(page, many=True, context={'request': request})

        # Trả về response gồm thông tin category và danh sách bài viết đã phân trang
        return paginator.get_paginated_response({
            'category': ArticleCategorySerializer(category, context={'request': request}).data,
            'articles': serialized_articles.data
        })


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='slug',
            type=OpenApiTypes.STR,
            description='Slug của tag cần xem',
            required=True
        )
    ],
    summary="Chi tiết tag + danh sách bài viết",
    description="Trả về thông tin tag kèm danh sách các bài viết thuộc tag đó, có phân trang"
)
class ArticleTagListView(APIView):
    """
    Danh sách các bài viết theo tag
    """
    permission_classes = [AllowAny]

    def get(self, request):
        slug = request.GET.get('slug')
        tag = get_object_or_404(ArticleTag, slug=slug)

        articles = Article.objects.filter(tags=tag, status='published').exclude(published_at=None).order_by('-published_at')
        paginator = ArticlePagination()
        page = paginator.paginate_queryset(articles, request)
        serialized_articles = ArticleSerializer(page, many=True, context={'request': request})

        return paginator.get_paginated_response({
            'tag': ArticleTagSerializer(tag, context={'request': request}).data,
            'articles': serialized_articles.data
        })


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='username',
            type=OpenApiTypes.STR,
            description='Username tác giả',
            required=True
        )
    ],
    summary="Chi tiết tác giả + danh sách bài viết",
    description="Trả về thông tin tác giả cùng với các bài viết họ đã xuất bản, có phân trang"
)
class ArticleAuthorListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        username = request.GET.get('username', '')
        author = User.objects.filter(username=username).first()
        if not author:
            raise NotFound('Không tìm thấy tác giả')

        articles = Article.objects.filter(
            author=author,
            status='published'
        ).exclude(published_at=None).order_by('-published_at')

        paginator = ArticlePagination()
        page = paginator.paginate_queryset(articles, request)
        serialized_articles = ArticleSerializer(page, many=True, context={'request': request})

        return paginator.get_paginated_response({
            'author': ArticleAuthorSerializer(author, context={'request': request}).data,
            'articles': serialized_articles.data
        })


@extend_schema(
    summary="Danh sách danh mục bài viết",
    description="Danh sách tất cả các danh mục bài viết"
)
class ArticleCategoryListViewAll(ListAPIView):
    """
    Danh sách tất cả các danh mục bài viết
    """
    serializer_class = ArticleCategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return ArticleCategory.objects.all()


@extend_schema(
    summary="Danh sách tag bài viết",
    description="Danh sách tất cả các tag bài viết"
)
class ArticleTagListViewAll(ListAPIView):
    """
    Danh sách tất cả các tag bài viết
    """
    serializer_class = ArticleTagSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return ArticleTag.objects.all()

