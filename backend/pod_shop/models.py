from django.db import models
from sorl.thumbnail import ImageField as ThumbnailerImageField
from .utils import upload_product_image

# --- Product Color ---
class ProductColor(models.Model):
    """
    Product color model.
    """
    name = models.CharField(max_length=100, verbose_name="Color Name", help_text="Name of the color")
    value = models.CharField(max_length=50, verbose_name="Value", help_text="Value used as id (e.g. color-black)")
    color_code = models.CharField(max_length=10, verbose_name="Color Code", blank=True, help_text="Color code (hex, e.g. #FFFFFF)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Color"
        verbose_name_plural = "Product Colors"

# --- Product Size ---
class ProductSize(models.Model):
    """
    Product size model.
    """
    name = models.CharField(max_length=10, verbose_name="Size Name", help_text="Name of the size")
    value = models.CharField(max_length=20, verbose_name="Value", help_text="Value used as id (e.g. size-xl)")
    order = models.PositiveIntegerField(default=0, verbose_name="Order", help_text="Display order")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Size"
        verbose_name_plural = "Product Sizes"
        ordering = ['order']

# --- Product Color Image ---
class ProductColorImage(models.Model):
    """
    Image for each product color
    """
    color = models.ForeignKey('ProductColor', on_delete=models.CASCADE, related_name='color_images_set')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='product_color_images_set')
    alt = models.CharField(max_length=255, help_text='Alt text for the image')
    image = ThumbnailerImageField(
        upload_to=upload_product_image,
        verbose_name="Image"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Order", help_text="Display order")

    class Meta:
        verbose_name = "Product Color Image"
        verbose_name_plural = "Product Color Images"
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - {self.color.name} - {self.alt}"

# --- Product Variant ---
class ProductVariant(models.Model):
    """
    Product variant model (combination of color and size)
    """
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='variants_product_set',
        verbose_name="Product"
    )
    attr_items = models.ManyToManyField(
        'ProductAttrItem',
        blank=True,
        help_text='Các giá trị thuộc tính của biến thể'
    )
    code = models.CharField(
        max_length=128,
        unique=True,
        verbose_name="SKU",
        editable=False,
        help_text="SKU for this variant. Auto-generated."
    )
    price_origin = models.FloatField(null=True, blank=True, verbose_name="Variant Price", help_text="Original price of the variant")
    price_promo = models.FloatField(null=True, blank=True, verbose_name="Variant Promo Price", help_text="Promo price of the variant")

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        # unique_together sẽ dựa trên product và các attr_items, cần custom validation

    def __str__(self):
        attrs = ', '.join([item.label for item in self.attr_items.all()])
        return f"{self.product.name} - {attrs}"

    def is_sale(self):
        return self.price_promo is not None

    def get_price(self):
        return self.price_promo if self.price_promo else self.price_origin

    def save(self, *args, **kwargs):
    # Sinh SKU động: product.code + '_' + các giá trị thuộc tính
        product_code = self.product.code if self.product and self.product.code else "P0000000"
        # Ensure stable order: sort by attribute name then item order/id
        ordered_items = self.attr_items.all().select_related('attr').order_by('attr__name', 'attr_order', 'id')
        attr_values = [item.value for item in ordered_items]
        sku = f"{product_code}_{'_'.join(attr_values)}" if attr_values else product_code
        base_sku = sku
        i = 1
        while ProductVariant.objects.filter(code=sku).exclude(pk=self.pk).exists():
            sku = f"{base_sku}_{i}"
            i += 1
        self.code = sku
        super().save(*args, **kwargs)
from autoslug import AutoSlugField
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse

from pod_shop.utils import upload_product_image, upload_product_category_image, upload_product_brand_image
from utils.common import build_full_url

UserModel = get_user_model()


