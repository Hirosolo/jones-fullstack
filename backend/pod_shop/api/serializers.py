# path: pod_shop/api/serializers.py

from django.conf import settings
from django.template.defaultfilters import truncatechars
from django.templatetags.static import static
from django.utils.html import strip_tags
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from pod_shop.models import (ProductImage, Product, Category, Brand, Tag, Review,
                            WishList, CartItem, OrderItem, Order, ProductAttr, ProductAttrItem, ProductVariant, ProductColor, ProductSize)
from utils.common import build_media_url, safe_static, build_full_url
class ProductVariantSerializer(serializers.ModelSerializer):
    attr_items = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    def get_attr_items(self, obj):
        return [ {'attr': item.attr.name if item.attr else '', 'label': item.label, 'value': item.value} for item in obj.attr_items.all() ]

    def get_price(self, obj):
        return obj.get_price()

    class Meta:
        model = ProductVariant
        fields = ('id', 'code', 'attr_items', 'price_origin', 'price_promo', 'price')
from utils.api.common import OpenGraphSerializer


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

    @extend_schema_field(serializers.IntegerField)
    def get_num_product(self, obj: Category):
        return Product.objects.filter(status='A', category=obj).count()

    class Meta:
        model = Category
        fields = (
            'name', 'slug', 'desc', 'image', 'order',
            'url', 'full_url', 'num_product',
        )


class ProductCategoryListSerializer(serializers.ModelSerializer):
    """
    Serializer cho chi tiết danh mục sản phẩm
    G
    """
    open_graph = serializers.SerializerMethodField()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj: Category):
        default_og_image = safe_static('img/default-og-image.jpg')
        images = (
            [obj.image.url] if obj.image else [default_og_image]
        )

        return {
            'title': obj.name,
            'description': truncatechars(strip_tags(obj.desc), 145) if obj.desc else settings.SITE_DESC,
            'images': images,
            'url': obj.full_url()
        }

    class Meta:
        model = Category
        fields = (
            'name', 'slug', 'desc', 'image',
            'url', 'full_url', 'open_graph',
        )


