# path: myshop/api/views/cart/post.py
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, F
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from myshop.models import CartItem, ProductVariant, Order, OrderItem, OrderTax, ShippingFee


@extend_schema(
    summary="Thêm sản phẩm vào giỏ hàng",
    description="API này cho phép người dùng thêm sản phẩm vào giỏ hàng, bao gồm các biến thể về size và màu sắc.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'sku_code': {
                    'type': 'string',
                    'description': 'Mã SKU của biến thể sản phẩm cần thêm vào giỏ hàng'
                },
                'quantity': {
                    'type': 'integer',
                    'description': 'Số lượng sản phẩm cần thêm vào giỏ hàng',
                    'minimum': 1
                },
            },
            'required': ['sku_code', 'quantity']
        }
    },
    responses={
        200: {
            'description': 'Thêm sản phẩm vào giỏ hàng thành công',
            'content': {
                'application/json': {
                    'example': {
                        'ok': True,
                        'msg': 'Product variant added to cart successfully',
                        'quantity': 5
                    }
                }
            }
        },
        404: {'description': 'Biến thể sản phẩm không tìm thấy hoặc không hoạt động'}
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart_view(request):
    """
    Thêm sản phẩm vào giỏ hàng (dành cho cả user và guest), bao gồm các biến thể về size và màu sắc.
    """
    data = request.data
    sku_code = data.get('sku_code')
    quantity = data.get('quantity', 1)

    # Xác định user hoặc session_key
    user = request.user if request.user.is_authenticated else None
    session_key = None
    if not user:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

    # Validate input
    if not isinstance(quantity, int) or quantity < 1:
        return Response({'ok': False, 'msg': 'Quantity must be a positive integer.'}, status=400)

    vp = ProductVariant.objects.filter(code=sku_code).first()
    if not vp:
        return Response({'ok': False, 'msg': 'Product variant not found or inactive.'}, status=404)

    with transaction.atomic():
        filter_kwargs = {'variant_product': vp, 'removed': False}
        if user:
            filter_kwargs['user'] = user
        else:
            filter_kwargs['session_key'] = session_key
            filter_kwargs['user'] = None

        cart_item = CartItem.objects.select_for_update().filter(**filter_kwargs).first()

        if cart_item:
            # Nếu đã tồn tại, cập nhật số lượng
            cart_item.quantity = F('quantity') + quantity
            cart_item.removed = False
            cart_item.save(update_fields=['quantity', 'removed', 'updated_at'])
        else:
            # Nếu chưa có, tạo mới
            CartItem.objects.create(
                user=user,
                session_key=session_key,
                variant_product=vp,
                quantity=quantity
            )

        # Tính tổng số lượng sản phẩm trong giỏ hàng
        total_filter = {'removed': False}
        if user:
            total_filter['user'] = user
        else:
            total_filter['session_key'] = session_key
            total_filter['user'] = None

        total_quantity = CartItem.objects.filter(**total_filter).aggregate(
            s=Sum('quantity')
        )['s'] or 0

    return Response({
        'ok': True,
        'msg': 'Product variant added to cart successfully',
        'quantity': total_quantity
    }, status=200)


@extend_schema(
    summary="Xóa sản phẩm khỏi giỏ hàng",
    description="API này cho phép người dùng xóa một sản phẩm khỏi giỏ hàng của họ.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'sku_code': {
                    'type': 'string',
                    'description': 'Mã SKU của biến thể sản phẩm cần xóa khỏi giỏ hàng'
                }
            },
            'required': ['sku_code']
        }
    },
    responses={
        200: {
            'description': 'Xóa sản phẩm khỏi giỏ hàng thành công',
            'content': {
                'application/json': {
                    'example': {
                        'ok': True,
                        'msg': 'Product variant removed from cart successfully'
                    }
                }
            }
        },
        404: {
            'description': 'Biến thể sản phẩm không tìm thấy hoặc không hoạt động'
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def remove_from_cart_view(request):
    """
    Xóa sản phẩm khỏi giỏ hàng (dành cho cả user và guest).
    """
    data = request.data
    sku_code = data.get('sku_code')

    # Xác định user hoặc session_key
    user = request.user if request.user.is_authenticated else None
    session_key = None
    if not user:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

    # Kiểm tra SKU
    vp = ProductVariant.objects.filter(code=sku_code).first()
    if not vp:
        return Response({'ok': False, 'msg': 'Product variant not found or inactive.'}, status=404)

    # Lọc CartItem
    filter_kwargs = {'variant_product': vp, 'removed': False}
    if user:
        filter_kwargs['user'] = user
    else:
        filter_kwargs['user'] = None
        filter_kwargs['session_key'] = session_key

    cart_item = CartItem.objects.filter(**filter_kwargs).first()
    if not cart_item:
        return Response({'ok': False, 'msg': 'Cart item not found.'}, status=404)

    cart_item.removed = True
    cart_item.save(update_fields=['removed', 'updated_at'])

    return Response({'ok': True, 'msg': 'Product variant removed from cart successfully'}, status=200)


@extend_schema(
    summary="Cập nhật số lượng sản phẩm trong giỏ hàng",
    description="API này cho phép người dùng cập nhật số lượng của một sản phẩm trong giỏ hàng.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'sku_code': {
                    'type': 'string',
                    'description': 'Mã SKU của biến thể sản phẩm cần cập nhật số lượng'
                },
                'quantity': {
                    'type': 'integer',
                    'description': 'Số lượng mới của sản phẩm trong giỏ hàng',
                    'minimum': 1
                }
            },
            'required': ['sku_code', 'quantity']
        }
    },
    responses={
        200: {
            'description': 'Cập nhật số lượng sản phẩm thành công',
            'content': {
                'application/json': {
                    'example': {
                        'ok': True,
                        'msg': 'Cart item quantity updated successfully'
                    }
                }
            }
        },
        400: {
            'description': 'Số lượng không hợp lệ hoặc không phải là số nguyên dương'
        },
        404: {
            'description': 'Biến thể sản phẩm không tìm thấy hoặc không hoạt động'
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def update_cart_quantity_view(request):
    """
    Cập nhật số lượng sản phẩm trong giỏ hàng (dành cho cả user và guest).
    """
    data = request.data
    sku_code = data.get('sku_code')
    quantity = data.get('quantity')

    # Validate quantity
    if not isinstance(quantity, int) or quantity < 1:
        return Response({'ok': False, 'msg': 'Quantity must be a positive integer.'}, status=400)

    # Kiểm tra SKU hợp lệ
    vp = ProductVariant.objects.filter(code=sku_code).first()
    if not vp:
        return Response({'ok': False, 'msg': 'Product variant not found or inactive.'}, status=404)

    # Xác định user hoặc session_key
    user = request.user if request.user.is_authenticated else None
    session_key = None
    if not user:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

    # Lọc CartItem
    filter_kwargs = {'variant_product': vp, 'removed': False}
    if user:
        filter_kwargs['user'] = user
    else:
        filter_kwargs['user'] = None
        filter_kwargs['session_key'] = session_key

    cart_item = CartItem.objects.filter(**filter_kwargs).order_by('updated_at').first()
    if not cart_item:
        return Response({'ok': False, 'msg': 'Cart item not found.'}, status=404)

    cart_item.quantity = quantity
    cart_item.save(update_fields=['quantity', 'updated_at'])

    return Response({'ok': True, 'msg': 'Cart item quantity updated successfully'}, status=200)


@extend_schema(
    summary="Tạo đơn hàng từ giỏ hàng",
    description="API này cho phép người dùng tạo đơn hàng từ các sản phẩm trong giỏ hàng của họ. "
                "Nếu người dùng chưa đăng nhập, cần cung cấp thông tin giao hàng thủ công.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'cart_item_ids': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'description': 'Danh sách ID của các sản phẩm trong giỏ hàng'
                },
                'shipping_address': {
                    'type': 'object',
                    'description': 'Thông tin giao hàng (bắt buộc nếu chưa đăng nhập)',
                    'properties': {
                        'first_name': {'type': 'string'},
                        'last_name': {'type': 'string'},
                        'email': {'type': 'string'},
                        'street': {'type': 'string'},
                        'state': {'type': 'string'},
                        'city': {'type': 'string'},
                        'country': {'type': 'string'},
                        'zip_code': {'type': 'string'},
                    },
                    'required': ['first_name', 'last_name', 'email', 'street', 'state', 'city', 'country', 'zip_code']
                }
            },
            'required': ['cart_item_ids']
        }
    },
    responses={
        201: {
            'description': 'Tạo đơn hàng thành công',
            'content': {
                'application/json': {
                    'example': {
                        'ok': True,
                        'msg': 'Order created successfully.',
                        'code': 'ORDER12345678'
                    }
                }
            }
        },
        400: {'description': 'Dữ liệu không hợp lệ hoặc thiếu thông tin giao hàng'}
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def create_order_view(request):
    """
    API tạo đơn hàng từ giỏ hàng (hỗ trợ cả user và guest).
    """
    user = request.user if request.user.is_authenticated else None
    cart_item_ids = request.data.get('cart_item_ids')

    if not cart_item_ids or not isinstance(cart_item_ids, list):
        return Response({'ok': False, 'msg': 'cart_item_ids must be a non-empty list.'}, status=400)

    # Lấy session key nếu chưa đăng nhập
    session_key = None
    if not user:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

    # Lọc cart items theo user hoặc session
    filter_kwargs = {'id__in': cart_item_ids, 'removed': False}
    if user:
        filter_kwargs['user'] = user
    else:
        filter_kwargs.update({'user': None, 'session_key': session_key})

    cart_items = CartItem.objects.select_related('variant_product').filter(**filter_kwargs)
    if not cart_items.exists():
        return Response({'ok': False, 'msg': 'No valid items in the cart.'}, status=400)

    # Lấy địa chỉ giao hàng
    shipping_info = {}
    if user:
        # Lấy địa chỉ mặc định từ sổ địa chỉ của người dùng
        default_address = user.profile.profile_shippingaddress_set.filter(is_default=True).first()
        if not default_address:
            return Response({'ok': False, 'msg': 'User has no default shipping address.'}, status=400)
        shipping_info = {
            'first_name': default_address.first_name,
            'last_name': default_address.last_name,
            'email': default_address.email,
            'street': default_address.street,
            'state': default_address.state,
            'city': default_address.city,
            'country': default_address.country,
            'zip_code': default_address.zip_code,
        }
    else:
        # Lấy shipping_address từ request
        shipping_address = request.data.get('shipping_address')
        if not isinstance(shipping_address, dict):
            return Response({'ok': False, 'msg': 'shipping_address is required for guest checkout.'}, status=400)

        required_fields = ['first_name', 'last_name', 'email', 'street', 'state', 'city', 'country', 'zip_code']
        if not all(field in shipping_address for field in required_fields):
            return Response({'ok': False, 'msg': 'Missing fields in shipping_address.'}, status=400)

        shipping_info = shipping_address

    with transaction.atomic():
        # Tổng tạm tính của đơn hàng
        sub_total = sum(
            item.variant_product.price_promo * item.quantity for item in cart_items
        )
        # Lấy thông tin thuế và phí vận chuyển
        order_tax = OrderTax.objects.first()
        if not order_tax:
            return Response({'error': 'Chưa cấu hình thuế.'}, status=400)

        shipping_fee = ShippingFee.objects.first()
        if not shipping_fee:
            return Response({'error': 'Chưa cấu hình phí vận chuyển.'}, status=400)

        # Tính tổng tiền của đơn hàng bao gồm thuế và phí vận chuyển
        total_amount = (
                Decimal(sub_total)
                + (order_tax.value if order_tax else Decimal(0))
                + (shipping_fee.value if shipping_fee else Decimal(0))
        )

        # Tạo đơn hàng
        order = Order.objects.create(
            user=user,
            sub_total=sub_total,
            order_tax=order_tax,
            shipping_fee=shipping_fee,
            total_amount=total_amount,
            status='W',
            first_name=shipping_info['first_name'],
            last_name=shipping_info['last_name'],
            email=shipping_info['email'],
            street=shipping_info['street'],
            state=shipping_info['state'],
            city=shipping_info['city'],
            country=shipping_info['country'],
            zip_code=shipping_info['zip_code'],
        )

        # Thêm từng sản phẩm vào đơn
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                variant_product=item.variant_product,
                quantity=item.quantity,
                price=item.variant_product.price_promo
            )

        # Đánh dấu đã removed
        cart_items.update(removed=True)

    return Response({
        'ok': True,
        'msg': 'Order created successfully.',
        'code': order.code,
    }, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def merge_cart_on_login_view(request):
    """
    Khi người dùng đăng nhập, hợp nhất giỏ hàng của khách với giỏ hàng của người dùng.
    """
    user = request.user
    data = request.data

    cart_items = data.get('cart_items', [])

    for item in cart_items:
        sku_code = item.get('sku_code', '')
        quantity = item.get('quantity', 1)

        # Kiểm tra SKU hợp lệ
        vp = ProductVariant.objects.filter(code=sku_code).first()
        if not vp:
            return Response({'ok': False, 'msg': f'Product variant {sku_code} not found or inactive.'}, status=404)

        cart_item = CartItem.objects.filter(
            variant_product=vp,
            removed=False,
            user=user,
        ).first()

        if cart_item:
            # Nếu đã tồn tại, cập nhật số lượng
            cart_item.quantity += quantity
            cart_item.removed = False
            cart_item.save(update_fields=['quantity', 'removed', 'updated_at'])
        else:
            # Nếu chưa có, tạo mới
            CartItem.objects.create(
                user=user,
                variant_product=vp,
                quantity=quantity
            )
    return Response({'ok': True, 'msg': 'Cart merged successfully'})


