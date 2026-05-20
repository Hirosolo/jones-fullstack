from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from articles.forms import ArticleCategoryAdminForm, ArticleTagAdminForm, ArticleAdminForm, ArticleCommentAdminForm
from articles.models import ArticleCategory, ArticleTag, Article, ArticleComment


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    """
    Quản lý danh mục bài viết
    """
    list_display = ('name', 'slug', 'desc')
    search_fields = ('name', 'slug')
    ordering = ('name',)
    empty_value_display = '-empty-'
    save_on_top = True
    form = ArticleCategoryAdminForm


@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    """
    Quản lý tag bài viết
    """
    list_display = ('name', 'slug', 'desc')
    search_fields = ('name', 'slug')
    ordering = ('name',)
    empty_value_display = '-empty-'
    save_on_top = True
    form = ArticleTagAdminForm


class ArticleCommentInline(admin.TabularInline):
    """
    Hiển thị bình luận trong trang quản trị bài viết
    """
    model = ArticleComment
    extra = 0
    fieldsets = (
        (None, {
            'fields': ('code', 'content', 'author', 'created_at', 'parent')
        }),
    )
    readonly_fields = ('code', 'created_at')
    ordering = ('-created_at',)
    verbose_name = 'Bình luận'
    verbose_name_plural = 'Bình luận'

    @admin.display(description='Parent')
    def has_parent(self, obj: ArticleComment):
        if obj.parent:
            return obj.parent.code
        return '-empty-'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Quản lý bài viết
    """
    list_display = ('title', 'slug', 'featured', 'has_featured_image', 'category', 'author', 'published_at', 'status', 'num_views')
    search_fields = ('title', 'slug', 'content')
    list_filter = ('featured', 'published_at', 'status', 'category')
    ordering = ('-published_at', 'status')
    date_hierarchy = 'published_at'
    list_per_page = 100
    list_max_show_all = 100
    save_on_top = True
    empty_value_display = '-empty-'
    form = ArticleAdminForm

    @admin.display(description='Ảnh đại diện')
    def has_featured_image(self, obj):
        if obj.featured_image:
            return format_html('<span style="color:green;">✔</span>')
        return format_html('<span style="color:red;">✘</span>')

    def save_model(self, request, obj, form, change):
        if not change and obj.status == 'draft':
            obj.status = 'published'
        if obj.status == 'published' and not obj.published_at:
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(ArticleComment)
class ArticleCommentAdmin(admin.ModelAdmin):
    """
    Quản lý bình luận bài viết
    """
    list_display = ('code', 'article', 'content', 'author', 'created_at', 'has_parent')
    search_fields = ('content', 'article__title', 'created_by__username')
    list_filter = ('created_at',)
    ordering = ('created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 10
    list_max_show_all = 100
    empty_value_display = '-empty-'
    save_on_top = True
    form = ArticleCommentAdminForm

    @admin.action(description='Xóa nhanh các bình luận đã chọn')
    def remove_comments(self, request, queryset):
        """
        Xóa nhanh các bình luận đã chọn
        """
        count = queryset.count()
        for comment in queryset:
            comment.delete()
        self.message_user(request, f'Đã xóa {count} bình luận.', messages.SUCCESS)

    @admin.display(description='Parent')
    def has_parent(self, obj: ArticleComment):
        if obj.parent:
            return obj.parent.code
        return '-empty-'

    @admin.display(description='Author')
    def author_name(self, obj: ArticleComment):
        return obj.author.username