class Product(models.Model):
    def save(self, *args, **kwargs):
        # Lưu sản phẩm trước để có code
        super().save(*args, **kwargs)
        # Sau khi tạo mới Product, cập nhật lại SKU cho các biến thể liên quan
        for variant in self.variants_product_set.all():
            # Regenerate variant SKU based on current product code and variant attr_items
            # Logic for SKU composition lives in ProductVariant.save()
            variant.save()
    """
    Sản phẩm.
    """
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name='cat_products')
    tags = models.ManyToManyField('Tag', blank=True, related_name='tag_products')
    code = models.CharField(max_length=8, unique=True, blank=True, help_text='Mã sản phẩm, ví dụ: "P1234567"')

    name = models.CharField(max_length=500)
    slug = AutoSlugField(populate_from='name', unique=True, editable=True, blank=True, max_length=500)
    desc = models.TextField(blank=True, help_text='HTML for SEO')
    desc_short = models.TextField(blank=True, help_text='Mô tả ngắn gọn về sản phẩm')

    STATUS_CHOICES = (
        ('D', 'Nháp'),
        ('A', 'Đang Bán'),
        ('O', 'Hết Hàng'),
    )
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='D', db_index=True)

    fake_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Giá gạch', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Giá bán')

    standard_shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=4.95,
                                                help_text='Phí vận chuyển tiêu chuẩn cho sản phẩm này')
    fast_shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=12.95,
                                            help_text='Phí vận chuyển nhanh cho sản phẩm này')

    created_at = models.DateTimeField(auto_now_add=True, help_text='Thời gian tạo sản phẩm')
    updated_at = models.DateTimeField(auto_now=True, help_text='Thời gian cập nhật sản phẩm')

    best_seller = models.BooleanField(default=False, help_text='Đánh dấu sản phẩm là bán chạy nhất')
    is_featured = models.BooleanField(default=False, help_text='Đánh dấu sản phẩm là nổi bật')
    times_purchased = models.PositiveIntegerField(
        blank=True, null=True,
        verbose_name='Số lần sản phẩm được mua',
        default=0,
        help_text='Số lần sản phẩm được mua.'
    )

    # Thông tin SEO
    meta_title = models.CharField(
        blank=True, max_length=60,
        help_text='Tiêu đề SEO cho sản phẩm tối đa 60 ký tự. Nếu để trống thì sẽ hệ thống sẽ tự động lấy từ tên sản phẩm.'
    )
    meta_desc = models.CharField(
        blank=True, max_length=145,
        help_text='Mô tả SEO cho sản phẩm, tối đa 145 ký tự. Nếu để trống thì sẽ hệ thống sẽ tự động lấy từ mô tả.'
    )

    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')

    # Chọn các thuộc tính dùng cho sản phẩm này (được định nghĩa toàn cục hoặc riêng lẻ)
    available_attrs = models.ManyToManyField(
        'ProductAttr',
        related_name='products_using',
        blank=True,
        help_text='Các thuộc tính áp dụng cho sản phẩm này (ví dụ: Size, Color, Type, ...).'
    )

    def __str__(self):
        return f"{self.name} - {self.brand.name}"

    def related_products(self, limit=8):
        """
        Sản phẩm liên quan — match tags hoặc category, ưu tiên best-seller
        và mới nhất, có shuffle để mỗi lần page regen có variety.

        Ranking:
          1. status='A' AND (chia sẻ ≥1 tag OR cùng category) AND ≠ self
          2. order by times_purchased DESC, created_at DESC
          3. lấy top (limit*2) → shuffle → trả về `limit` đầu

        Pool = limit*2 đảm bảo các sản phẩm trả về vẫn nằm trong "top
        relevant", random shuffle chỉ tạo variety trong nhóm đó.
        """
        import random
        pool = list(
            Product.objects.filter(
                (Q(tags__in=self.tags.all()) | Q(category=self.category)) & ~Q(id=self.id),
                status='A',
            )
            .distinct()
            .order_by('-times_purchased', '-created_at')[: limit * 2]
        )
        random.shuffle(pool)
        return pool[:limit]

    def percentage_discount(self):
        """
        Tính toán phần trăm giảm giá dựa trên giá gốc và giá bán.
        Nếu giá gốc không có, trả về None.
        """
        if self.fake_price and self.fake_price > 0:
            return round((self.fake_price - self.price) / self.fake_price * 100, 2)
        return None

    def product_review_count(self):
        """
        Trả về số lượng đánh giá của sản phẩm (chỉ tính review đã được duyệt).
        """
        return self.product_review_set.filter(status=True).count()

    def product_average_rating(self):
        """
        Trả về điểm đánh giá trung bình của sản phẩm (chỉ tính review đã được duyệt).
        """
        reviews = self.product_review_set.filter(status=True)
        if not reviews.exists():
            return 0.0
        
        total_sum = reviews.aggregate(total=models.Sum('rating'))['total'] or 0
        count = reviews.count()
        
        if count > 0:
            return round(total_sum / count, 1)
        return 0.0

    def is_sale(self):
        """
        Kiểm tra xem sản phẩm có đang được giảm giá hay không.
        """
        return self.fake_price is not None and self.fake_price > self.price

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết sản phẩm.
        """
        return reverse('pod_shop:product_detail', args=[self.slug])

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết sản phẩm.
        Ví dụ: /p/<product>
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết sản phẩm.
        """
        if self.slug:
            return build_full_url(self.url())
        return ''


