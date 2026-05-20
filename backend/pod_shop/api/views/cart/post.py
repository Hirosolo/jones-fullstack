# path: pod_shop/api/views/cart/post.py
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum, F
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pod_shop.models import CartItem, Product, ProductAttrItem, Order, OrderItem


@extend_schema(
    summary="Thêm sản phẩm vào giỏ hàng",
    description="Thêm sản phẩm vào giỏ hàng với các giá trị thuộc tính (attr_ids). "
                "Dùng cho cả người dùng đăng nhập và không đăng nhập.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'product_code': {'type': 'string'},
                'attr_ids': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'description': 'Danh sách ID của các thuộc tính đã chọn',
                },
                'quantity': {'type': 'integer', 'minimum': 1},
                'customer_note': {
                    'type': 'string',
                    'description': 'Ghi chú của khách hàng (tùy chọn)'
                }
            },
            'required': ['product_code', 'quantity']
        }
    },
    responses={
        200: {
            'description': 'Thêm vào giỏ hàng thành công',
            'content': {
                'application/json': {
                    'example': {
                        'ok': True,
                        'msg': 'Product added to cart successfully',
                        'quantity': 4
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart_view(request):
    data = request.data
    product_code = data.get('product_code')
    attr_items = data.get('attr_ids', [])
    quantity = data.get('quantity', 1)
    customer_note = data.get('customer_note', '')

    # Kiểm tra dữ liệu đầu vào
    if not isinstance(quantity, int) or quantity < 1:
        return Response({'ok': False, 'msg': 'Số lượng' 'quantity' 'phải là một số nguyên lớn hơn 0.'})

    user = request.user if request.user.is_authenticated else None

    # Kiểm tra sản phẩm có tồn tại và đang bán
    try:
        product = Product.objects.get(code=product_code, status='A')
    except Product.DoesNotExist:
        return Response({'ok': False, 'msg': 'Sản phẩm không tồn tại hoặc đã bị xóa.'})
    
    # Lấy và xác thực các attr_items
    attr_items = list(ProductAttrItem.objects.filter(product=product, id__in=attr_items))
    if len(attr_items) != len(attr_items):
        return Response({'ok': False, 'msg': 'Một hoặc nhiều giá trị thuộc tính không hợp lệ.'})

    # Tạo khóa so sánh
    attr_item_ids = sorted(item.id for item in attr_items)
    attr_key = ','.join(map(str, attr_item_ids))

    with transaction.atomic():
        if user:
            cart_items = CartItem.objects.select_for_update().filter(
                user=user,
                product=product,
                removed=False
            )
        else:
            cart_items = CartItem.objects.select_for_update().filter(
                user__isnull=True,
                product=product,
                removed=False
            )

        matched_item = None
        for item in cart_items:
            item_ids = sorted(item.attr_items.values_list('id', flat=True))
            item_key = ','.join(map(str, item_ids))
            if item_key == attr_key:
                matched_item = item
                break

        if matched_item:
            matched_item.quantity = F('quantity') + quantity
            matched_item.save(update_fields=['quantity', 'updated_at'])
        else:
            new_item = CartItem.objects.create(
                user=user,
                product=product,
                quantity=quantity,
                customer_note=customer_note,
            )
            new_item.attr_items.set(attr_items)

        if user:
            total_quantity = CartItem.objects.filter(
                user=user,
                removed=False
            ).aggregate(total=Sum('quantity'))['total'] or 0
        else:
            total_quantity = CartItem.objects.filter(
                user__isnull=True,
                removed=False
            ).aggregate(total=Sum('quantity'))['total'] or 0

    return Response({
        'ok': True,
        'msg': 'Product added to cart successfully',
        'quantity': total_quantity
    })


@extend_schema(
    summary="Cập nhật số lượng sản phẩm trong giỏ hàng",
    description="Cập nhật số lượng của từng sản phẩm có trong giỏ hàng theo ID.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'quantity': {'type': 'integer', 'minimum': 1},
                        },
                        'required': ['id', 'quantity']
                    }
                }
            },
            'required': ['items']
        }
    },
    responses={
        200: {
            'description': 'Cập nhật số lượng thành công',
            'content': {
                'application/json': {
                    'example': {'ok': True, 'msg': 'Đã cập nhật số lượng sản phẩm.'}
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def update_cart_quantity_view(request):
    user = request.user if request.user.is_authenticated else None

    items = request.data.get('items', [])
    if not isinstance(items, list):
        return Response({'ok': False, 'msg': 'Dữ liệu không hợp lệ.'})

    updated_count = 0
    for entry in items:
        item_id = entry.get('id')
        quantity = entry.get('quantity')

        if not isinstance(item_id, int) or not isinstance(quantity, int) or quantity < 1:
            continue  # Bỏ qua dữ liệu sai

        if user:
            cart_item = CartItem.objects.filter(id=item_id, user=user, removed=False).first()
        else:
            cart_item = CartItem.objects.filter(id=item_id, user__isnull=True, removed=False).first()
            
        if cart_item:
            cart_item.quantity = quantity
            cart_item.save(update_fields=['quantity', 'updated_at'])
            updated_count += 1

    return Response({'ok': True, 'msg': f'Đã cập nhật {updated_count} sản phẩm.'})


@extend_schema(
    summary="Xóa sản phẩm khỏi giỏ hàng theo ID",
    description="Xóa (soft delete) các sản phẩm trong giỏ hàng dựa vào danh sách ID.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'id_list': {
                    'type': 'array',
                    'items': {'type': 'integer'},
                    'description': 'Danh sách ID của CartItem cần xóa',
                },
            },
            'required': ['id_list']
        }
    },
    responses={
        200: {
            'description': 'Đã xóa sản phẩm khỏi giỏ hàng',
            'content': {
                'application/json': {
                    'example': {'ok': True, 'msg': 'Đã xóa các sản phẩm khỏi giỏ hàng.'}
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def remove_from_cart_view(request):
    user = request.user if request.user.is_authenticated else None

    id_list = request.data.get('id_list', [])
    if not isinstance(id_list, list) or not all(isinstance(i, int) for i in id_list):
        return Response({'ok': False, 'msg': 'Dữ liệu không hợp lệ.'})

    deleted_count = 0
    for ci_id in id_list:
        if user:
            cart_item = CartItem.objects.filter(id=ci_id, user=user, removed=False).first()
        else:
            cart_item = CartItem.objects.filter(id=ci_id, user__isnull=True, removed=False).first()
            
        if cart_item:
            cart_item.removed = True
            cart_item.save(update_fields=['removed', 'updated_at'])
            deleted_count += 1

    return Response({'ok': True, 'msg': f'Đã xóa {deleted_count} sản phẩm khỏi giỏ hàng.'})


@extend_schema(
    summary="Hợp nhất giỏ hàng khi đăng nhập",
    description="Khi người dùng đăng nhập, hợp nhất giỏ hàng của khách với giỏ hàng của người dùng. "
                "Nếu có sản phẩm trùng lặp, cập nhật số lượng.",
    methods=['POST'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'cart_items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'product_code': {'type': 'string'},
                            'quantity': {'type': 'integer', 'minimum': 1},
                            'customer_note': {'type': 'string', 'default': ''},
                            'attr_items': {
                                'type': 'array',
                                'items': {'type': 'integer'},
                                'description': 'Danh sách ID của các thuộc tính đã chọn',
                            },
                        },
                        'required': ['product_code', 'quantity']
                    }
                }
            },
        }
    },
    responses={
        200: {
            'description': 'Hợp nhất giỏ hàng thành công',
            'content': {
                'application/json': {
                    'example': {
                        'ok': True,
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def merge_cart_on_login_view(request):
    """
    Khi người dùng đăng nhập, hợp nhất giỏ hàng của khách với giỏ hàng của người dùng.
    """
    user = request.user if request.user.is_authenticated else None
    
    # Nếu user không được xác thực, không thể merge cart
    if not user:
        return Response({'ok': False, 'msg': 'Bạn cần đăng nhập để thực hiện chức năng này.'})
    
    data = request.data

    cart_items = data.get('cart_items', [])

    for item in cart_items:
        quantity = item.get('quantity', 1)
        customer_note = item.get('customer_note', '')
        customer_note = customer_note.strip()

        # kiểm tra sản phẩm có đang bán không
        product_code = item.get('product_code', '')
        prod = Product.objects.filter(code=product_code, status='A').first()
        if not prod:
            return Response({'ok': False, 'msg': f'Sản phẩm với mã {product_code} không tồn tại.'})

        attr_items = item.get('attr_items', [])
        attr_items_qs = ProductAttrItem.objects.filter(id__in=attr_items, product=prod)

        # kiểm tra id trong attr_items có hợp lệ không, có là thuộc tính của sản phẩm không
        if attr_items_qs.count() != len(attr_items):
            return Response({'ok': False, 'msg': 'Một hoặc nhiều giá trị thuộc tính không hợp lệ.'})

        # xem user có đưa sản phẩm nào có chung attr_items vào giỏ hàng không
        ci = CartItem.objects.filter(
            product=prod,
            user=user,
            removed=False,
            attr_items__in=attr_items_qs
        ).first()

        if ci:
            # nếu customer_note khác với giỏ hàng hiện tại thì sẽ tạo mới cart item
            if ci.customer_note != customer_note:
                new_ci = CartItem.objects.create(
                    user=user,
                    product=prod,
                    quantity=quantity,
                    customer_note=customer_note,
                )
                new_ci.attr_items.set(attr_items_qs)
            else:
                # Nếu đã tồn tại, cập nhật số lượng
                ci.quantity += quantity
                ci.save(update_fields=['quantity', 'updated_at'])
        else:
            # Nếu chưa có, tạo mới
            new_ci = CartItem.objects.create(
                user=user,
                product=prod,
                quantity=quantity,
                customer_note=customer_note,
            )
            new_ci.attr_items.set(attr_items_qs)
    return Response({'ok': True})


@extend_schema(
    summary="Tạo đơn hàng từ giỏ hàng",
    description="Tạo đơn hàng từ giỏ hàng của người dùng hoặc khách. "
                "Yêu cầu thông tin người nhận và danh sách sản phẩm trong giỏ hàng.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'first_name': {'type': 'string', 'default': ''},
                'last_name': {'type': 'string', 'default': ''},
                'email': {'type': 'string', 'format': 'email'},
                'street': {'type': 'string', 'default': ''},
                'city': {'type': 'string', 'default': ''},
                'country': {'type': 'string', 'default': ''},
                'zip_code': {'type': 'string', 'default': ''},
                'state': {'type': 'string', 'default': ''},
                'shipping_method': {
                    'type': 'string',
                    'enum': ['standard', 'fast'],
                    'default': 'standard'
                },
                'cart_items': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'product_code': {'type': 'string'},
                            'quantity': {'type': 'integer', 'minimum': 1, 'default': 1},
                            'attr_value_ids': {
                                'type': 'array',
                                'items': {'type': 'integer'},
                                'default': []
                            },
                            'customer_note': {
                                'type': 'string',
                                'default': '',
                                'description': 'Ghi chú của khách hàng cho sản phẩm này'
                            }
                        },
                    }
                }
            },
            'required': ['first_name', 'last_name', 'email', 'street', 'city', 'country', 'zip_code', 'state', 'cart_items']
        }
    },
    responses={
        200: {
            'description': 'Tạo đơn hàng thành công',
            'content': {
                'application/json': {
                    'example': {
                        'ok': True,
                        'order_code': 'ORDER12345678',
                        'sub_total': 100.00,
                        'shipping_fee': 10.00,
                        'total_amount': 110.00
                    }
                }
            }
        },
        400: {
            'description': 'Yêu cầu không hợp lệ',
            'content': {
                'application/json': {
                    'example': {'ok': False, 'msg': 'Thiếu thông tin bắt buộc: first_name'}
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic # Đảm bảo tính toàn vẹn dữ liệu khi tạo đơn hàng
def create_order_view(request):
    """
    API tạo đơn hàng từ giỏ hàng (user hoặc guest).
    """
    data = request.data
    user = request.user if request.user.is_authenticated else None

    # Lấy thông tin người nhận
    required_fields = ['first_name', 'last_name', 'email', 'street', 'city', 'country', 'zip_code', 'cart_items']
    for field in required_fields:
        if not data.get(field):
            return Response({'ok': False, 'msg': f'Thiếu thông tin bắt buộc: {field}'}, status=400)

    cart_data = data['cart_items']  # đây là list cart từ client (dùng cho guest)
    shipping_method = data.get('shipping_method', 'standard')  # 'standard' hoặc 'fast'

    if not isinstance(cart_data, list) or not cart_data:
        return Response({'ok': False, 'msg': 'Danh sách cart_items không hợp lệ.'}, status=400)

    # Tạo đơn hàng
    order = Order.objects.create(
        user=user,
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        street=data['street'],
        state=data.get('state', ''),
        city=data['city'],
        country=data['country'],
        zip_code=data['zip_code'],
    )

    sub_total = Decimal('0.00')
    product_shipping_fee = Decimal('0.00')

    for item in cart_data:
        try:
            product_code = item['product_code']
            quantity = int(item.get('quantity', 1))
            attr_value_ids = item.get('attr_value_ids', [])  # danh sách id của ProductAttrItem
            customer_note = item.get('customer_note', '')

            product = Product.objects.get(code=product_code)
        except (KeyError, Product.DoesNotExist, ValueError):
            return Response({'ok': False, 'msg': f'Sản phẩm không hợp lệ: {item}'}, status=400)

        attr_items = ProductAttrItem.objects.filter(id__in=attr_value_ids) if attr_value_ids else []

        # Phí vận chuyển từng sản phẩm
        if shipping_method == 'standard':
            product_shipping_fee += product.standard_shipping_fee * quantity
        else:
            product_shipping_fee += product.fast_shipping_fee * quantity

        sub_total += product.price * quantity

        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
            customer_note=customer_note,
        )
        if attr_items.exists():
            order_item.attr_item.set(attr_items)

    total_amount = sub_total + product_shipping_fee

    # Cập nhật lại tổng tiền
    order.sub_total = sub_total
    order.shipping_fee = product_shipping_fee
    order.total_amount = total_amount
    order.save(update_fields=['sub_total', 'shipping_fee', 'total_amount'])

    # Xóa các sản phẩm trong giỏ hàng của người dùng sau khi tạo đơn hàng
    if user:
        CartItem.objects.filter(user=user, removed=False).update(removed=True)

    return Response({
        'ok': True,
        'order_code': order.code,
        'sub_total': Decimal(sub_total),
        'shipping_fee': Decimal(product_shipping_fee),
        'total_amount': Decimal(total_amount)
    })