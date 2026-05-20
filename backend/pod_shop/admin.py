import requests
from django.conf import settings
from django import forms

def add_to_woocommerce_cart(sku, quantity=1, note=None):
    """
    Gọi WooCommerce API để thêm sản phẩm vào giỏ hàng bằng SKU
    """
    url = f"https://jones.com/wp-json/wc/v3/products?sku={sku}"
    auth = (WOOCOMMERCE_API_KEY, WOOCOMMERCE_API_SECRET)
    # Lấy thông tin sản phẩm/biến thể theo SKU
    resp = requests.get(url, auth=auth)
    if resp.status_code != 200:
        return False, f"Không tìm thấy sản phẩm với SKU: {sku} (status {resp.status_code})"
    products = resp.json()
    if not products:
        return False, "Không tìm thấy sản phẩm với SKU này."
    product_id = products[0]["id"]
    # Gọi API thêm vào giỏ hàng (tùy WooCommerce, có thể cần plugin hỗ trợ REST cart)
    # Ví dụ: sử dụng endpoint custom /wp-json/cocart/v2/cart/add-item
    cart_url = "https://jones.com/wp-json/cocart/v2/cart/add-item"
    payload = {
        "product_id": product_id,
        "quantity": quantity,
    }
    if note:
        payload["customer_note"] = note
    cart_resp = requests.post(cart_url, auth=auth, json=payload)
    if cart_resp.status_code == 200:
        return True, "Đã thêm vào giỏ hàng thành công."
    return False, f"Lỗi khi thêm vào giỏ hàng: {cart_resp.text}"

from django.contrib import admin, messages
from django.utils.html import format_html

from pod_shop.forms import ProductBrandAdminForm, ProductCategoryAdminForm, ProductTagAdminForm, ProductReviewAdminForm, \
    ProductAdminForm
from pod_shop.models import Brand, Category, ProductImage, Tag, Review, WishList, CartItem, Order, OrderItem, Product, \
    ProductAttr, ProductAttrItem, ProductColor, ProductSize, ProductColorImage, ProductVariant, BulkReview

# WooCommerce API credentials
WOOCOMMERCE_API_KEY = "ck_5ce2e3c411f7ee8328dbd9beffe0c7653341b292"
WOOCOMMERCE_API_SECRET = "cs_6f9a2fc5567520a539be514e9ea4581c8fd1160c"

# --- ProductColor ---
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'value', 'color_code')
    search_fields = ('name', 'value', 'color_code')
    save_on_top = True

# --- ProductSize ---
@admin.register(ProductSize)
class ProductSizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'value', 'order')
    search_fields = ('name', 'value')
    list_editable = ('order',)
    ordering = ('order',)
    save_on_top = True

# --- ProductColorImage ---
@admin.register(ProductColorImage)
class ProductColorImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'color', 'alt', 'order')
    search_fields = ('product__name', 'color__name', 'alt')
    list_filter = ('color', 'product')
    list_editable = ('order',)
    save_on_top = True