class ProductSlugAlias(models.Model):
    """Historical slugs that should 301-redirect to the product's current slug.

    Populated by `admin_product_update` whenever an admin changes a product's
    slug — the prior slug is captured here so /p/<old>/ keeps working via a
    301 from the Next.js middleware. Without this, renaming a slug would 404
    every URL Google had previously indexed for that product.
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='slug_aliases',
    )
    old_slug = models.CharField(max_length=500, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Product slug alias'
        verbose_name_plural = 'Product slug aliases'

    def __str__(self):
        return f'{self.old_slug} → {self.product.slug}'


class ProductAttr(models.Model):
    """
    Thuộc tính của sản phẩm, ví dụ: "Size", "Color..."
    Có thể là toàn cục (product = null) hoặc gắn với một sản phẩm cụ thể.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes', null=True, blank=True)
    name = models.CharField(
        max_length=100,
        help_text='Tên thuộc tính, ví dụ: "Size", "Color", "Gender", "Material", "Choose Your Style",...'
    )

    def __str__(self):
        prod_name = self.product.name if self.product else 'Global'
        return f"{prod_name} - {self.name}"


class ProductAttrItem(models.Model):
    """
    Giá trị của thuộc tính sản phẩm, ví dụ: "XL", "Red Devil", "Blue Sky"...
        Giá trị của biến thể, danh sách của các giá trị, ví dụ:
        [{
            "label": "XL",
            "value": "xl",
            "extra": ""
        },...]
        hoặc
        [{
            "label": "Red Devil",
            "value": "red-devil",
            "extra": "#800011"
        },...]
    """
    # ta có thể lấy Product từ ProductAttr, nhưng để tránh việc phải truy vấn nhiều lần,
    # ta sẽ lưu lại Product ở đây để truy vấn nhanh hơn
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, related_name='+', null=True, blank=True)

    attr = models.ForeignKey(ProductAttr, on_delete=models.CASCADE, related_name='product_attr_items')
    label = models.CharField(max_length=100, help_text='Tên hiển thị của giá trị thuộc tính, '
                                                       'ví dụ: "XL", "Red Devil", "Blue Sky"...')
    value = AutoSlugField(
        populate_from='label',
        unique_with=('product', 'attr'),
        editable=True,
        blank=True
    )
    extra = models.CharField(max_length=200, blank=True, help_text='Thông tin bổ sung, ví dụ: mã màu')
    attr_order = models.PositiveIntegerField(
        default=0,
        help_text='Thứ tự hiển thị của thuộc tính trong danh sách, từ nhỏ đến lớn.'
    )

    def __str__(self):
        prod_name = self.product.name if self.product else 'Global'
        return f"{prod_name} - {self.attr.name} - {self.label}"


