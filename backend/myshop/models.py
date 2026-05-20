# path: myshop/models.py
# Description: Định nghĩa các model cho ứng dụng myshop.

from typing import Any

from autoslug import AutoSlugField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, CharField
from django.urls import reverse
from django_countries.fields import CountryField
from easy_thumbnails.fields import ThumbnailerImageField

from myshop.utils import upload_product_image, upload_product_category_image, upload_product_brand_image
from profiles.models import Profile
from utils.common import get_random_code2, slugify2, build_full_url


class Brand(models.Model):
    """
    Mô hình thương hiệu sản phẩm.
    """
    name = models.CharField(max_length=255, unique=True, help_text='Tên thương hiệu.')
    slug = AutoSlugField(populate_from='name', blank=True, unique=True, editable=True,
                         help_text='Slug của thương hiệu.')
    desc = models.TextField(blank=True, help_text='Mô tả chi tiết về thương hiệu.')
    desc_safe = models.TextField(blank=True, help_text='Mô tả chi tiết về thương hiệu (safe)')
    logo = ThumbnailerImageField(
        blank=True,
        upload_to=upload_product_brand_image,
        resize_source={'size': (400, 400), 'upscale': True, 'crop': True},
        help_text='Hình ảnh logo thương hiệu.',
    )
    order = models.IntegerField(default=0, help_text='Độ ưu tiên hiển thị. Càng lớn thì càng hiển thị trước.')
    meta_title = models.CharField(blank=True, max_length=60, help_text='Tiêu đề SEO')
    meta_desc = models.CharField(
        blank=True, max_length=145,
        help_text='Mô tả cho SEO trang, tối đa 145 ký tự. Nếu để trống thì sẽ hệ thống sẽ tự động lấy từ mô tả.'
    )
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')

    def save(self, *args, **kwargs):
        """
        Ghi đè phương thức save mặc định của thương hiệu sản phẩm,
        tạo slug cho thương hiệu sản phẩm từ tên thương hiệu.
        """
        self.slug = slugify2(self.name)
        super().save(*args, **kwargs)

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết thương hiệu.
        """
        return reverse('myshop:brand_detail', args=[self.slug])

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết thương hiệu.
        Ví dụ: /brands/<brand>
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết thương hiệu.
        """
        if self.slug:
            return build_full_url(self.url())
        return ''

    def __str__(self):
        """
        Trả về tên thương hiệu.
        """
        return self.name

    class Meta:
        verbose_name_plural = 'brands'
        ordering = ('-order', 'name')
        indexes = [
            models.Index(fields=['-order', 'name']),
        ]


class Category(models.Model):
    """
    Mô hình danh mục sản phẩm.
    """
    name = models.CharField(max_length=255, unique=True, help_text='Tên danh mục sản phẩm.')
    slug = AutoSlugField(populate_from='name', blank=True, unique=True, editable=True, help_text='Slug của danh mục.')
    desc = models.TextField(max_length=255, null=True, blank=True, help_text='Mô tả chi tiết về danh mục sản phẩm.')
    desc_safe = models.TextField(max_length=255, null=True, blank=True, help_text='Mô tả chi tiết về danh mục sản phẩm (safe).')
    img = ThumbnailerImageField(
        blank=True,
        upload_to=upload_product_category_image,
        resize_source={'size': (400, 400), 'upscale': True, 'crop': True},
        help_text='Hình ảnh danh mục.',
    )
    order = models.IntegerField(default=0, help_text='Thứ tự hiển thị. Lớn hơn thì hiển thị trước.')
    meta_title = models.CharField(blank=True, max_length=60, help_text='Tiêu đề SEO')
    meta_desc = models.CharField(
        blank=True, max_length=145,
        help_text='Mô tả SEO cho trang, tối đa 145 ký tự. Nếu để trống thì sẽ hệ thống sẽ tự động lấy từ mô tả.'
    )
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')

    def save(self, *args, **kwargs):
        """
        Ghi đè phương thức save mặc định của danh mục sản phẩm,
        tạo slug cho danh mục sản phẩm từ tên danh mục.
        """
        self.slug = slugify2(self.name)
        super().save(*args, **kwargs)

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết danh mục sản phẩm.
        """
        return reverse('myshop:category_detail', args=[self.slug])

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết danh mục sản phẩm.
        Ví dụ: /categories/<category>
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết danh mục sản phẩm.
        """
        if self.slug:
            return build_full_url(self.url())
        return ''

    def __str__(self):
        """
        Trả về tên danh mục sản phẩm.
        """
        return self.name

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ('-order', 'name')
        indexes = [
            models.Index(fields=['-order', 'name']),
        ]