class BrandListSerializer(serializers.ModelSerializer):
    """
    Serializer cho danh sách thương hiệu sản phẩm
    """
    num_product = serializers.SerializerMethodField()

    @extend_schema_field(serializers.IntegerField)
    def get_num_product(self, obj: Brand):
        return Product.objects.filter(status='A', brand=obj).count()

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
            [obj.logo.url] if obj.logo else [default_og_image]
        )

        return {
            'title': obj.name,
            'description': truncatechars(strip_tags(obj.desc), 145) if obj.desc else settings.SITE_DESC,
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

    @extend_schema_field(serializers.IntegerField)
    def get_num_product(self, obj):
        return Product.objects.filter(status='A', tags=obj).count()

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

        return {
            'title': obj.name,
            'description': truncatechars(strip_tags(obj.desc), 145) if obj.desc else settings.SITE_DESC,
            'images': default_og_image,
            'url': obj.full_url()
        }

    class Meta:
        model = Tag
        fields = (
            'name', 'desc', 'slug', 'url', 'full_url', 'open_graph',
        )


class ProductAttrItemSerializer(serializers.ModelSerializer):
    """
    Serializer cho các mục thuộc tính sản phẩm
    """
    class Meta:
        model = ProductAttrItem
        fields = (
            'id',
            'label',
            'value',
            'extra',
            'attr_order',
        )


class ProductAttrSerializer(serializers.ModelSerializer):
    """
    Serializer cho thuộc tính sản phẩm
    """
    attr = serializers.SerializerMethodField()

    class Meta:
        model = ProductAttr
        fields = (
            'name',
            'attr',
        )

    @extend_schema_field(ProductAttrItemSerializer(many=True))
    def get_attr(self, obj: ProductAttr):
        attr = ProductAttrItem.objects.filter(attr=obj).order_by('attr_order')
        return ProductAttrItemSerializer(attr, many=True).data


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer cho sản phẩm
    """
    brand = BrandSerializer()
    category = CategorySerializer()
    tags = TagSerializer(many=True)
    preview_picture = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    sale_percentage = serializers.SerializerMethodField()
    product_review_count = serializers.SerializerMethodField()
    product_average_rating = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()

    @extend_schema_field(serializers.CharField)
    def get_attributes(self, obj):
        attrs = obj.attributes.all()
        return ProductAttrSerializer(attrs, many=True).data

    @extend_schema_field(serializers.CharField)
    def get_preview_picture(self, obj: Product):
        """
        Preview URL cho ảnh đầu tiên — ưu tiên image_url (external URL
        do admin paste), fallback sang stored file thumbnails. Nếu file
        đã bị xóa khỏi storage thì trả về empty để FE dùng placeholder.
        """
        img = obj.images.filter(removed=False).order_by('order').first()
        if not img:
            return {'w200': '', 'w400': '', 'w800': ''}

        # External URL: skip the thumbnailer, return the same URL for all sizes.
        if img.image_url:
            url = build_media_url(img.image_url)
            return {'w200': url, 'w400': url, 'w800': url}

        try:
            return {
                'w200': build_media_url(img.get_thumb_by_width(width=200)),
                'w400': build_media_url(img.get_thumb_by_width(width=400)),
                'w800': build_media_url(img.get_thumb_by_width(width=800)),
            }
        except Exception:
            return {'w200': '', 'w400': '', 'w800': ''}


    @extend_schema_field(serializers.FloatField())
    def get_sale_percentage(self, obj: Product):
        """
        Lấy tỷ lệ giảm giá
        """
        return obj.percentage_discount()

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
            'name', 'slug', 'code', 'desc_short', 'fake_price', 'price', 'preview_picture', 'attributes',
            'status', 'category', 'brand', 'tags', 'url', 'full_url', 'is_sale', 'sale_percentage', 'is_featured',
            'best_seller', 'product_review_count', 'product_average_rating', 'is_wishlisted', 'times_purchased'
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
        return build_media_url(obj.image.url)

    @extend_schema_field(serializers.CharField)
    def get_image_thumb_url(self, obj: ProductImage):
        return build_media_url(obj.get_thumb_by_width(width=400))

    @extend_schema_field(serializers.CharField)
    def get_dimension(self, obj: ProductImage):
        return f'{obj.image.width}x{obj.image.height}'

    @extend_schema_field(serializers.IntegerField)
    def get_size(self, obj: ProductImage):
        return obj.image.size

    class Meta:
        model = ProductImage
        fields = (
            'id', 'order', 'created_at',
            'image_url', 'image_thumb_url',
            'dimension', 'size'
        )


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
        Lấy URL của hình ảnh mặc định (absolute URL)
        """
        img = obj.images.filter(removed=False).exclude(image='').order_by('order').first()
        return {
            'w200': build_media_url(img.get_thumb_by_width(width=200)) if img else '',
            'w400': build_media_url(img.get_thumb_by_width(width=400)) if img else '',
            'w800': build_media_url(img.get_thumb_by_width(width=800)) if img else '',
        }

    @extend_schema_field(serializers.FloatField())
    def get_sale_percentage(self, obj: Product):
        """
        Lấy tỷ lệ giảm giá
        """
        return obj.percentage_discount()

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
            'name', 'slug', 'code', 'fake_price', 'price', 'preview_picture',
            'status', 'category', 'brand', 'tags', 'url', 'full_url',
            'is_sale', 'sale_percentage', 'times_purchased',
            'product_review_count', 'product_average_rating', 'is_wishlisted'
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer cho chi tiết sản phẩm
    """
    open_graph = serializers.SerializerMethodField()
    brand = BrandSerializer()
    category = CategorySerializer()
    tags = TagSerializer(many=True)
    related_products = serializers.SerializerMethodField()
    product_review_count = serializers.SerializerMethodField()
    product_average_rating = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    thumbnails = serializers.SerializerMethodField()
    sale_percentage = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()
    @extend_schema_field(ProductVariantSerializer(many=True))
    def get_variants(self, obj):
        variants = obj.variants_product_set.all()
        return ProductVariantSerializer(variants, many=True).data

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj: Product):
        default_og_image = build_full_url(safe_static('img/default-og-image.jpg'))
        img = obj.images.filter(removed=False).order_by('order').first()
        og_image = ''
        if img:
            if img.image_url:
                og_image = img.image_url if img.image_url.startswith(('http://', 'https://')) else build_full_url(build_media_url(img.image_url))
            else:
                # Use the original image (>=1200 returns the original URL via
                # get_thumb_by_width). Larger og:image gives Google/social
                # better thumbnails and reinforces it as the primary image.
                try:
                    thumb = img.get_thumb_by_width(width=1200)
                except Exception:
                    thumb = ''
                raw = thumb or img.get_url()
                og_image = build_full_url(build_media_url(raw)) if raw else ''
        images = [og_image] if og_image else [default_og_image]

        desc = (
            obj.meta_desc if obj.meta_desc
            else truncatechars(strip_tags(obj.desc_short), 145) if obj.desc_short
            else truncatechars(strip_tags(obj.desc), 145) if obj.desc
            else settings.SITE_DESC
        )

        return {
            'title': obj.meta_title if obj.meta_title else obj.name,
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
        return ProductSerializer(obj.related_products(), many=True, context=self.context).data

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

    @extend_schema_field(serializers.CharField)
    def get_attributes(self, obj):
        """
        Lấy danh sách thuộc tính sản phẩm
        """
        attrs = obj.attributes.all()
        return ProductAttrSerializer(attrs, many=True).data

    @extend_schema_field(serializers.CharField)
    def get_images(self, obj: Product):
        urls = []
        for img in obj.images.filter(removed=False).order_by('order'):
            try:
                url = img.get_url()
            except Exception:
                url = ''
            if url:
                urls.append(build_media_url(url))
        return urls

    @extend_schema_field(serializers.CharField)
    def get_thumbnails(self, obj: Product):
        data = []
        for img in obj.images.filter(removed=False).order_by('order'):
            try:
                url = img.get_url()
            except Exception:
                url = ''
            if not url:
                continue
            # `src` keeps returning the 600px thumbnail (used by FE/admin
            # for fast-loading previews — leave untouched).
            # `width/height` now report the ORIGINAL image dimensions so
            # JSON-LD/Google sees the real resolution paired with the
            # full-size URL in `images[]`. Hard-coding 600x600 here while
            # the URL was a 2048x2048 file made Google treat the main
            # image as low-resolution and prefer thumbnails from the
            # "More Products You May Like" section.
            try:
                if img.image:
                    src = build_media_url(img.get_thumb_by_width(width=600))
                    if img.image.width and img.image.height:
                        width = img.image.width
                        height = img.image.height
                    else:
                        width, height = 0, 0
                else:
                    src = build_media_url(url)
                    width, height = 0, 0
            except Exception:
                src = build_media_url(url)
                width, height = 0, 0
            data.append({'key': img.id, 'src': src, 'width': width, 'height': height})
        return PhotoGallerySerializer(data, many=True).data

    @extend_schema_field(serializers.FloatField())
    def get_sale_percentage(self, obj: Product):
        """
        Lấy tỷ lệ giảm giá
        """
        return obj.percentage_discount()

    class Meta:
        model = Product
        fields = (
            'name', 'slug', 'code', 'desc', 'desc_short', 'images', 'thumbnails', 'fake_price', 'price', 'status',
            'category', 'brand', 'tags', 'attributes', 'url', 'full_url', 'open_graph', 'related_products',
            'product_review_count', 'product_average_rating', 'sale_percentage',
            'is_wishlisted', 'is_featured', 'best_seller', 'variants'
        )


class ProductReviewSerializer(serializers.ModelSerializer):
    """
    Serializer cho đánh giá sản phẩm
    """
    user = serializers.SerializerMethodField(source='user_review_set')
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    @extend_schema_field(serializers.CharField)
    def get_user(self, obj: Review):
        if obj.user:
            # User đã đăng nhập
            return {
                'username': obj.user.username,
                'full_name': obj.user.get_full_name() or obj.user.username
            }
        elif obj.reviewer_name:
            # Anonymous nhưng có tên (vì có opinion/content)
            return {
                'username': 'anonymous',
                'full_name': obj.reviewer_name
            }
        else:
            # Anonymous không có tên (chỉ rating)
            return {
                'username': 'anonymous',
                'full_name': 'Anonymous User'
            }

    class Meta:
        model = Review
        fields = ('id', 'user', 'rating', 'subject', 'content_safe', 'created_at')


class ReviewCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer cho việc tạo và cập nhật đánh giá sản phẩm
    """
    user = serializers.HiddenField(default=None)  # Sẽ được gán trong view
    reviewer_name = serializers.CharField(max_length=255, required=False, allow_blank=True)

    @extend_schema_field(serializers.IntegerField())
    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate(self, data):
        """
        Validate logic:
        - BẮT BUỘC phải có reviewer_name cho tất cả review (nếu user chưa đăng nhập)
        """
        request = self.context.get('request')
        has_reviewer_name = bool(data.get('reviewer_name', '').strip())
        is_authenticated = request and request.user.is_authenticated
        
        # Nếu chưa đăng nhập thì BẮT BUỘC phải có reviewer_name
        if not is_authenticated and not has_reviewer_name:
            raise serializers.ValidationError({
                'reviewer_name': 'Reviewer name is required.'
            })
        
        return data

    class Meta:
        model = Review
        fields = ["id", "user", "reviewer_name", "rating", 'subject', 'content', 'status']
        read_only_fields = ["id", "user", "status"]

    def create(self, validated_data):
        review = super().create(validated_data)
        # Forward push lên .shop. Fail-soft — wp_review_sync.push_to_shop tự
        # nuốt mọi exception và chỉ log, để response trả 201 ngay cả khi
        # .shop unreachable. on_commit để chắc chắn DB row đã commit trước
        # khi gọi WP REST.
        try:
            from django.db import transaction
            from pod_shop.services.wp_review_sync import push_to_shop
            transaction.on_commit(lambda: push_to_shop(review))
        except Exception:  # noqa: BLE001
            pass
        return review


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
    product = ProductInCartSerializer()
    attr_cart_items = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_attr_cart_items(self, obj):
        """
        Chỉ trả về các thuộc tính và giá trị đã chọn trong giỏ hàng
        """
        selected_items = obj.attr_items.select_related('attr')

        # Group items theo attr
        attr_map = {}
        for item in selected_items:
            attr = item.attr
            if attr.id not in attr_map:
                attr_map[attr.id] = {
                    'name': attr.name,
                    'attr': []
                }
            attr_map[attr.id]['attr'].append({
                'id': item.id,
                'label': item.label,
                'value': item.value,
                'extra': item.extra,
                'attr_order': item.attr_order,
            })

        return list(attr_map.values())

    @extend_schema_field(serializers.FloatField)
    def get_line_total(self, obj):
        return float(obj.product.price * obj.quantity)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'attr_cart_items', 'quantity', 'customer_note', 'line_total']