class ProductImage(models.Model):
    """
    Hình ảnh của sản phẩm. Ảnh có thể lưu ở GCS (image field) hoặc là URL
    external (image_url field) — admin dán URL trực tiếp từ /acp/ Media Library.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = ThumbnailerImageField(
        blank=True,
        upload_to=upload_product_image,
    )
    # External URL of an already-uploaded image (e.g. /images/<slug>-1.jpg).
    # Either `image` or `image_url` is populated per row.
    image_url = models.URLField(blank=True, max_length=1000)
    # thứ tự ưu tiên hiển thị ảnh, từ nhỏ đến lớn
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    removed = models.BooleanField(default=False)

    def get_url(self):
        """Public URL of this image — prefers explicit image_url when set."""
        if self.image_url:
            return self.image_url
        return self.image.url if self.image else ''

    def __str__(self):
        return f"Hình ảnh cho {self.product.name}"

    def get_thumb_by_width(self, width=1200):
        """
        Lấy ảnh thumbnail theo chiều rộng, đảm bảo tỉ lệ của ảnh gốc.
        """
        if not self.image:
            return ''
        if width >= 1200:
            return self.image.url
        # lấy tỉ lệ của ảnh gốc
        ratio = self.image.width / self.image.height
        new_height = int(width / ratio)
        option_dict = {
            'size': (width, new_height),
            'width': width,
            'height': new_height,
            'crop': True,
            'upscale': True,
        }
        # Fix lỗi: chỉ gọi get_thumbnail nếu tồn tại
        if hasattr(self.image, 'get_thumbnail'):
            return self.image.get_thumbnail(option_dict).url
        return self.image.url


class Brand(models.Model):
    """
    Thương hiệu.
    """
    name = models.CharField(max_length=100, unique=True)
    desc = models.TextField(blank=True, help_text='HTML for SEO')
    slug = AutoSlugField(populate_from='name', unique=True, editable=True, blank=True, max_length=500)
    logo = ThumbnailerImageField(
        blank=True,
        upload_to=upload_product_brand_image,
        help_text='Hình ảnh logo thương hiệu.',
    )
    # External URL for the logo (so admin can paste a URL from /acp/
    # Media Library instead of uploading a file).
    logo_url = models.URLField(blank=True, max_length=1000)
    # Optional league/grouping label used by the Brands mega-menu.
    league = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=1, help_text='Thứ tự hiển thị thương hiệu trong danh sách, từ nhỏ đến lớn.')

    def get_logo_url(self):
        """Public URL of the brand logo — prefers the explicit logo_url."""
        if self.logo_url:
            return self.logo_url
        try:
            return self.logo.url if self.logo else ''
        except Exception:
            return ''

    def __str__(self):
        return self.name

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết thương hiệu.
        """
        return reverse('pod_shop:brand_detail', args=[self.slug])

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết thương hiệu.
        Ví dụ: /b/<brand>
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết thương hiệu.
        """
        if self.slug:
            return build_full_url(self.url())
        return ''


class Category(models.Model):
    """
    Danh mục sản phẩm.
    """
    name = models.CharField(max_length=100, unique=True)
    desc = models.TextField(blank=True, help_text='HTML for SEO')
    slug = AutoSlugField(populate_from='name', unique=True, editable=True, blank=True, max_length=500)
    image = ThumbnailerImageField(
        blank=True,
        upload_to=upload_product_category_image,
        help_text='Hình ảnh đại diện cho danh mục sản phẩm.'
    )
    order = models.PositiveIntegerField(default=1, help_text='Thứ tự hiển thị danh mục trong danh sách, từ nhỏ đến lớn.')

    def __str__(self):
        return self.name

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết danh mục sản phẩm.
        """
        return reverse('pod_shop:category_detail', args=[self.slug])

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết danh mục sản phẩm.
        Ví dụ: /c/<category>
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết danh mục sản phẩm.
        """
        if self.slug:
            return build_full_url(self.url())
        return ''


class Tag(models.Model):
    """
    Thẻ gắn cho sản phẩm. Ví dụ: "hiking", "rain-proof", "lightweight"...
    """
    name = models.CharField(max_length=100, unique=True)
    desc = models.TextField(blank=True, help_text='HTML for SEO')
    slug = AutoSlugField(populate_from='name', unique=True, editable=True, blank=True, max_length=500)

    def __str__(self):
        return self.name

    def url(self):
        """
        Trả về đường dẫn tới trang chi tiết tags sản phẩm.
        """
        return reverse('pod_shop:tags_detail', args=[self.slug])

    def get_absolute_url(self):
        """
        Trả về đường dẫn tới trang chi tiết tags sản phẩm.
        Ví dụ: /t/<tags>
        """
        return self.url()

    def full_url(self):
        """
        Trả về đường dẫn đầy đủ tới trang chi tiết tags sản phẩm.
        """
        if self.slug:
            return build_full_url(self.url())
        return ''


class CartItem(models.Model):
    """
    Mô hình giỏ hàng, dùng để lưu trữ các sản phẩm trong giỏ hàng của người dùng.
    """
    user = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        related_name='cart_items',
        help_text='Người dùng sở hữu giỏ hàng (nếu có, nếu không thì là khách vãng lai)',
        blank=True, null=True,
    )

    # New: Link to ProductVariant for advanced variant support
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.SET_NULL,
        related_name='cart_items',
        blank=True, null=True,
        help_text='Selected product variant (if any)'
    )

    quantity = models.PositiveIntegerField(default=1)
    customer_note = models.CharField(blank=True, help_text='Ghi chú của khách hàng về sản phẩm khi mua')
    order = models.PositiveIntegerField(default=0, help_text='Lớn hơn thì lên trước trong giỏ hàng')

    attr_items = models.ManyToManyField(
        ProductAttrItem,
        related_name='+',
        blank=True,
        help_text='Thuộc tính sản phẩm đã chọn (nếu có)'
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text='Thời gian tạo giỏ hàng')
    updated_at = models.DateTimeField(auto_now=True, help_text='Thời gian cập nhật giỏ hàng')

    removed = models.BooleanField(default=False, help_text='Đánh dấu sản phẩm đã bị xóa khỏi giỏ hàng')


    def __str__(self):
        attrs = ", ".join(a.label for a in self.attr_items.all())
        variant_str = f" | Variant: {self.variant}" if self.variant else ""
        return f"{self.quantity} x {self.product.name}{variant_str} [{attrs}]"


    @property
    def line_total(self):
        # Use variant price if available, else fallback to product price
        if self.variant:
            return (self.variant.get_price() or self.product.price) * self.quantity
        return self.product.price * self.quantity


class Order(models.Model):
    """
    Đơn hàng được đặt.
    """
    user = models.ForeignKey(
        UserModel,
        on_delete=models.SET_NULL,
        related_name='orders',
        help_text='Người dùng đã đặt hàng (nếu có, nếu không thì là khách vãng lai)',
        blank=True, null=True,
    )
    code = models.CharField(max_length=20, unique=True, blank=True, help_text='Mã đơn hàng, ví dụ: "ORDER12345678"')
    sub_total = models.DecimalField(max_digits=9, decimal_places=2, default=0, help_text='Tổng tiền hàng trước thuế và phí vận chuyển')
    shipping_fee = models.DecimalField(max_digits=9, decimal_places=2, default=0, help_text='Phí vận chuyển cho đơn hàng')
    total_amount = models.DecimalField(max_digits=9, decimal_places=2, default=0, help_text='Tổng số tiền của đơn hàng, bao gồm tiền hàng, thuế và phí vận chuyển')

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
        """
        Trả về mã đơn hàng hoặc tên người dùng nếu có.
        """
        if self.user:
            return f"Đơn hàng #{self.code} của {self.user.username}"
        return f"Đơn hàng #{self.code} của Khách"


class OrderItem(models.Model):
    """
    Mô hình sản phẩm trong đơn hàng.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.SET_NULL,
        related_name='order_items',
        blank=True, null=True,
        help_text='Selected product variant (if any)'
    )
    quantity = models.PositiveIntegerField(default=1)
    attr_item = models.ManyToManyField(
        ProductAttrItem,
        related_name='attr_order_items',
        blank=True,
        help_text='Thuộc tính sản phẩm đã chọn (nếu có)'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Giá của sản phẩm tại thời điểm đặt hàng')

    created_at = models.DateTimeField(auto_now_add=True, help_text='Thời gian tạo sản phẩm trong đơn hàng')
    updated_at = models.DateTimeField(auto_now=True, help_text='Thời gian cập nhật sản phẩm trong đơn hàng')

    customer_note = models.TextField(blank=True, null=True, help_text='Ghi chú của khách hàng cho sản phẩm')


    def __str__(self):
        variant_str = f" | Variant: {self.variant}" if self.variant else ""
        return f"{self.quantity} x {self.product.name}{variant_str} trong đơn hàng {self.order.code}"

    def get_customer_note(self):
        return self.customer_note or ''


class WishList(models.Model):
    """
    Người dùng thích sản phẩm.
    """
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='user_wishlists', help_text='Người dùng thích sản phẩm.')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_wishlists', help_text='Sản phẩm được người dùng thích.')
    created_at = models.DateTimeField(auto_now_add=True)
    removed = models.BooleanField(default=False, help_text='Đánh dấu sản phẩm đã bị xóa khỏi danh sách yêu thích hay chưa.')

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'


