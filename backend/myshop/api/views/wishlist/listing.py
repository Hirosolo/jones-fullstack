#path: myshop/api/views/wishlist/listing.py
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView

from myshop.api.serializers import WishListSerializer
from myshop.models import WishList
from utils.api.common import ItemsListPagination


@extend_schema(
    responses={200: WishListSerializer(many=True)},
    summary="Danh sách sản phẩm yêu thích của người dùng",
    description="Trả về danh sách sản phẩm yêu thích của người dùng đã đăng nhập."
)
class UserWishListView(ListAPIView):
    """
    Danh sách sản phẩm yêu thích của người dùng.
    """
    serializer_class = WishListSerializer
    pagination_class = ItemsListPagination

    def get_queryset(self):
        user = self.request.user
        return (WishList.objects.filter(user=user, removed=False)
                .select_related('product')
                .filter(product__is_available=True).order_by('-created_at'))
