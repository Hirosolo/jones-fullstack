# path: myshop/signals.py

from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from django.db.models import F
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from myshop.models import Brand, Category, Tag, Product, ProductVariant, Review, ShippingFee, OrderTax, CartItem, Order
from utils.common import get_random_code2
from utils.content_processors import clean_content

# Dict ánh xạ các model với các trường tương ứng
PRE_SAVE_MODELS = {
    Brand: ['desc'],
    Category: ['desc'],
    Tag: ['desc'],
    Product: ['desc', 'desc_short', 'seller_notes'],
    Review: ['content']
}

@receiver(pre_save)
def handle_pre_save(sender, instance, **kwargs):
    """
    Xử lý trước khi lưu dữ liệu
    """
    if sender in PRE_SAVE_MODELS:
        for field in PRE_SAVE_MODELS[sender]:
            safe_field = f"{field}_safe"
            setattr(instance, safe_field, clean_content(getattr(instance, field)))


# Danh sách các model cần xử lý sau khi lưu
POST_SAVE_MODELS = [Product, Review, OrderTax, ShippingFee]

@receiver(post_save)
def handle_post_save(sender, instance, created, **kwargs):
    """
    Xử lý sau khi lưu dữ liệu
    """
    if sender in POST_SAVE_MODELS and not instance.code:
        code = get_random_code2(13, "n")
        instance.code = code
        sender.objects.filter(id=instance.id).update(code=code)


# Xử lý để tạo mã SKU cho riêng cho ProductVariant có tiền tố là SKUxxxxxxxxxx
@receiver(pre_save, sender=ProductVariant)
def create_sku_code(sender, instance, **kwargs):
    """
    Tạo mã SKU cho ProductVariant nếu chưa có.
    Mã SKU sẽ có định dạng 'SKU' + mã ngẫu nhiên 10 ký tự.
    """
    if not instance.code:
        instance.code = f'SKU{get_random_code2(10, "n")}'


# Xử lý để tạo mã order riêng cho các đơn hàng mới
@receiver(post_save, sender=Order)
def create_order_code(sender, instance, created, **kwargs):
    """
    Tạo mã đơn hàng cho Order nếu là đơn hàng mới.
    Mã đơn hàng sẽ có định dạng 'ORDER' + mã ngẫu nhiên 8 ký tự.
    """
    if created and not instance.code:
        instance.code = f'ORDER{get_random_code2(8, "n")}'
        instance.save()


@receiver(user_logged_in, sender=User)
def merge_cart_on_login(sender, request, user, **kwargs):
    """
    Khi người dùng đăng nhập, hợp nhất giỏ hàng của khách (dựa vào session_key) với giỏ hàng của người dùng.
    """
    if not user.is_authenticated:
        return

    session_key = request.session.session_key
    if not session_key:
        return

    guest_cart_items = CartItem.objects.filter(user=None, session_key=session_key)

    for guest_item in guest_cart_items:
        try:
            with transaction.atomic():
                existing_item = CartItem.objects.get(
                    user=user,
                    variant_product=guest_item.variant_product
                )
                # Nếu đã tồn tại, cộng dồn số lượng
                existing_item.quantity = F('quantity') + guest_item.quantity
                existing_item.save()
                guest_item.delete()
        except CartItem.DoesNotExist:
            # Nếu chưa tồn tại, chuyển sang user
            guest_item.user = user
            guest_item.session_key = None  # bỏ session_key sau khi gán user
            guest_item.save()