class Review(models.Model):
    """
    Mô hình đánh giá sản phẩm.
    """
    user = models.ForeignKey(
        UserModel, on_delete=models.SET_NULL,
        related_name='user_review_set',
        help_text='Người dùng đánh giá.',
        null=True, blank=True,  # Cho phép người dùng chưa đăng nhập cũng có thể đánh giá sản phẩm (ẩn danh).
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,  # Nếu sản phẩm bị xóa thì đánh giá của sản phẩm cũng bị xóa theo.
        related_name='product_review_set',
        help_text='Sản phẩm được đánh giá.'
    )
    reviewer_name = models.CharField(
        max_length=255, 
        blank=True,
        help_text='Tên người đánh giá (bắt buộc nếu không đăng nhập)'
    )
    rating = models.PositiveIntegerField(help_text='Điểm đánh giá của sản phẩm, từ 1 đến 5 sao.')
    subject = models.CharField(max_length=100, blank=True, help_text='Tiêu đề review')
    content = models.TextField(blank=True, help_text='Nội dung review.')
    content_safe = models.TextField(blank=True, help_text='Nội dung review (safe).')
    ip_review = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=False, help_text='Trạng thái đánh giá, True: Đã duyệt, False: Chưa duyệt')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Thời gian tạo đánh giá.')
    updated_at = models.DateTimeField(auto_now_add=True, help_text='Thời gian cập nhật đánh giá.')
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')
    wp_review_id = models.BigIntegerField(
        null=True, blank=True, unique=True,
        help_text='ID của review tương ứng trên WP/.shop. Dùng để dedup khi import và để khóa cặp .com↔.shop.'
    )

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


