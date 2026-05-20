# path: myshop/api/serializers.py

from django.conf import settings
from django.template.defaultfilters import truncatechars
from django.templatetags.static import static
from django.utils.html import strip_tags
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from myshop.models import (ProductImage, Product, Category, Brand, Tag, Review,
                           ProductVariant, ProductColor, ProductSize, ProductColorImage, WishList, CartItem, OrderItem,
                           Order)
from utils.api.common import OpenGraphSerializer
from utils.common import build_media_url, safe_static


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer cho danh mục sản phẩm
    """
    class Meta:
        model = Category
        fields = (
            'name', 'slug', 'url', 'full_url'
        )


class BrandSerializer(serializers.ModelSerializer):
    """
    Serializer cho thương hiệu sản phẩm
    """
    class Meta:
        model = Brand
        fields = (
            'name', 'slug', 'url', 'full_url'
        )


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer cho tag sản phẩm
    """
    class Meta:
        model = Tag
        fields = (
            'name', 'slug', 'url', 'full_url'
        )


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Serializer cho danh sách danh mục sản phẩm
    """
    num_product = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_num_product(self, obj: Category):
        return Product.objects.filter(is_available=True, category=obj).count()

    class Meta:
        model = Category
        fields = (
            'name', 'slug', 'desc_safe', 'img', 'order',
            'url', 'full_url', 'num_product',
        )


class ProductCategoryListSerializer(serializers.ModelSerializer):
    """
    Serializer cho chi tiết danh mục sản phẩm
    """
    open_graph = serializers.SerializerMethodField()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj: Category):
        default_og_image = safe_static('img/default-og-image.jpg')
        images = (
            [build_media_url(obj.img.url)] if obj.img else [default_og_image]
        )

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
            'images': images,
            'url': obj.full_url()
        }

    class Meta:
        model = Category
        fields = (
            'name', 'slug', 'desc_safe', 'img',
            'url', 'full_url', 'open_graph',
        )


class BrandListSerializer(serializers.ModelSerializer):
    """
    Serializer cho danh sách thương hiệu sản phẩm
    """
    num_product = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_num_product(self, obj: Brand):
        return Product.objects.filter(is_available=True, brand=obj).count()

    class Meta:
        model = Brand
        fields = (
            'name', 'slug', 'logo', 'order',
            'url', 'full_url', 'num_product',
        )


class ProductBrandListSerializer(serializers.ModelSerializer):
    """
    Serializer cho chi tiết thương hiệu sản phẩm
    """
    open_graph = serializers.SerializerMethodField()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj: Brand):
        default_og_image = safe_static('img/default-og-image.jpg')
        images = (
            [build_media_url(obj.logo.url)] if obj.logo else [default_og_image]
        )

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
            'images': images,
            'url': obj.full_url()
        }

    class Meta:
        model = Brand
        fields = (
            'name', 'slug', 'logo',
            'url', 'full_url', 'open_graph',
        )


class TagListSerializer(serializers.ModelSerializer):
    """
    Serializer cho danh sách tag sản phẩm
    """
    num_product = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_num_product(self, obj):
        return Product.objects.filter(is_available=True, tags=obj).count()

    class Meta:
        model = Tag
        fields = (
            'name', 'slug', 'num_product',
        )


class ProductTagListSerializer(serializers.ModelSerializer):
    """
    Serializer cho chi tiết tag sản phẩm
    """
    open_graph = serializers.SerializerMethodField()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj: Tag):
        default_og_image = safe_static('img/default-og-image.jpg')

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

    class Meta:
        model = Tag
        fields = (
            'name', 'slug', 'url', 'full_url', 'open_graph',
        )


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer cho sản phẩm
    """
    brand = BrandSerializer()
    category = CategorySerializer()
    tags = TagSerializer(many=True)
    preview_picture = serializers.SerializerMethodField()
    sale_percentage = serializers.SerializerMethodField()
    variants_by_color = serializers.SerializerMethodField()
    color_images = serializers.SerializerMethodField()
    product_review_count = serializers.SerializerMethodField()
    product_average_rating = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_preview_picture(self, obj: Product):
        """
        Lấy URL của hình ảnh mặc định
        """
        img = obj.product_images_set.filter(removed=False).order_by('order').first()
        return {
            'w200': img.get_thumb_by_width(width=200) if img else '',
            'w400': img.get_thumb_by_width(width=400) if img else '',
            'w800': img.get_thumb_by_width(width=800) if img else '',
        }

    @extend_schema_field(serializers.CharField)
    def get_sale_percentage(self, obj):
        """
        Lấy tỷ lệ giảm giá
        """
        return obj.calculate_sale_percentage()

    @extend_schema_field(serializers.CharField)
    def get_variants_by_color(self, obj):
        """
        Lấy danh sách biến thể sản phẩm theo màu sắc
        """
        result = {}
        variants = ProductVariant.objects.filter(product=obj).select_related('color', 'size')

        for variant in variants:
            color_value = variant.color.value
            if color_value not in result:
                result[color_value] = {
                    'color': ProductColorSerializer(variant.color).data,
                    'sizes': []
                }

            result[color_value]['sizes'].append({
                'size': ProductSizeSerializer(variant.size).data,
                'sku': variant.code,
                'price_origin': variant.price_origin,
                'price_promo': variant.price_promo,
            })

        return result

    @extend_schema_field(serializers.CharField)
    def get_color_images(self, obj):
        """
        Lấy danh sách hình ảnh theo màu sắc
        """
        return obj.get_color_images()

    @extend_schema_field(serializers.IntegerField())
    def get_product_review_count(self, obj: Product):
        """
        Lấy số lượng đánh giá sản phẩm
        """
        return obj.product_review_count()

    @extend_schema_field(serializers.FloatField())
    def get_product_average_rating(self, obj: Product):
        """
        Lấy đánh giá trung bình của sản phẩm
        """
        return obj.product_average_rating()

    @extend_schema_field(serializers.BooleanField())
    def get_is_wishlisted(self, obj: Product):
        """
        Kiểm tra xem sản phẩm có trong danh sách yêu thích của người dùng hay không
        """
        user = self.context.get('user')
        if user and user.is_authenticated:
            qs = WishList.objects.filter(product=obj, removed=False, user=user)
            return qs.exists()
        return False

    class Meta:
        model = Product
        fields = (
            'name', 'slug', 'code', 'desc_short_safe', 'desc_safe', 'price_origin', 'preview_picture',
            'price_promo', 'is_available', 'category', 'brand', 'tags', 'url', 'full_url',
            'is_sale', 'sale_percentage', 'times_purchased', 'color_images', 'variants_by_color',
            'product_review_count', 'product_average_rating', 'is_wishlisted'
        )