class ProductInOrderSerializer(serializers.ModelSerializer):
    """
    Serializer cho sản phẩm trong đơn hàng
    """
    class Meta:
        model = Product
        fields = (
            'name', 'slug', 'code', 'price'
        )


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer cho các sản phẩm trong đơn hàng
    """
    product = ProductInOrderSerializer(read_only=True)
    attr_order_items = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_attr_order_items(self, obj: OrderItem):
        """
        Chỉ trả về các thuộc tính và giá trị đã chọn trong đơn hàng
        """
        selected_items = obj.attr_item.select_related('attr')

        # Group items theo attr
        attr_map = {}
        for item in selected_items:
            attr = item.attr
            if attr.id not in attr_map:
                attr_map[attr.id] = {
                    'name': attr.name,
                    'attr': []
                }
            attr_map[attr.id]['attr'].append({
                'id': item.id,
                'label': item.label,
                'value': item.value,
                'extra': item.extra,
                'attr_order': item.attr_order,
            })

        return list(attr_map.values())

    @extend_schema_field(serializers.FloatField)
    def get_line_total(self, obj: OrderItem):
        """
        Tính tổng giá trị của sản phẩm trong đơn hàng
        """
        return float(obj.price * obj.quantity)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'attr_order_items', 'quantity', 'price', 'customer_note', 'line_total']


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


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer cho đơn hàng.
    Dùng để list đơn hàng.
    """
    class Meta:
        model = Order
        fields = [
            'id', 'code', 'sub_total', 'shipping_fee', 'total_amount',
            'status', 'created_at', 'updated_at',
        ]


