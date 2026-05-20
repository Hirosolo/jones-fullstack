# path: pod_shop/api/views/cart/listing.py
from decimal import Decimal

from django.db.models import Sum
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pod_shop.api.serializers import CartItemSerializer, OrderListSerializer
from pod_shop.models import CartItem, Order
from utils.api.common import ItemsListPagination


@extend_schema(
    summary="Lấy danh sách sản phẩm trong giỏ hàng",
    description="API này trả về danh sách các sản phẩm trong giỏ hàng của người dùng, bao gồm tổng số lượng sản phẩm.",
    responses={
        200: OpenApiResponse(
            description="Danh sách sản phẩm trong giỏ hàng",
            response=CartItemSerializer(many=True)
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart_items_view(request):
    """
    Lấy danh sách sản phẩm trong giỏ hàng của người dùng.
    """
    user = request.user if request.user.is_authenticated else None

    if user:
        cart_items = CartItem.objects.filter(user=user, removed=False)\
            .select_related('product')\
            .prefetch_related('attr_items')
    else:
        # Cho khách vãng lai, lấy cart items có user=None
        cart_items = CartItem.objects.filter(user__isnull=True, removed=False)\
            .select_related('product')\
            .prefetch_related('attr_items')

    total_quantity = cart_items.aggregate(s=Sum('quantity'))['s'] or 0
    sub_total = sum(item.product.price * item.quantity for item in cart_items)

    serializer = CartItemSerializer(cart_items, many=True, context={'user': user})

    # tính phí shipping
    total_standard_shipping_fee = Decimal('0.00')
    total_fast_shipping_fee = Decimal('0.00')

    for item in cart_items:
        if item.product.standard_shipping_fee:
            total_standard_shipping_fee += item.product.standard_shipping_fee * item.quantity
        if item.product.fast_shipping_fee:
            total_fast_shipping_fee += item.product.fast_shipping_fee * item.quantity

    return Response({
        'ok': True,
        'cart_items': serializer.data,
        'total_quantity': total_quantity,
        'sub_total': Decimal(sub_total),
        'total_standard_shipping_fee': Decimal(total_standard_shipping_fee),
        'total_fast_shipping_fee': Decimal(total_fast_shipping_fee)
    })


@extend_schema(
    summary="Lấy danh sách đơn hàng của người dùng",
    description="API này trả về danh sách các đơn hàng của người dùng, có thể lọc theo trạng thái, khoảng thời gian tạo và tìm kiếm theo mã đơn.",
    parameters=[
        OpenApiParameter(
            name='status', type=str, description="Lọc theo trạng thái đơn hàng (ví dụ: 'pending', 'completed')"
        ),
        OpenApiParameter(
            name='created_from', type=str, description="Lọc theo ngày tạo từ (định dạng: YYYY-MM-DD)"
        ),
        OpenApiParameter(
            name='created_to', type=str, description="Lọc theo ngày tạo đến (định dạng: YYYY-MM-DD)"
        ),
        OpenApiParameter(
            name='search', type=str, description="Tìm kiếm theo mã đơn hàng"
        ),
        OpenApiParameter(
            name='page', type=int, description="Số trang để phân trang (mặc định là 1)"
        ),
        OpenApiParameter(
            name='page_size', type=int, description="Số lượng đơn hàng trên mỗi trang (mặc định là 10)"
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Danh sách đơn hàng",
            response=OrderListSerializer(many=True)
        )
    }
)
@api_view(['GET'])
def list_orders_view(request):
    """
    Lấy danh sách đơn hàng của người dùng với các tùy chọn lọc và phân trang.
    """
    user = request.user
    orders = Order.objects.filter(user=user)

    # Lọc theo trạng thái
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    # Lọc theo khoảng thời gian
    created_from = request.GET.get('created_from')
    created_to = request.GET.get('created_to')
    if created_from:
        orders = orders.filter(created_at__gte=parse_datetime(created_from))
    if created_to:
        orders = orders.filter(created_at__lte=parse_datetime(created_to))

    # Tìm kiếm theo mã đơn
    search = request.GET.get('search')
    if search:
        orders = orders.filter(code__icontains=search)

    orders = orders.order_by('-created_at')

    # Phân trang
    paginator = ItemsListPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(orders, request)
    serializer = OrderListSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)