class PhotoGallerySerializer(serializers.Serializer):
    """
    Serializer cho bộ sưu tập ảnh
    """
    class Meta:
        fields = (
            'key', 'src', 'width', 'height'
        )

    key = serializers.ReadOnlyField()
    src = serializers.CharField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class ProductPictureSerializer(serializers.ModelSerializer):
    """
    Serializer cho hình ảnh sản phẩm
    """
    image_url = serializers.SerializerMethodField()
    image_thumb_url = serializers.SerializerMethodField()
    dimension = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_image_url(self, obj: ProductImage):
        return build_media_url(obj.img.url)

    @extend_schema_field(serializers.CharField)
    def get_image_thumb_url(self, obj: ProductImage):
        return build_media_url(obj.get_thumb_by_width(width=400))

    @extend_schema_field(serializers.CharField)
    def get_dimension(self, obj: ProductImage):
        return f'{obj.img.width}x{obj.img.height}'

    @extend_schema_field(serializers.IntegerField)
    def get_size(self, obj: ProductImage):
        return obj.img.size

    class Meta:
        model = ProductImage
        fields = (
            'id', 'order', 'created_at',
            'image_url', 'image_thumb_url',
            'dimension', 'size'
        )


class ProductColorSerializer(serializers.ModelSerializer):
    """
    Serializer cho màu sắc sản phẩm
    """
    class Meta:
        model = ProductColor
        fields = ['name', 'value', 'color_code']


class ProductSizeSerializer(serializers.ModelSerializer):
    """
    Serializer cho kích thước sản phẩm
    """
    class Meta:
        model = ProductSize
        fields = ['name', 'value', 'order']


class ProductColorImageSerializer(serializers.ModelSerializer):
    """
    Serializer cho hình ảnh màu sắc sản phẩm
    """
    url = serializers.SerializerMethodField()
    color = ProductColorSerializer()

    class Meta:
        model = ProductColorImage
        fields = [ 'alt', 'url', 'color', 'order']

    @extend_schema_field(serializers.CharField)
    def get_url(self, obj):
        if obj.image:
            return build_media_url(obj.image.url)
        return ''