class Tag(models.Model):
    """
    Mô hình tags cho sản phẩm.
    """
    name = models.CharField(max_length=255, unique=True, help_text='Tên tags.')
    desc = models.TextField(blank=True, help_text='Mô tả chi tiết về tags.')
    desc_safe = models.TextField(blank=True, help_text='Mô tả chi tiết về tags (safe).')
    slug = AutoSlugField(populate_from='name', blank=True, unique=True, editable=True, help_text='Slug của tags.')
    meta_title = models.CharField(blank=True, max_length=60, help_text='Tiêu đề SEO')
    meta_desc = models.CharField(
        blank=True, max_length=145,
        help_text='Mô tả cho SEO trang, tối đa 145 ký tự. Nếu để trống thì sẽ hệ thống sẽ tự động lấy từ mô tả.'
    )
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')

    def save(self, *args, **kwargs):
        """
        Ghi đè phương thức save mặc định của tags sản phẩm,
        tạo slug cho tags sản phẩm từ tên tags.
        """
        self.slug = slugify2(self.name)
        super().save(*args, **kwargs)

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết tags sản phẩm.
        """
        return reverse('myshop:tags_detail', args=[self.slug])

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết tags sản phẩm.
        Ví dụ: /tags/<tags>
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết tags sản phẩm.
        """
        if self.slug:
            return build_full_url(self.url())
        return ''

    def __str__(self):
        """
        Trả về tên tags sản phẩm.
        """
        return self.name

    class Meta:
        verbose_name_plural = 'tags'
        indexes = [
            models.Index(fields=['name']),
        ]


