# path: articles/models.py

from autoslug import AutoSlugField
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from easy_thumbnails.fields import ThumbnailerImageField

from articles.utils import upload_articles_image
from utils.common import build_full_url


class ArticleCategory(models.Model):
    """
    Danh mục bài viết.
    """
    name = models.CharField(max_length=100, help_text='Tên danh mục')
    desc = models.TextField(blank=True, help_text='Mô tả danh mục')
    desc_safe = models.TextField(blank=True, help_text='Mô tả an toàn')
    slug = AutoSlugField(populate_from='name', blank=True, unique=True, editable=True, max_length=500, help_text='Đường dẫn thân thiện')
    order = models.IntegerField(default=0, help_text='Thứ tự hiển thị')
    admin_note = models.TextField(blank=True, help_text='Ghi chú của quản trị viên')

    # SEO
    meta_title = models.CharField(blank=True, max_length=60, help_text='Tiêu đề SEO')
    meta_desc = models.CharField(blank=True, max_length=145, help_text='Mô tả SEO')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Danh mục bài viết'
        verbose_name = 'Danh mục bài viết'
        ordering = ('-order', 'name')

    def url(self):
        return reverse('article_category', args=[self.slug])

    def get_absolute_url(self):
        return self.url()

    def full_url(self):
        return build_full_url(self.url())


class ArticleTag(models.Model):
    """
    Thẻ bài viết.
    """
    name = models.CharField(max_length=100, help_text='Tên thẻ')
    desc = models.TextField(blank=True, help_text='Mô tả thẻ')
    desc_safe = models.TextField(blank=True, help_text='Mô tả an toàn')
    slug = AutoSlugField(populate_from='name', blank=True, unique=True, editable=True, max_length=500, help_text='Đường dẫn thân thiện')
    order = models.IntegerField(default=0, help_text='Thứ tự hiển thị')
    admin_note = models.TextField(blank=True, help_text='Ghi chú của quản trị viên')

    # SEO
    meta_title = models.CharField(blank=True, max_length=60, help_text='Tiêu đề SEO')
    meta_desc = models.CharField(blank=True, max_length=145, help_text='Mô tả SEO')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Thẻ bài viết'
        verbose_name = 'Thẻ bài viết'
        ordering = ('-order', 'name')

    def url(self):
        return reverse('article_tag', args=[self.slug])

    def get_absolute_url(self):
        return self.url()

    def full_url(self):
        return build_full_url(self.url())


class Article(models.Model):
    """
    Bài viết trên trang web.
    """
    title = models.CharField(max_length=100, help_text='Tiêu đề bài viết')
    code = models.CharField(max_length=13, unique=True, blank=True, help_text='Mã bài viết. Tự động tạo khi tạo mới')
    excerpt = models.TextField(blank=True, help_text='Trích dẫn bài viết')
    excerpt_safe = models.TextField(blank=True, help_text='Trích dẫn bài viết (safe)')
    featured_image = ThumbnailerImageField(
        blank=True,
        upload_to=upload_articles_image,
        resize_source={'size': (1200, 800), 'upscale': True, 'crop': True},
        help_text='Ảnh đại diện bài viết'
    )
    # External URL for the featured image (set when admin pastes a URL
    # from /acp/ Media Library instead of uploading a file).
    featured_image_url = models.URLField(blank=True, max_length=1000)
    content = models.TextField(blank=True, help_text='Nội dung bài viết')
    content_safe = models.TextField(blank=True, help_text='Nội dung bài viết (safe)')
    slug = AutoSlugField(populate_from='title', blank=True, unique=True, editable=True, max_length=500, help_text='Đường dẫn thân thiện')
    author = models.ForeignKey(User, related_name='articles_author_set', on_delete=models.SET_NULL, null=True, blank=True, help_text='Tác giả bài viết')
    author_name = models.CharField(max_length=100, blank=True, help_text='Tên tác giả (nếu không phải là người dùng)')
    published_at = models.DateTimeField(blank=True, null=True, help_text='Ngày xuất bản')
    num_views = models.IntegerField(default=0, help_text='Số lượt xem')
    featured = models.BooleanField(default=False, help_text='Bài viết nổi bật')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('published', 'Đã xuất bản'),
        ('private', 'Riêng tư'),
        ('archived', 'Đã lưu trữ'),
        ('deleted', 'Đã xóa')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Trạng thái bài viết'
    )

    meta_title = models.CharField(blank=True, max_length=60, help_text='Tiêu đề SEO')
    meta_desc = models.CharField(blank=True, max_length=145, help_text='Mô tả SEO')
    meta_image = ThumbnailerImageField(
        blank=True,
        upload_to=upload_articles_image,
        resize_source={'size': (1200, 800), 'upscale': True, 'crop': True},
    )
    # Mặc định nếu không chọn danh mục thì sẽ thuộc về danh mục "Không xác định"
    category = models.ForeignKey(
        ArticleCategory,
        on_delete=models.SET_NULL,
        related_name='categories_set',
        help_text='Danh mục bài viết',
        blank=True,
        null=True,
        default=1
    )
    tags = models.ManyToManyField(
        ArticleTag,
        related_name='tags_set',
        help_text='Thẻ bài viết',
        blank=True
    )

    admin_notes = models.TextField(blank=True, help_text='Ghi chú của admin')
    admin_check = models.DateTimeField(blank=True, null=True, help_text='Ngày kiểm tra của admin')

    class Meta:
        verbose_name_plural = 'Bài viết'
        verbose_name = 'Bài viết'
        ordering = ('-published_at',)

    def __str__(self):
        return self.title

    def get_featured_image_thumb(self, width=1200):
        if not self.featured_image:
            return ''
        if width >= 1200:
            return self.featured_image.url
        option_dict = {
            'size': (width, width),
            'width': width,
            'height': width,
            'crop': True,
            'upscale': True,
        }
        return self.featured_image.get_thumbnail(option_dict).url

    def url(self):
        return reverse('article_detail', args=[self.slug])

    def get_absolute_url(self):
        return self.url()

    def full_url(self):
        return build_full_url(self.url())