# --- ProductVariant ---
class ProductVariantDynamicForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['product', 'price_origin', 'price_promo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # When product is known, add one field per available attribute
        product = self.instance.product if self.instance and self.instance.pk else self.initial.get('product')
        if not product and 'product' in self.data:
            try:
                product_id = int(self.data.get('product'))
                from pod_shop.models import Product
                product = Product.objects.filter(pk=product_id).first()
            except Exception:
                product = None
        if product:
            attrs = product.available_attrs.all()
            for attr in attrs:
                field_name = f"attr__{attr.id}"
                # Build choices from ProductAttrItem for this attr (global or per-product)
                from pod_shop.models import ProductAttrItem
                qs = ProductAttrItem.objects.filter(attr=attr, product=product)
                self.fields[field_name] = forms.ChoiceField(
                    choices=[('', '---------')] + [(str(it.id), it.label) for it in qs.order_by('attr_order', 'id')],
                    label=attr.name,
                    required=False
                )
                # Pre-select existing value when editing
                if self.instance and self.instance.pk:
                    selected = self.instance.attr_items.filter(attr=attr).values_list('id', flat=True).first()
                    if selected:
                        self.fields[field_name].initial = str(selected)

    def save(self, commit=True):
        instance = super().save(commit)
        # Collect selected items and set attr_items
        from pod_shop.models import ProductAttrItem
        selected_ids = []
        product = instance.product
        if product:
            for attr in product.available_attrs.all():
                key = f"attr__{attr.id}"
                val = self.cleaned_data.get(key)
                if val:
                    selected_ids.append(int(val))
        if commit:
            instance.attr_items.set(selected_ids)
            instance.save()
        else:
            # When not commit, defer setting; but admin usually commits
            self._pending_attr_item_ids = selected_ids
        return instance

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'display_attrs', 'code', 'price_origin', 'price_promo')
    search_fields = ('product__name', 'code')
    list_filter = ('product',)
    form = ProductVariantDynamicForm

    def display_attrs(self, obj):
        return ", ".join([f"{item.attr.name}: {item.label}" for item in obj.attr_items.all()])
    display_attrs.short_description = "Thuộc tính"
    save_on_top = True

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'slug', 'order')
    list_display_links = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    list_editable = ('order',)
    form = ProductBrandAdminForm
    save_on_top = True

    @admin.display(description='Logo')
    def thumbnail(self, obj: Brand):
        if obj.logo:
            u = obj.logo.url
            h = f'<img src="{u}" width="40" height="40" />'
            h = f'<a href="{u}" target="_blank" rel="noopener">{h}</a>'
            return format_html(h)
        return "-"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'name', 'slug', 'order',)
    list_display_links = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    list_editable = ('order',)
    form = ProductCategoryAdminForm
    save_on_top = True

    @admin.display(description='Img')
    def thumbnail(self, obj: Category):
        if obj.image:
            u = obj.image.url
            h = f'<img src="{u}" width="40" height="40" />'
            h = f'<a href="{u}" target="_blank" rel="noopener">{h}</a>'
            return format_html(h)
        return "-"

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ('thumbnail', 'dimensions')
    fields = ('thumbnail', 'image', 'dimensions', 'order', 'removed')

    @admin.display(description='Thumbnail')
    def thumbnail(self, obj: ProductImage):
        if obj.image:
            u = obj.image.url
            h = f'<img src="{u}" width="100" height="100" />'
            h = f'<a href="{u}" target="_blank">{h}</a>'
            return format_html(h)
        return "-"

    @admin.display(description='Dimensions')
    def dimensions(self, obj: ProductImage):
        if obj.image:
            return f'{obj.image.width}x{obj.image.height}'
        return '-'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'desc')
    list_display_links = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}
    form = ProductTagAdminForm
    save_on_top = True

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'subject', 'user', 'rating', 'status', 'created_at')
    list_display_links = ('id', 'product', 'subject')
    list_filter = ('product', 'user', 'rating', 'status', 'created_at')
    search_fields = ('product__name', 'subject', 'user__username', 'content')
    readonly_fields = ('created_at',)
    actions = ['approve_reviews']
    form = ProductReviewAdminForm
    raw_id_fields = ['product']
    save_on_top = True

    @admin.display(description='Duyệt đánh giá')
    def approve_reviews(self, request, queryset):
        updated = queryset.update(status=True)
        self.message_user(request, "Selected reviews have been approved.")
        self.message_user(request, f'Đã duyệt thành công {updated} đánh giá.', messages.SUCCESS)

