from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view
from rest_framework.response import Response

from pod_shop.api.serializers import OrderDetailSerializer
from pod_shop.models import Order


@extend_schema(
    summary="Lấy chi tiết đơn hàng",
    description="API để lấy chi tiết đơn hàng theo mã đơn hàng.",
    parameters=[
        OpenApiParameter(
            name='order_code',
            type=str,
            description='Mã đơn hàng cần xem chi tiết',
            required=True
        )
    ],
    responses={
        200: {
            'description': 'Chi tiết đơn hàng',
            'content': {
                'application/json': {
                    'example': {
                        'ok': True,
                        'order': {
                            'order_code': 'ORDER12345678'
                        }
                    }
                }
            }
        }
    },
)
@api_view(['GET'])
def order_detail_view(request):
    """
    API để lấy chi tiết đơn hàng theo mã đơn hàng.
    """
    user = request.user

    order_code = request.GET.get('order_code', '').strip()
    if not order_code:
        return Response({'ok': False, 'msg': 'Thiếu mã đơn hàng.'})

    try:
        order = Order.objects.get(code=order_code, user=user)
    except Order.DoesNotExist:
        return Response({'ok': False, 'msg': 'Đơn hàng không tồn tại.'})

    data = OrderDetailSerializer(order, context={'user': user}).data
    return Response({'ok': True, 'order': data})