# path: myshop/api/views/cart/listing.py

from django.db.models import Sum
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from myshop.api.serializers import CartItemSerializer
from myshop.models import CartItem


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
class CartItemListView(ListAPIView):
    """
    API dùng để lấy danh sách các sản phẩm trong giỏ hàng (user hoặc guest).
    """
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None

        # Nếu chưa có session_key thì tạo mới
        if not user and not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key if not user else None

        # Lấy cart items theo user hoặc session_key
        filter_kwargs = {'removed': False}
        if user:
            filter_kwargs['user'] = user
        else:
            filter_kwargs['user'] = None
            filter_kwargs['session_key'] = session_key

        cart_items = CartItem.objects.select_related("variant_product").filter(**filter_kwargs)

        serializer = self.get_serializer(cart_items, many=True, context={'user': user})
        total_quantity = cart_items.aggregate(total=Sum('quantity'))['total'] or 0

        return Response({
            'cart_items': serializer.data,
            'total_quantity': total_quantity
        })