# Tạo mô hình biến thể sản phẩm (Đạt)
class ProductColor(models.Model):
    """
    Mô hình màu sắc sản phẩm.
    """
    name = models.CharField(max_length=100, verbose_name="Tên màu", help_text="Tên màu sắc sản phẩm")
    value = models.CharField(max_length=50, verbose_name="Giá trị", help_text="Giá trị dùng làm id (vd: color-black)")
    color_code = models.CharField(max_length=10, verbose_name="Mã màu", blank=True,
                                  help_text="Mã màu sắc (hex code, vd: #FFFFFF)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Màu sắc sản phẩm"
        verbose_name_plural = "Màu sắc sản phẩm"


class ProductSize(models.Model):
    """
    Mô hình kích thước sản phẩm.
    """
    name = models.CharField(max_length=10, verbose_name="Tên kích thước", help_text="Tên kích thước sản phẩm")
    value = models.CharField(max_length=20, verbose_name="Giá trị", help_text="Giá trị dùng làm id (vd: size-xl)")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự", help_text="Thứ tự sắp xếp")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kích thước sản phẩm"
        verbose_name_plural = "Kích thước sản phẩm"
        ordering = ['order']


class Product(models.Model):
    """
    Mô hình sản phẩm.
    """
    name = models.CharField(verbose_name='Tên sản phẩm', max_length=255, help_text='Tên của sản phẩm.')
    code = models.CharField(
        verbose_name='Mã sản phẩm',
        max_length=8,
        unique=True,
        editable=False,
        help_text='Mã ngẫu nhiên của sản phẩm (8 số), được tạo tự động.')
    slug = AutoSlugField(
        populate_from='name',
        blank=True,
        unique=True,
        editable=True,
        help_text='Slug của sản phẩm.'
    )
    desc = models.TextField(
        verbose_name='Mô tả chi tiết',
        help_text='Mô tả chi tiết về sản phẩm.'
    )
    desc_safe = models.TextField(
        blank=True,
        verbose_name='Mô tả chi tiết (An toàn)',
        help_text='Mô tả chi tiết về sản phẩm đã loại bỏ các thẻ HTML không cần thiết.'
    )
    desc_short = models.CharField(
        verbose_name='Mô tả ngắn',
        max_length=255,
        help_text='Mô tả ngắn về sản phẩm.'
    )
    desc_short_safe = models.CharField(
        blank=True,
        verbose_name='Mô tả ngắn (An toàn)',
        max_length=255,
        help_text='Mô tả ngắn về sản phẩm đã loại bỏ các thẻ HTML không cần thiết.'
    )
    seller_notes = models.TextField(
        verbose_name='Ghi chú thêm của người bán',
        blank=True,
        help_text='Ghi chú thêm của người bán về sản phẩm, không có thì để trống.'
    )
    seller_notes_safe = models.TextField(
        verbose_name='Ghi chú thêm của người bán (An toàn)',
        blank=True,
        help_text='Ghi chú thêm của người bán về sản phẩm, đã loại bỏ các thẻ HTML không cần thiết.'
    )
    price_origin = models.FloatField(verbose_name='Giá gốc', help_text='Giá gốc của sản phẩm.')
    price_promo = models.FloatField(
        verbose_name='Giá khuyến mãi',
        null=True, blank=True,
        help_text='Giá khuyến mãi của sản phẩm.'
    )
    stock = models.PositiveIntegerField(verbose_name='Tồn kho', help_text='Số lượng sản phẩm còn lại trong kho.')
    is_available = models.BooleanField(
        verbose_name='Còn hàng?',
        default=True,
        help_text='Tình trạng hiện có của sản phẩm (còn hàng hay hết hàng).'
    )
    category = models.ForeignKey(
        Category, verbose_name='Danh mục',
        related_name='category_product_set',
        on_delete=models.SET_NULL,  # Nếu danh mục bị xóa thì sản phẩm không bị xóa theo.
        null=True,
        blank=True,
        help_text='Danh mục sản phẩm, sản phẩm thuộc danh mục nào.'
    )
    brand = models.ForeignKey(
        Brand,
        verbose_name='Thương hiệu',
        related_name='brand_product_set',
        on_delete=models.SET_NULL,  # Nếu thương hiệu bị xóa thì sản phẩm không bị xóa theo.
        null=True,
        blank=True,
        help_text='Thương hiệu của sản phẩm.'
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    times_purchased = models.PositiveIntegerField(
        verbose_name='Số lần sản phẩm được mua',
        default=0,
        help_text='Số lần sản phẩm được mua.'
    )
    cross_sell = models.ManyToManyField(
        'self',
        verbose_name='Bán chéo',
        blank=True,
        help_text='Sản phẩm thường được mua cùng nhau, tự chọn để tối ưu hóa bán chéo (cross-sell).'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Thẻ tags sản phẩm',
        blank=True,
        related_name='tags_product_set',
        help_text='Tags của sản phẩm, giúp tìm kiếm sản phẩm dễ dàng hơn, được chọn nhiều tags.'
    )
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')

    # Thông tin SEO
    meta_title = models.CharField(
        blank=True, max_length=60,
        help_text='Tiêu đề SEO cho sản phẩm tối đa 60 ký tự. Nếu để trống thì sẽ hệ thống sẽ tự động lấy từ tên sản phẩm.'
    )
    meta_desc = models.CharField(
        blank=True, max_length=145,
        help_text='Mô tả SEO cho sản phẩm, tối đa 145 ký tự. Nếu để trống thì sẽ hệ thống sẽ tự động lấy từ mô tả.'
    )

    def __str__(self):
        """
        Trả về tên sản phẩm.
        """
        return self.name

    def get_product_price(self):
        """
        Trả về giá của sản phẩm, nếu sản phẩm đang được khuyến mãi thì trả về giá khuyến mãi, ngược lại trả về giá gốc.
        """
        if self.price_promo is not None:
            return self.price_promo
        else:
            return self.price_origin

    def is_sale(self):
        """
        Kiểm tra xem sản phẩm có đang được khuyến mãi (sale) hay không.
        Nếu giá price_promo được nhập thì hiển thị nhãn sale, ngược lại thì không.
        """
        return self.price_promo is not None

    def calculate_sale_percentage(self):
        """
        Tính tổng số phần trăm giảm giá của sản phẩm dựa trên giá gốc và giá khuyến mãi.
        """
        if self.price_origin and self.price_promo:
            sale_amount = self.price_origin - self.price_promo
            sale_percentage = (sale_amount / self.price_origin) * 100
            return round(sale_percentage, 2)
        return None

    def save(self, *args, **kwargs):
        """
        Ghi đè phương thức save mặc định của sản phẩm, kiểm tra xem đã có mã sản phẩm chưa,
        nếu chưa có thì tạo mã sản phẩm ngẫu nhiên, sau đó quay lại lưu sản phẩm.
        """
        if not self.code:
            self.code = get_random_code2(8, 'n')
        super().save(*args, **kwargs)

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết sản phẩm.
        """
        return reverse('myshop:product_detail', args=[self.slug])

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết sản phẩm.
        Ví dụ: /products/<product>
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết sản phẩm.
        """
        if self.slug:
            return build_full_url(self.url())
        return ''

    def product_review_count(self):
        """
        Trả về số lượng đánh giá của sản phẩm.
        """
        reviews = Review.objects.filter(product=self)
        review_count = reviews.count()
        # Nếu có ít nhất một đánh giá thì trả về số lượng đánh giá, ngược lại trả về 0.
        # đảm bảo trả về giá trị số nguyên
        if review_count > 0:
            return review_count
        else:
            return 0

    def product_average_rating(self):
        """
        Trả về điểm đánh giá trung bình của sản phẩm.
        """
        reviews = Review.objects.filter(product=self)
        review_count = reviews.count()
        # Nếu có ít nhất một đánh giá thì tính điểm trung bình, ngược lại trả về 0.0.
        if review_count > 0:
            total_rating = sum([review.rating for review in reviews])
            average = total_rating / review_count
            return round(average, 2)
        else:
            return 0.0

    def related_products(self):
        """
        Trả về danh sách các sản phẩm liên quan dựa trên các tags và danh mục của sản phẩm hiện tại.
        """
        # Lấy ra tất cả các tag của sản phẩm hiện tại
        tags = self.tags.all()
        # Lấy ra danh mục của sản phẩm hiện tại
        category = self.category

        # Lọc các sản phẩm khác có ít nhất một trong các tag hoặc danh mục giống với sản phẩm hiện tại
        # sau đó loại bỏ sản phẩm hiện tại ra khỏi danh sách sản phẩm liên quan
        related_products = Product.objects.filter(
            Q(tags__in=tags) | Q(category=category)
        ).exclude(id=self.id).distinct()[:8]
        return related_products

    def get_color_images(self, color_value=None):

        """
        Trả về danh sách các ảnh của sản phẩm theo màu sắc.
        """
        from utils.common import build_media_url
        
        if color_value:
            images = ProductColorImage.objects.filter(
                product=self,
                color__value=color_value
            ).order_by('order')
        else:
            images = ProductColorImage.objects.filter(product=self).order_by('color__value', 'order')

        result = {}
        for img in images:
            color_value = img.color.value
            if color_value not in result:
                result[color_value] = []

            result[color_value].append({
                'alt': img.alt,
                'url': build_media_url(img.image.url) if img.image else ''
            })

        return result


class ProductColorImage(models.Model):
    """
    Mô hình ảnh cho từng màu sắc sản phẩm
    """
    color = models.ForeignKey(ProductColor, on_delete=models.CASCADE, related_name='color_images_set')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_color_images_set')
    alt = models.CharField(max_length=255, help_text='Chữ thay thế cho hình ảnh')
    image = ThumbnailerImageField(
        upload_to=upload_product_image,
        resize_source={'size': (800, 800), 'upscale': False, 'crop': False},
        verbose_name="Hình ảnh"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự", help_text="Thứ tự hiển thị")

    class Meta:
        verbose_name = "Ảnh màu sắc sản phẩm"
        verbose_name_plural = "Ảnh màu sắc sản phẩm"
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.alt}"


class ProductVariant(models.Model):
    """
    Mô hình biến thể sản phẩm kết hợp màu sắc và kích thước
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants_product_set',
        verbose_name="Sản phẩm"
    )
    color = models.ForeignKey(
        ProductColor,
        on_delete=models.CASCADE,
        related_name='variants_color_set',
        verbose_name="Màu sắc"
    )
    size = models.ForeignKey(
        ProductSize,
        on_delete=models.CASCADE,
        related_name='variants_size_set',
        verbose_name="Kích thước"
    )
    code = models.CharField(
        max_length=13,
        unique=True,
        verbose_name="Mã SKU",
        editable=False,
        help_text="Mã SKU riêng cho biến thể này, được tạo tự động."
    )
    price_origin = models.FloatField(null=True, blank=True, verbose_name="Giá của biến thể", help_text="Giá của biến thể")
    price_promo = models.FloatField(null=True, blank=True, verbose_name="Giá khuyến mãi của biến thể", help_text="Giá khuyến mãi của biến thể")

    class Meta:
        verbose_name = "Biến thể sản phẩm"
        verbose_name_plural = "Biến thể sản phẩm"
        unique_together = ('product', 'size', 'color')

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.size.name}"

    def is_sale(self):
        return self.price_promo is not None

    def get_price(self):
        return self.price_promo if self.price_promo else self.price_origin


class ProductImage(models.Model):
    product = models.ForeignKey(
        'Product', on_delete=models.CASCADE, null=True, blank=True,
        related_name='product_images_set', help_text='Hình ảnh của sản phẩm.'
    )
    alt = models.CharField(max_length=255, null=True, blank=True, help_text='Chữ thay thế cho hình ảnh')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    img = ThumbnailerImageField(
        blank=True,
        upload_to=upload_product_image,
        resize_source={'size': (1200, 800), 'upscale': False, 'crop': False},
        help_text='Hình ảnh sản phẩm.'
    )
    order = models.IntegerField(default=0, help_text='Thứ tự hiển thị hình ảnh. Càng lớn thì càng hiển thị trước.')
    removed = models.BooleanField(default=False, help_text='Đánh dấu hình ảnh đã bị xóa hay chưa.')

    def __str__(self) -> CharField | Any:
        """
        Trả về tiêu đề của hình ảnh.
        """
        return self.product.name

    class Meta:
        indexes = [
            models.Index(fields=['product', 'order', 'removed']),
        ]

    def get_thumb_by_width(self, width=1200):
        """
        Lấy ảnh thumbnail theo chiều rộng, đảm bảo tỉ lệ của ảnh gốc.
        """
        from utils.common import build_media_url
        
        if not self.img:
            return ''
        if width >= 1200:
            return build_media_url(self.img.url)
        # lấy tỉ lệ của ảnh gốc
        ratio = self.img.width / self.img.height
        new_height = int(width / ratio)
        option_dict = {
            'size': (width, new_height),
            'width': width,
            'height': new_height,
            'crop': True,
            'upscale': True,
        }
        return build_media_url(self.img.get_thumbnail(option_dict).url)


class Review(models.Model):
    """
    Mô hình đánh giá sản phẩm.
    """
    profile = models.ForeignKey(
        Profile, on_delete=models.SET_NULL,
        related_name='profile_review_set',
        help_text='Người dùng đánh giá.',
        null=True, blank=True,  # Cho phép người dùng chưa đăng nhập cũng có thể đánh giá sản phẩm (ẩn danh).
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,  # Nếu sản phẩm bị xóa thì đánh giá của sản phẩm cũng bị xóa theo.
        related_name='product_review_set',
        help_text='Sản phẩm được đánh giá.'
    )
    rating = models.PositiveIntegerField(help_text='Điểm đánh giá của sản phẩm, từ 1 đến 5 sao.')
    subject = models.CharField(max_length=100, blank=True, help_text='Tiêu đề review')
    content = models.TextField(blank=True, help_text='Nội dung review.')
    content_safe = models.TextField(blank=True, help_text='Nội dung review (safe).')
    code = models.CharField(max_length=13, unique=True, blank=True, editable=False, help_text='Mã đánh giá sản phẩm, được tạo tự động.')
    ip_review = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=False, help_text='Trạng thái đánh giá, True: Đã duyệt, False: Chưa duyệt')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Thời gian tạo đánh giá.')
    updated_at = models.DateTimeField(auto_now_add=True, help_text='Thời gian cập nhật đánh giá.')
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')

    def save(self, *args, **kwargs):
        """
        Ghi đè phương thức save mặc định của đánh giá sản phẩm,
        cập nhật điểm đánh giá trung bình của sản phẩm sau khi lưu đánh giá.
        """
        super(Review, self).save(*args, **kwargs)
        self.product.save()

    def delete(self, *args, **kwargs):
        """
        Ghi đè phương thức delete mặc định của đánh giá sản phẩm,
        cập nhật điểm đánh giá trung bình của sản phẩm sau khi xóa đánh giá.
        """
        product = self.product
        super(Review, self).delete(*args, **kwargs)
        product.save()


class WishList(models.Model):
    """
    Người dùng thích sản phẩm.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_wishlist_set', help_text='Người dùng thích sản phẩm.')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_wishlist_set', help_text='Sản phẩm được người dùng thích.')
    created_at = models.DateTimeField(auto_now_add=True)
    removed = models.BooleanField(default=False, help_text='Đánh dấu sản phẩm đã bị xóa khỏi danh sách yêu thích hay chưa.')

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_wishlist_2206',
                condition=models.Q(removed=False),
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'removed', '-created_at']),
        ]