@admin.register(WishList)
class WishListAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'removed', 'created_at')
    raw_id_fields = ('user', 'product')
    list_filter = ('removed',)
    list_editable = ('removed',)
    search_fields = ('user__username', 'product__code', 'product__name')
    readonly_fields = ('created_at',)
    save_on_top = True

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'product', 'variant', 'get_code', 'get_variant_sku', 'get_attr_item', 'product_price', 'quantity',
        'line_total', 'customer_note', 'order', 'removed', 'updated_at'
    )
    list_display_links = ('id', 'user', 'product')
    list_filter = ('user', 'removed', 'updated_at')
    search_fields = ('user__username', 'product', 'variant__code')
    readonly_fields = ('updated_at', 'get_code', 'get_variant_sku', 'get_attr_item')
    raw_id_fields = ('user', 'product', 'variant')
    save_on_top = True
    fieldsets = (
        (None, {
            'fields': (
                'user', 'product', 'variant', 'get_code', 'get_variant_sku', 'get_attr_item',
                'quantity', 'customer_note', 'order', 'removed', 'updated_at'
            )
        }),
    )

    @admin.display(description='Mã sản phẩm')
    def get_code(self, obj: CartItem):
        return obj.product.code if obj.product else '-'

    @admin.display(description='SKU Variant')
    def get_variant_sku(self, obj: CartItem):
        return obj.variant.code if obj.variant else '-'

    @admin.display(description='Thuộc tính')
    def get_attr_item(self, obj: CartItem):
        if obj.attr_items:
            return ", ".join(a.label + f'({a.id})' for a in obj.attr_items.all())
        return '-'

    @admin.display(description='Giá sản phẩm')
    def product_price(self, obj: CartItem):
        if obj.variant:
            return obj.variant.get_price() or obj.product.price
        return obj.product.price if obj.product else '-'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'get_code', 'get_attr_item', 'quantity', 'price', 'line_total', 'get_customer_note')
    readonly_fields = ('get_code', 'get_attr_item', 'price', 'line_total', 'get_customer_note')
    raw_id_fields = ['product']
    show_change_link = True

    @admin.display(description='Mã sản phẩm')
    def get_code(self, obj: OrderItem):
        return obj.product.code if obj.product else '-'

    @admin.display(description='Thuộc tính')
    def get_attr_item(self, obj: OrderItem):
        if obj.attr_item:
            return ", ".join(a.label + f'({a.id})' for a in obj.attr_item.all())
        return '-'

    @admin.display(description='Giá x số lượng')
    def line_total(self, obj: OrderItem):
        """
        Tính tổng giá trị của sản phẩm trong đơn hàng
        """
        return obj.price * obj.quantity if obj.price and obj.quantity else 0.0

    @admin.display(description='Ghi chú của khách hàng')
    def get_customer_note(self, obj: OrderItem):
        """
        Hiển thị ghi chú của khách hàng nếu có
        """
        return obj.customer_note if obj.customer_note else '-'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'variant', 'get_code', 'get_variant_sku', 'get_attr_item', 'quantity', 'price', 'line_total')
    list_display_links = ('id', 'order', 'product')
    list_filter = ('order__status', 'created_at')
    search_fields = ('order__code', 'product__name', 'product__code', 'variant__code')
    readonly_fields = ('get_code', 'get_variant_sku', 'get_attr_item', 'price', 'line_total')
    raw_id_fields = ['order', 'product', 'variant']
    save_on_top = True
    fieldsets = (
        (None, {
            'fields': (
                'order', 'product', 'variant', 'get_code', 'get_variant_sku', 'get_attr_item', 'quantity', 'price', 'line_total'
            )
        }),
    )

    @admin.display(description='Mã sản phẩm')
    def get_code(self, obj: OrderItem):
        return obj.product.code if obj.product else '-'

    @admin.display(description='SKU Variant')
    def get_variant_sku(self, obj: OrderItem):
        return obj.variant.code if obj.variant else '-'

    @admin.display(description='Thuộc tính')
    def get_attr_item(self, obj: OrderItem):
        if obj.attr_item:
            return ", ".join(a.label + f'({a.id})' for a in obj.attr_item.all())
        return '-'

    @admin.display(description='Giá x số lượng')
    def line_total(self, obj: OrderItem):
        """
        Tính tổng giá trị của sản phẩm trong đơn hàng
        """
        return obj.price * obj.quantity if obj.price and obj.quantity else 0.0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'user', 'status', 'total_amount', 'created_at')
    list_display_links = ('id', 'code', 'user')
    list_filter = ('status', 'created_at')
    search_fields = ('code', 'user__username', 'email', 'first_name', 'last_name')
    readonly_fields = ('code', 'sub_total', 'total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    raw_id_fields = ['user']
    save_on_top = True

class ProductReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ('user', 'reviewer_name', 'subject', 'rating', 'status', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False
    show_change_link = True


class ProductBulkReviewInline(admin.TabularInline):
    """
    Inline để hiển thị và quản lý bulk reviews trong ProductAdmin
    """
    model = BulkReview
    extra = 0
    fields = ('rating', 'quantity', 'created_at', 'admin_notes')
    readonly_fields = ('created_at',)
    show_change_link = True


@admin.register(BulkReview)
class BulkReviewAdmin(admin.ModelAdmin):
    """
    Admin interface cho BulkReview - cho phép admin tạo nhiều review ẩn danh chỉ với số sao
    """
    list_display = ('id', 'product', 'rating', 'quantity', 'total_reviews', 'created_at')
    list_display_links = ('id', 'product')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'product__code')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ['product']
    save_on_top = True
    fieldsets = (
        (None, {
            'fields': ('product', 'rating', 'quantity')
        }),
        ('Thông tin bổ sung', {
            'fields': ('admin_notes', 'created_at', 'updated_at')
        }),
    )

    @admin.display(description='Tổng reviews')
    def total_reviews(self, obj: BulkReview):
        """
        Hiển thị tổng số reviews (rating x quantity)
        """
        return f"{obj.rating} ⭐ × {obj.quantity} = {obj.rating * obj.quantity} điểm"


class _MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class _MultiFileField(forms.FileField):
    """Form field accepting multiple files in one <input type=file multiple>.
    Django 5.x ships the widget but not the field — define once."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', _MultiFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)]


class BulkProductImageForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(status='A').order_by('name'),
        help_text='Sản phẩm sẽ nhận tất cả ảnh upload.',
    )
    images = _MultiFileField(
        help_text='Giữ Ctrl/Cmd để chọn nhiều file một lúc.',
    )


@admin.register(ProductImage)
class ProductImage(admin.ModelAdmin):
    list_display = ('thumbnail', 'product', 'order', 'removed')
    list_display_links = ('product',)
    readonly_fields = ('thumbnail',)
    search_fields = ('product__name',)
    list_editable = ('order', 'removed')
    save_on_top = True
    change_list_template = 'admin/pod_shop/productimage/change_list.html'

    @admin.display(description='Thumbnail')
    def thumbnail(self, obj: ProductImage):
        if obj.image:
            u = obj.image.url
            h = f'<img src="{u}" width="100" height="100" />'
            h = f'<a href="{u}" target="_blank">{h}</a>'
            return format_html(h)
        return "-"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                'bulk-upload/',
                self.admin_site.admin_view(self.bulk_upload_view),
                name='pod_shop_productimage_bulk_upload',
            ),
        ]
        return custom + urls

    def bulk_upload_view(self, request):
        from django.shortcuts import render, redirect
        from pod_shop.models import ProductImage as PI

        if request.method == 'POST':
            form = BulkProductImageForm(request.POST, request.FILES)
            files = request.FILES.getlist('images')
            if form.is_valid() and files:
                product = form.cleaned_data['product']
                last_order = (
                    PI.objects.filter(product=product)
                    .order_by('-order')
                    .values_list('order', flat=True)
                    .first()
                ) or 0
                for i, f in enumerate(files, start=1):
                    PI.objects.create(product=product, image=f, order=last_order + i)
                self.message_user(
                    request,
                    f'Đã upload {len(files)} ảnh cho "{product.name}".',
                    messages.SUCCESS,
                )
                return redirect('admin:pod_shop_productimage_changelist')
            if not files:
                form.add_error('images', 'Phải chọn ít nhất 1 file.')
        else:
            form = BulkProductImageForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Bulk upload product images',
            'form': form,
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        return render(request, 'admin/pod_shop/productimage/bulk_upload.html', context)

@admin.register(ProductAttrItem)
class ProductAttrItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'attr', 'label', 'value', 'extra', 'attr_order')
    list_display_links = ('product', 'attr', 'label')
    search_fields = ('product__name', 'label', 'value')
    save_on_top = True
    raw_id_fields = ['product', 'attr']

class ProductAttrItemAdminInline(admin.TabularInline):
    model = ProductAttrItem
    extra = 0
    raw_id_fields = ['attr']
    fields = ('attr', 'label', 'value', 'extra', 'attr_order')
    show_change_link = True

@admin.register(ProductAttr)
class ProductAttrAdmin(admin.ModelAdmin):
    # Global attributes: manage names only (no product binding here)
    list_display = ('name',)
    list_display_links = ('name',)
    search_fields = ('name',)
    save_on_top = True
    fields = ('name',)
    # Explicit form to enforce only-name field in popup as well
    class ProductAttrOnlyNameForm(forms.ModelForm):
        class Meta:
            model = ProductAttr
            fields = ('name',)

    form = ProductAttrOnlyNameForm

class ProductAttrInline(admin.TabularInline):
    model = ProductAttr
    extra = 0
    fields = ('product', 'name')
    can_delete = False
    show_change_link = True
    autocomplete_fields = ('product',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'slug', 'fake_price', 'price', 'num_images', 'display_attr', 'times_purchased',
        'category', 'display_tags', 'brand', 'status', 'best_seller', 'is_featured', 'updated_at'
    )
    list_display_links = ('name', 'code', 'slug')
    list_filter = ('status', 'created_at', 'updated_at', 'category', 'brand',)
    search_fields = ['name', 'desc', 'desc_short', 'tags__name', 'category__name', 'brand__name']
    readonly_fields = ('code', 'created_at', 'updated_at')
    from pod_shop.models import ProductVariant
    class ProductVariantInline(admin.TabularInline):
        model = ProductVariant
        extra = 0
        fields = ('attr_items', 'code', 'price_origin', 'price_promo')
        readonly_fields = ('code',)
        show_change_link = True
        filter_horizontal = ('attr_items',)

        # Limit attr_items to this product's items only
        def get_formset(self, request, obj=None, **kwargs):
            formset = super().get_formset(request, obj, **kwargs)
            # Capture current object on request for use in formfield filtering
            request._current_product_obj = obj
            return formset

        def formfield_for_manytomany(self, db_field, request, **kwargs):
            if db_field.name == 'attr_items':
                from pod_shop.models import ProductAttrItem
                current_product = getattr(request, '_current_product_obj', None)
                if current_product is not None:
                    kwargs['queryset'] = ProductAttrItem.objects.filter(
                        attr__in=current_product.available_attrs.all(),
                        product=current_product
                    )
                else:
                    # No product yet; show none to encourage save first
                    kwargs['queryset'] = ProductAttrItem.objects.none()
            formfield = super().formfield_for_manytomany(db_field, request, **kwargs)
            if db_field.name == 'attr_items':
                # Prevent adding/editing related from this M2M to reduce confusion
                if hasattr(formfield.widget, 'can_add_related'):
                    formfield.widget.can_add_related = False
                if hasattr(formfield.widget, 'can_change_related'):
                    formfield.widget.can_change_related = False
            return formfield
    class ProductAttrItemInlineFlat(admin.TabularInline):
        """
        Allow creating ProductAttrItem directly under Product admin.
        This lets admins add item values (e.g., Type/Gender/Color/Size options) for this product
        without navigating to a different page.
        """
        model = ProductAttrItem
        extra = 0
        fields = ('attr', 'label', 'value', 'extra', 'attr_order')
        show_change_link = True
    # Django sets the parent FK automatically for inlines; no need to exclude

        def get_queryset(self, request):
            qs = super().get_queryset(request)
            return qs.select_related('attr')

        def get_formset(self, request, obj=None, **kwargs):
            formset = super().get_formset(request, obj, **kwargs)
            request._current_product_obj = obj
            return formset

        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == 'attr':
                from pod_shop.models import ProductAttr
                current_product = getattr(request, '_current_product_obj', None)
                if current_product is not None:
                    # Limit to attributes selected for this product
                    kwargs['queryset'] = current_product.available_attrs.all()
                else:
                    kwargs['queryset'] = ProductAttr.objects.none()
            formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
            if db_field.name == 'attr':
                # Hide the green "+" add button so attributes are managed globally
                if hasattr(formfield.widget, 'can_add_related'):
                    formfield.widget.can_add_related = False
                if hasattr(formfield.widget, 'can_change_related'):
                    formfield.widget.can_change_related = True
            return formfield

    # Use attr items inline and variants inline; attributes are selected via available_attrs field
    inlines = [ProductImageInline, ProductAttrItemInlineFlat, ProductVariantInline, ProductReviewInline, ProductBulkReviewInline]
    form = ProductAdminForm
    filter_horizontal = ('available_attrs',)
    save_on_top = True
    fieldsets = (
        (None, {
            'fields': (
                'name', 'slug', 'code', 'desc_short', 'desc', 'fake_price', 'price', 'status',
                'category', 'brand', 'tags_input', 'best_seller', 'is_featured', 'times_purchased',
                'standard_shipping_fee', 'fast_shipping_fee', 'available_attrs'
            )
        }),
        ('SEO', {
            'fields': (
                'meta_title', 'meta_desc'
            ),
        }),
        ('Advanced options', {
            # 'classes': ('collapse',),
            'fields': (
                'admin_notes',
                'created_at',
                'updated_at'
            )
        }),
    )

    def get_inline_instances(self, request, obj=None):
        """
        Hide inlines on the add view so creating a Product doesn't require
        adding attributes/variants/items/images immediately. They appear after save.
        """
        if obj is None:
            return []
        return super().get_inline_instances(request, obj)

    def save_formset(self, request, form, formset, change):
        # Auto-assign product for ProductAttrItemInlineFlat entries
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, ProductAttrItem) and not obj.product:
                obj.product = form.instance
            obj.save()
        formset.save_m2m()

    # Admin action: Generate variants from attribute items combinations
    actions = ['generate_variants']

    @admin.action(description='Tạo biến thể từ các lựa chọn thuộc tính')
    def generate_variants(self, request, queryset):
        from itertools import product as iter_product
        created = 0
        skipped = 0
        from pod_shop.models import ProductAttrItem
        for prod in queryset:
            # Group items by attribute selected for this product
            attrs = list(prod.available_attrs.all())
            groups = [list(ProductAttrItem.objects.filter(attr=attr, product=prod).order_by('attr_order', 'id')) for attr in attrs if ProductAttrItem.objects.filter(attr=attr, product=prod).exists()]
            if not groups:
                continue
            # Existing signatures to avoid duplicates (tuple of sorted item IDs)
            existing = set()
            for var in prod.variants_product_set.prefetch_related('attr_items').all():
                sig = tuple(sorted(list(var.attr_items.values_list('id', flat=True))))
                existing.add(sig)
            # Generate combinations
            for combo in iter_product(*groups):
                sig = tuple(sorted([item.id for item in combo]))
                if sig in existing:
                    skipped += 1
                    continue
                variant = ProductVariant(product=prod)
                variant.save()  # Save first to get PK
                variant.attr_items.set([item.id for item in combo])
                variant.save()  # Regenerate SKU with attr_items
                existing.add(sig)
                created += 1
        self.message_user(request, f'Đã tạo {created} biến thể mới. Bỏ qua {skipped} tổ hợp đã tồn tại.', messages.SUCCESS)

    @admin.display(description='Tags')
    def display_tags(self, instance):
        """
        Display tags
        """
        return ", ".join(instance.tags.values_list('name', flat=True))

    @admin.display(description='Images')
    def num_images(self, obj: Product):
        """
        Số lượng hình ảnh của sản phẩm
        """
        return obj.images.filter(removed=False).count()

    @admin.display(description='Thuộc tính')
    def display_attr(self, obj: Product):
        """
        Display attributes selected for this product and their available items
        """
        from pod_shop.models import ProductAttrItem
        parts = []
        for attr in obj.available_attrs.all():
            items = ProductAttrItem.objects.filter(attr=attr, product=obj).order_by('attr_order', 'id')
            parts.append(f"{attr.name}: {', '.join(i.label + f' ({i.id})' for i in items)}")
        return ", ".join(parts)