class ArticleComment(models.Model):
    """
    Bình luận cho bài viết.
    """
    code = models.CharField(max_length=13, unique=True, blank=True, help_text='Mã bình luận. Tự động tạo khi tạo mới')
    article = models.ForeignKey(
        Article,
        related_name='comments',
        on_delete=models.CASCADE,  # Nếu bài viết bị xóa thì xóa hết bình luận liên quan
        help_text='Bài viết'
    )
    author = models.ForeignKey(
        User,
        related_name='articles_comments_author_set',
        on_delete=models.SET_NULL,  # Nếu người dùng bị xóa thì không ảnh hưởng đến bình luận
        null=True,
        blank=True,
        help_text='Tác giả bình luận'
    )
    content = models.TextField(help_text='Nội dung bình luận')
    content_safe = models.TextField(help_text='Nội dung bình luận (safe)')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Ngày tạo bình luận')
    removed = models.BooleanField(default=False, help_text='Đã xóa')
    updated_at = models.DateTimeField(auto_now=True, help_text='Ngày cập nhật bình luận')

    parent = models.ForeignKey(
        'self',
        related_name='children',
        on_delete=models.SET_NULL,  # Nếu bình luận cha bị xóa thì không ảnh hưởng đến bình luận con
        blank=True,
        null=True,
        help_text='Trả lời bình luận'
    )

    class Meta:
        verbose_name_plural = 'Bình luận bài viết'
        verbose_name = 'Bình luận bài viết'
        ordering = ('-created_at',)

    def __str__(self):
        """
        Trả về tên người tạo bình luận.
        Nếu không có bình luận cha thì trả về tên người tạo bình luận cùng với mã bình luận.
        Nếu có bình luận cha thì trả về tên người tạo bình luận cha cùng với mã bình luận cha và mã bình luận.
        Phân biệt mã bình luận cha và mã bình luận bằng cách thêm "reply_to:" vào mã bình luận con.
        """
        if self.parent:
            return f'{self.author.username} - {self.parent.code} reply_to: {self.parent.author.username} - {self.code}'
        return f'{self.author.username} - {self.code}'


class Timeline(models.Model):
    """
    Thống kê số lượt xem của bài viết theo thời gian.
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='+', help_text='Dự án')
    start_date = models.DateField()
    frame = models.CharField(max_length=20, help_text='Khung thời gian', choices=(('M', 'Tháng'), ('W', 'Tuần')))
    num_views = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Timelines'
        verbose_name = 'Timeline'
        indexes = [
            models.Index(fields=['article', 'start_date', 'frame']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['article', 'start_date', 'frame'],
                name='unique_article_timeline_14052025'
            ),
        ]