class ProductInCartSerializer(serializers.ModelSerializer):
    """
    Serializer cho sản phẩm trong giỏ hàng
    """
    brand = BrandSerializer()
    category = CategorySerializer()
    tags = TagSerializer(many=True)
    preview_picture = serializers.SerializerMethodField()
    sale_percentage = serializers.SerializerMethodField()
    product_review_count = serializers.SerializerMethodField()
    product_average_rating = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_preview_picture(self, obj: Product):
        """
        Lấy URL của hình ảnh mặc định
        """
        img = obj.product_images_set.filter(removed=False).order_by('order').first()
        return {
            'w200': img.get_thumb_by_width(width=200) if img else '',
            'w400': img.get_thumb_by_width(width=400) if img else '',
            'w800': img.get_thumb_by_width(width=800) if img else '',
        }

    @extend_schema_field(serializers.CharField)
    def get_sale_percentage(self, obj):
        """
        Lấy tỷ lệ giảm giá
        """
        return obj.calculate_sale_percentage()

    @extend_schema_field(serializers.IntegerField())
    def get_product_review_count(self, obj: Product):
        """
        Lấy số lượng đánh giá sản phẩm
        """
        return obj.product_review_count()

    @extend_schema_field(serializers.FloatField())
    def get_product_average_rating(self, obj: Product):
        """
        Lấy đánh giá trung bình của sản phẩm
        """
        return obj.product_average_rating()

    @extend_schema_field(serializers.BooleanField())
    def get_is_wishlisted(self, obj: Product):
        """
        Kiểm tra xem sản phẩm có trong danh sách yêu thích của người dùng hay không
        """
        user = self.context.get('user')
        if user and user.is_authenticated:
            qs = WishList.objects.filter(product=obj, removed=False, user=user)
            return qs.exists()
        return False

    class Meta:
        model = Product
        fields = (
            'name', 'slug', 'code', 'desc_short_safe', 'desc_safe', 'price_origin', 'preview_picture',
            'price_promo', 'is_available', 'category', 'brand', 'tags', 'url', 'full_url',
            'is_sale', 'sale_percentage', 'times_purchased',
            'product_review_count', 'product_average_rating', 'is_wishlisted'
        )


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Serializer cho biến thể sản phẩm
    """
    color = ProductColorSerializer()
    size = ProductSizeSerializer()
    product = ProductInCartSerializer()

    class Meta:
        model = ProductVariant
        fields = [
             'code', 'color', 'size',
            'price_origin', 'price_promo', 'product'
        ]

    @extend_schema_field(serializers.CharField)
    def get_price(self, obj):
        return obj.get_price()


class ProductReviewSerializer(serializers.ModelSerializer):
    """
    Serializer cho đánh giá sản phẩm
    """
    profile = serializers.SerializerMethodField(source='profile_review_set')
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    @extend_schema_field(serializers.CharField)
    def get_profile(self, obj):
        if obj.profile and obj.profile.user:
            return {
                'username': obj.profile.user.username,
                'full_name': obj.profile.full_name()
            }
        else:
            return {
                'username': 'anonymous',
                'full_name': 'Anonymous User'
            }

    class Meta:
        model = Review
        fields = ('code', 'profile', 'rating', 'subject', 'content_safe', 'created_at')


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer cho chi tiết sản phẩm
    """
    open_graph = serializers.SerializerMethodField()
    brand = BrandSerializer()
    category = CategorySerializer()
    tags = TagSerializer(many=True)
    related_products = serializers.SerializerMethodField()
    cross_sell = serializers.SerializerMethodField()
    variants_by_color = serializers.SerializerMethodField()
    color_images = serializers.SerializerMethodField()
    product_review_count = serializers.SerializerMethodField()
    product_average_rating = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj: Product):
        default_og_image = safe_static('img/default-og-image.jpg')
        img = obj.product_images_set.filter(removed=False).exclude(img='').order_by('order').first()
        images = [img.get_thumb_by_width(width=800)] if img else [default_og_image]

        # Lấy tiêu đề và mô tả Open Graph
        title = obj.meta_title if obj.meta_title else obj.name
        desc = (
            obj.meta_desc if obj.meta_desc
            else truncatechars(strip_tags(obj.desc), 145)
            if obj.desc else settings.SITE_DESC
        )

        return {
            'title': title,
            'description': desc,
            'images': images,
            'url': obj.full_url()
        }

    @extend_schema_field(serializers.CharField)
    def get_related_products(self, obj: Product):
        """
        Lấy danh sách sản phẩm liên quan
        """
        user = self.context.get('user')
        if user and user.is_authenticated:
            return ProductSerializer(obj.related_products(), many=True, context={'user': user}).data
        return ProductSerializer(obj.related_products(), many=True).data

    @extend_schema_field(serializers.CharField)
    def get_cross_sell(self, obj: Product):
        """
        Lấy danh sách sản phẩm bán kèm
        """
        user = self.context.get('user')
        if user and user.is_authenticated:
            return ProductSerializer(obj.cross_sell.all(), many=True, context={'user': user}).data
        return ProductSerializer(obj.cross_sell.all(), many=True).data

    @extend_schema_field(serializers.CharField)
    def get_variants_by_color(self, obj):
        """
        Lấy danh sách biến thể sản phẩm theo màu sắc
        """
        result = {}
        variants = ProductVariant.objects.filter(product=obj).select_related('color', 'size')

        for variant in variants:
            color_value = variant.color.value
            if color_value not in result:
                result[color_value] = {
                    'color': ProductColorSerializer(variant.color).data,
                    'sizes': []
                }

            result[color_value]['sizes'].append({
                'size': ProductSizeSerializer(variant.size).data,
                'sku': variant.code,
                'price_origin': variant.price_origin,
                'price_promo': variant.price_promo,
            })

        return result

    @extend_schema_field(serializers.CharField)
    def get_color_images(self, obj):
        """
        Lấy danh sách hình ảnh theo màu sắc
        """
        return obj.get_color_images()

    @extend_schema_field(serializers.IntegerField())
    def get_product_review_count(self, obj: Product):
        """
        Lấy số lượng đánh giá sản phẩm
        """
        return obj.product_review_count()

    @extend_schema_field(serializers.FloatField())
    def get_product_average_rating(self, obj: Product):
        """
        Lấy đánh giá trung bình của sản phẩm
        """
        return obj.product_average_rating()

    @extend_schema_field(serializers.BooleanField())
    def get_is_wishlisted(self, obj: Product):
        """
        Kiểm tra xem sản phẩm có trong danh sách yêu thích của người dùng hay không
        """
        user = self.context.get('user')
        if user and user.is_authenticated:
            qs = WishList.objects.filter(product=obj, removed=False, user=user)
            return qs.exists()
        return False

    class Meta:
        model = Product
        fields = (
            'name', 'slug', 'code', 'desc_short_safe', 'color_images',
            'desc_safe', 'seller_notes_safe', 'price_origin', 'price_promo',
            'stock', 'is_available', 'category', 'brand', 'tags',
            'cross_sell', 'url', 'full_url', 'open_graph', 'related_products', 'variants_by_color',
            'product_review_count', 'product_average_rating', 'is_wishlisted'
        )


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer cho việc tạo và cập nhật đánh giá sản phẩm
    """
    profile = serializers.HiddenField(default=None)  # Sẽ được gán trong view

    @extend_schema_field(serializers.IntegerField())
    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    class Meta:
        model = Review
        fields = ["code", "profile", "rating", 'subject', 'content', 'status']
        read_only_fields = ["code", "profile", "status"]


class WishListSerializer(serializers.ModelSerializer):
    """
    Serializer cho danh sách yêu thích
    """
    product = ProductSerializer()

    class Meta:
        model = WishList
        fields = ('id', 'product', 'removed', 'created_at')


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer cho các sản phẩm trong giỏ hàng
    """
    variant_product = ProductVariantSerializer(read_only=True)
    variant_product_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), source='variant_product', write_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'variant_product', 'variant_product_id', 'quantity', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer cho các sản phẩm trong đơn hàng
    """
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer cho đơn hàng.
    Dùng để list đơn hàng.
    """
    order_items_set = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'code', 'sub_total', 'total_amount',
            'status', 'created_at', 'payment_method',
            'order_items_set',
        ]


class ShippingInfoSerializer(serializers.Serializer):
    """
    Serializer cho thông tin vận chuyển (đối với người dùng không đăng nhập).
    """
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    street = serializers.CharField()
    state = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField()
    country = serializers.CharField()
    zip_code = serializers.CharField()


class CartItemInputSerializer(serializers.Serializer):
    """
    Serializer cho phép tạo đơn hàng từ giỏ hàng.
    """
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer cho việc tạo đơn hàng từ giỏ hàng.
    """
    cart_items = CartItemInputSerializer(many=True)
    shipping = ShippingInfoSerializer()
    payment_method = serializers.ChoiceField(choices=['PP'])

    def validate_cart_items(self, value):
        if not value:
            raise serializers.ValidationError("Cart items cannot be empty.")
        return value


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer cho chi tiết đơn hàng.
    Dùng để xem chi tiết đơn hàng.
    """
    order_items_set = OrderItemSerializer(many=True, read_only=True)
    shipping_address = ShippingInfoSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'code', 'sub_total', 'total_amount',
            'status', 'created_at', 'payment_method',
            'order_items_set', 'shipping_address'
        ]