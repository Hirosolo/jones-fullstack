# path: utils/models.py

from autoslug import AutoSlugField
from django.db import models
from django.urls import reverse
from easy_thumbnails.fields import ThumbnailerImageField

from utils.common import build_full_url
from utils.function import upload_home_slider_image, upload_static_page_image
from ckeditor.fields import RichTextField


class HomeSlider(models.Model):
    """
    Slider trên trang chủ.
    """
    title = models.CharField(max_length=100, help_text='Tiêu đề slider')
    desc = models.TextField(blank=True, help_text='Mô tả slider')
    desc_safe = models.TextField(blank=True, help_text='Mô tả an toàn')
    image = ThumbnailerImageField(
        upload_to=upload_home_slider_image,
        resize_source={'size': (3840, 2560), 'upscale': True, 'crop': True},
        help_text='Ảnh đại diện slider'
    )
    link = models.CharField(max_length=200, blank=True, help_text='Liên kết đến bài viết hoặc trang khác.')
    button_text = models.CharField(max_length=50, blank=True, help_text='Tiêu đề nút bấm chứa link.')
    order = models.IntegerField(default=0, help_text='Thứ tự hiển thị')
    status = models.BooleanField(default=True, help_text='Trạng thái hiển thị')

    class Meta:
        verbose_name_plural = 'Slider trang chủ'
        verbose_name = 'Slider trang chủ'
        ordering = ('-order',)


class MainMenu(models.Model):
    """
    Menu cấp 1 như CLOTHING, FOOTWEAR,...
    """
    name = models.CharField(max_length=100, help_text='Tên menu')
    link = models.URLField(
        max_length=200, blank=True,
        help_text='Liên kết đến bài viết hoặc trang khác.'
    )
    target = models.CharField(
        max_length=20, blank=True, default='_self',
        help_text='Target của liên kết (ví dụ: _blank, _self, _parent, _top)'
    )
    rel = models.CharField(
        max_length=200, blank=True, default='noopener noreferrer',
        help_text='Thuộc tính rel của liên kết (ví dụ: noopener noreferrer nofollow)'
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text='Thứ tự hiển thị'
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class SubMenuGroup(models.Model):
    """
    Nhóm con trong CLOTHING như JERSEYS & JACKETS,...
    """
    main_menu = models.ForeignKey(
        MainMenu,
        on_delete=models.CASCADE,
        related_name='menu_groups_set',
        help_text='Menu cấp 1'
    )
    name = models.CharField(max_length=100, help_text='Tên nhóm menu')
    order = models.PositiveIntegerField(default=1, help_text='Thứ tự hiển thị')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.main_menu.name})"


class SubMenuItem(models.Model):
    """
    Các item nhỏ như Baseball Jersey, 3D Hoodie,...
    """
    group = models.ForeignKey(
        SubMenuGroup,
        on_delete=models.CASCADE,
        related_name='menu_items_set',
        help_text='Nhóm menu'
    )
    name = models.CharField(max_length=100, help_text='Tên item menu')
    link = models.URLField(
        max_length=200, blank=True,
        help_text='Liên kết đến bài viết hoặc trang khác.'
    )
    target = models.CharField(
        max_length=20, blank=True, default='_self',
        help_text='Target của liên kết (ví dụ: _blank, _self, _parent, _top)'
    )
    rel = models.CharField(
        max_length=200, blank=True, default='noopener noreferrer',
        help_text='Thuộc tính rel của liên kết (ví dụ: noopener noreferrer nofollow)'
    )
    order = models.PositiveIntegerField(default=1, help_text='Thứ tự hiển thị')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.group.name})"


class FooterMenuGroup(models.Model):
    """
    Nhóm menu chân trang.
    """
    title = models.CharField(max_length=100, help_text='Tên nhóm menu')
    order = models.PositiveIntegerField(default=1, help_text='Thứ tự hiển thị')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class FooterMenuItem(models.Model):
    """
    Mục menu chân trang.
    """
    group = models.ForeignKey(
        FooterMenuGroup,
        on_delete=models.CASCADE,
        related_name='footer_menu_items',
        help_text='Nhóm menu chân trang'
    )
    label = models.CharField(max_length=100, help_text='Tên mục menu')
    link = models.URLField(
        max_length=200, blank=True,
        help_text='Liên kết đến bài viết hoặc trang khác.'
    )
    order = models.PositiveIntegerField(default=1, help_text='Thứ tự hiển thị')
    target = models.CharField(
        max_length=20, blank=True, default='_self',
        help_text='Target của liên kết (ví dụ: _blank, _self, _parent, _top)'
    )
    rel = models.CharField(
        max_length=200, blank=True, default='noopener noreferrer',
        help_text='Thuộc tính rel của liên kết (ví dụ: noopener noreferrer nofollow)'
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.label} ({self.group.title})"


class StaticPage(models.Model):
    """
    Model cho các trang tĩnh như Giới thiệu, Chính sách bảo mật,...
    """
    title = models.CharField(
        max_length=100, verbose_name='Tên trang',
        help_text='Nhập tiêu đề trang, tốt nhất không quá 65 ký tự'
    )
    slug = AutoSlugField(
        max_length=255, populate_from='title', editable=True, blank=True, unique=True,
        verbose_name='Slug', help_text='Nhập slug cho trang, sẽ tự động tạo từ tiêu đề nếu để trống'
    )
    excerpt = models.TextField(blank=True, help_text='Trích dẫn ngắn cho trang', verbose_name='Trích dẫn ngắn')
    excerpt_safe = models.TextField(
        blank=True, verbose_name='Trích dẫn an toàn',
        help_text='Trích dẫn an toàn cho trang, đã loại bỏ HTML không an toàn'
    )
    content = RichTextField(verbose_name='Nội dung', help_text='Nhập nội dung cho trang')
    content_safe = models.TextField(
        blank=True, verbose_name='Nội dung an toàn',
        help_text='Nội dung an toàn cho trang, đã loại bỏ HTML không an toàn'
    )
    STATUS_PAGE_CHOICES = (
        ('W', 'Nháp...'),
        ('P', 'Đã công khai.'),
    )
    status = models.CharField(max_length=1, choices=STATUS_PAGE_CHOICES, default='W', verbose_name='Trạng thái',
                              help_text='Trạng thái trang')
    meta_title = models.CharField(
        max_length=60, blank=True, verbose_name='Tiêu đề SEO',
        help_text='Tiêu đề SEO cho trang, tốt nhất không quá 60 ký tự'
    )
    meta_desc = models.CharField(
        max_length=145, blank=True, verbose_name='Mô tả SEO',
        help_text='Mô tả SEO cho trang, tốt nhất không quá 145 ký tự'
    )
    meta_image = ThumbnailerImageField(
        upload_to=upload_static_page_image,
        resize_source={'size': (1200, 630), 'upscale': True, 'crop': True},
        blank=True, verbose_name='Ảnh đại diện SEO',
        help_text='Ảnh đại diện cho trang khi chia sẻ trên mạng xã hội'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo', help_text='Ngày tạo trang')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật', help_text='Ngày cập nhật trang')

    class Meta:
        """
        Cài đặt các thông tin về model
        """
        ordering = ['-created_at']

    def __str__(self):
        """
        Trả về tiêu đề trang
        """
        return self.title if self.title else ''

    def url(self):
        """
        Xây dựng đường dẫn tới trang
        """
        return reverse('static_page', args=[self.slug]) if self.slug else ''

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn tới trang với domain
        """
        return build_full_url(self.url())