class BulkReview(models.Model):
    """
    Mô hình review hàng loạt cho admin.
    Admin có thể tạo nhiều review ẩn danh với tên random từ danh sách người Mỹ.
    Khi lưu, sẽ tự động tạo các Review thật với tên ngẫu nhiên.
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='product_bulk_review_set',
        help_text='Sản phẩm được đánh giá hàng loạt.'
    )
    rating = models.PositiveIntegerField(
        help_text='Điểm đánh giá (1-5 sao) cho tất cả các review trong lô này.',
        choices=[(i, f'{i} sao') for i in range(1, 6)]
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text='Số lượng review sẽ được tạo với tên ngẫu nhiên.'
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text='Thời gian tạo bulk review.')
    updated_at = models.DateTimeField(auto_now=True, help_text='Thời gian cập nhật bulk review.')
    admin_notes = models.TextField(blank=True, help_text='Ghi chú của quản trị viên.')

    class Meta:
        verbose_name = "Bulk Review (Review Hàng Loạt)"
        verbose_name_plural = "Bulk Reviews (Review Hàng Loạt)"

    def __str__(self):
        return f"{self.product.name} - {self.rating} sao x {self.quantity} review"

    def save(self, *args, **kwargs):
        """
        Ghi đè phương thức save.
        Nếu đây là bulk review mới, tạo các Review thật với tên random.
        """
        import random
        from pod_shop.american_names import AMERICAN_NAMES
        
        is_new = self.pk is None
        super(BulkReview, self).save(*args, **kwargs)
        
        if is_new:
            # Tạo các review với tên random từ danh sách
            for _ in range(self.quantity):
                random_name = random.choice(AMERICAN_NAMES)
                Review.objects.create(
                    product=self.product,
                    reviewer_name=random_name,
                    rating=self.rating,
                    status=True,  # Tự động duyệt
                    subject='',
                    content='',
                    content_safe='',
                    ip_review='',
                    admin_notes=f'Auto-generated from BulkReview #{self.pk}'
                )
        
        self.product.save()

    def delete(self, *args, **kwargs):
        """
        Ghi đè phương thức delete.
        Xóa các review đã tạo từ bulk review này.
        """
        product = self.product
        # Xóa các review được tạo từ bulk review này
        Review.objects.filter(
            product=self.product,
            admin_notes__contains=f'Auto-generated from BulkReview #{self.pk}'
        ).delete()
        super(BulkReview, self).delete(*args, **kwargs)
        product.save()


class CMSContent(models.Model):
    """Singleton row holding the CMS payload (home/footer/seo/menu) as JSON.

    The FE admin /admin/ page reads + writes this through Django, replacing
    the old Vercel Blob storage. One row, fixed PK = SINGLETON_ID.
    """
    SINGLETON_ID = 1
    id = models.PositiveSmallIntegerField(primary_key=True, default=SINGLETON_ID)
    payload = models.JSONField(default=dict, blank=True, help_text='Toàn bộ CMS content (home/footer/seo/menu) dạng JSON.')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CMS Content'
        verbose_name_plural = 'CMS Content'

    def __str__(self):
        return f'CMSContent (updated {self.updated_at:%Y-%m-%d %H:%M})'

    def save(self, *args, **kwargs):
        # Force singleton — always pk=1
        self.pk = self.SINGLETON_ID
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_ID)
        return obj