class OrderDetailSerializer(serializers.ModelSerializer):
    """
    Serializer cho chi tiết đơn hàng.
    Dùng để xem chi tiết đơn hàng.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = serializers.SerializerMethodField()
    shipping_fee = serializers.SerializerMethodField()

    @extend_schema_field(serializers.FloatField)
    def get_shipping_fee(self, obj: Order):
        """
        Tính phí vận chuyển cho đơn hàng.
        """
        return float(obj.shipping_fee) if obj.shipping_fee else 0.0

    @extend_schema_field(ShippingInfoSerializer)
    def get_shipping_address(self, obj: Order):
        """
        Lấy thông tin địa chỉ vận chuyển.
        Nếu người dùng đã đăng nhập thì lấy từ thông tin người dùng,
        nếu không thì lấy từ thông tin vận chuyển của đơn hàng.
        """
        return {
            'first_name': obj.first_name,
            'last_name': obj.last_name,
            'email': obj.email,
            'street': obj.street,
            'state': obj.state,
            'city': obj.city,
            'country': obj.country,
            'zip_code': obj.zip_code
        }

    class Meta:
        model = Order
        fields = [
            'id', 'code', 'sub_total', 'total_amount',
            'status', 'created_at', 'updated_at',
            'items', 'shipping_fee', 'shipping_address'
        ]