class CartItem(models.Model):
    """
    Giỏ hàng.
    Thành viên có thể thêm sản phẩm vào giỏ hàng mà không cần đăng nhập.
    Sau khi đăng nhập, giỏ hàng sẽ tự merge vào thành viên.
    """
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, related_name='user_cart_item_set',
        help_text='Người mua'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, help_text='Khóa phiên của người dùng, dùng để xác định giỏ hàng của người dùng chưa đăng nhập.')
    variant_product = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.CASCADE, related_name='product_cart_item_set', help_text='Sản phẩm trong giỏ hàng.')
    quantity = models.IntegerField(default=1, help_text='Số lượng sản phẩm trong giỏ hàng.')
    updated_at = models.DateTimeField(auto_now=True)
    removed = models.BooleanField(default=False)

    def __str__(self):
        user_display = self.user.username if self.user else "anonymous"
        product_display = self.variant_product.product.name if self.variant_product else "unknown product"
        return f'cart of {user_display} - {product_display}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'variant_product'],
                name='unique_user_product_2206',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'removed', '-updated_at']),
        ]


class OrderTax(models.Model):
    """
    Mô hình thuế áp dụng cho đơn hàng.
    """
    name = models.CharField(max_length=100, unique=True, help_text='Tên thuế, ví dụ: Standard Tax, Los Angeles Tax, Texas Tax.')
    code = models.CharField(max_length=13, blank=True, unique=True, help_text='Mã định danh cho thuế.')
    value = models.DecimalField(max_digits=9, decimal_places=2, default=0.00, help_text='Giá trị thuế áp dụng cho đơn hàng.')
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên về thuế.')

    def __str__(self):
        return f'{self.name} ({self.code})'


class ShippingFee(models.Model):
    """
    Mô hình phí vận chuyển.
    """
    name = models.CharField(max_length=100, unique=True, help_text='Tên phí vận chuyển, ví dụ: Standard Shipping, Express Shipping.')
    code = models.CharField(max_length=13, blank=True, unique=True, help_text='Mã định danh cho phí vận chuyển.')
    value = models.DecimalField(max_digits=9, decimal_places=2, default=0.00, help_text='Giá trị phí vận chuyển.')
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên về phí vận chuyển.')

    def __str__(self):
        return f'{self.name} ({self.code})'


class Order(models.Model):
    """
    Đơn hàng được đặt.
    """
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='user_order_set',
        help_text='Người dùng đã đặt hàng, có thể là thành viên hoặc khách vãng lai.',
        null=True, blank=True,  # Cho phép người dùng chưa đăng nhập cũng có thể đặt hàng (ẩn danh).
    )
    code = models.CharField(max_length=13, unique=True, blank=True, editable=False, help_text='Mã đơn hàng, được tạo tự động.')
    order_tax = models.ForeignKey(
        OrderTax, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_tax_set', help_text='Thuế áp dụng cho đơn hàng.'
    )
    shipping_fee = models.ForeignKey(
        ShippingFee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='shipping_fee_set', help_text='Phí vận chuyển áp dụng cho đơn hàng.'
    )
    sub_total = models.DecimalField(max_digits=9, decimal_places=2, default=0, help_text='Tổng tiền hàng trước thuế và phí vận chuyển')
    total_amount = models.DecimalField(max_digits=9, decimal_places=0, default=0, help_text='Tổng số tiền của đơn hàng, bao gồm tiền hàng, thuế và phí vận chuyển')

    # Thông tin thanh toán
    METHOD_CHOICES = (
        ('PP', 'PayPal'),
    )
    payment_method = models.CharField(max_length=2, choices=METHOD_CHOICES, default='PP', db_index=True)

    # trạng thái của đơn hàng
    STATUS_CHOICES = (
        ('W', 'Đang chờ xử lý'),
        ('C', 'Đã xác nhận'),
        ('S', 'Đang giao hàng'),
        ('F', 'Đã hoàn thành'),
        ('R', 'Đã hủy'),
        ('X', 'Đang tranh chấp'),
    )
    status = models.CharField(max_length=1, default='W', db_index=True, choices=STATUS_CHOICES, help_text='Trạng thái của đơn hàng.')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # người mua xác nhận đơn hàng thành công, nhận được hàng ok.
    # Nếu không xác nhận thì sau 7 ngày sẽ tự động xác nhận.
    success_confirmed = models.DateTimeField(blank=True, null=True, db_index=True)

    # thông tin nhận hàng đối với người dùng không đăng nhập
    first_name = models.CharField(
        max_length=255,
        help_text='Tên của người nhận hàng',
        verbose_name='Tên'
    )
    last_name = models.CharField(
        max_length=255,
        help_text='Họ của người nhận hàng',
        verbose_name='Họ'
    )
    email = models.EmailField(help_text='Địa chỉ Email của người nhận hàng', verbose_name='Email')
    street = models.CharField(
        max_length=255, help_text='Địa chỉ của người nhận hàng, gồm số nhà và tên đường,...',
        verbose_name='Địa chỉ cụ thể'
    )
    state = models.CharField(
        null=True, blank=True, max_length=255, help_text='Tên quận huyện người nhận hàng đang sống',
        verbose_name='Quận / Huyện'
    )
    city = models.CharField(
        max_length=255, blank=True, help_text='Tên thành phố, thị xã người nhận hàng đang sống',
        verbose_name='Thành Phố / Thị Xã'
    )
    country = models.CharField(max_length=100, help_text='Quốc gia người nhận hàng đang sống')
    zip_code = models.CharField(max_length=10, help_text='Mã bưu chính')
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')

    def __str__(self):
        return f'đơn hàng của {self.user if self.user else "khách"} - {self.code}'

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'status', '-created_at']),
        ]


class OrderItem(models.Model):
    """
    Sản phẩm trong đơn hàng.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items_set', help_text='Đơn hàng mà sản phẩm này thuộc về.')
    variant_product = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.CASCADE, related_name='product_order_items_set', help_text='Sản phẩm trong đơn hàng.')
    quantity = models.IntegerField(default=1, help_text='Số lượng sản phẩm trong đơn hàng.')
    price = models.DecimalField(max_digits=9, decimal_places=0, default=0, help_text='Giá bán của sản phẩm tại thời điểm đặt hàng.')

    def __str__(self):
        return f'{self.order.code}'

