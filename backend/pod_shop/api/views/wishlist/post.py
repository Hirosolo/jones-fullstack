# path: pod_shop/api/views/wishlist/post.py

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from pod_shop.models import WishList, Product


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'code': {
                    'type': 'string',
                    'description': 'Mã sản phẩm (product.code)',
                },
                'slug': {
                    'type': 'string',
                    'description': 'Slug sản phẩm (product.slug)',
                },
                'action': {
                    'type': 'string',
                    'description': "Hành động: 'remove', 'remove-bulk' (mặc định là thêm vào danh sách yêu thích)",
                },
                'delete_list': {
                    'type': 'string',
                    'description': 'Danh sách ID wishlist để xóa hàng loạt (chỉ khi action = "remove-bulk")'
                    'Mỗi ID cách nhau bằng dấu "|".',
                }
            }
        }
    },
    responses={200: OpenApiTypes.OBJECT},
    summary="Thêm hoặc xóa sản phẩm khỏi danh sách yêu thích",
    description="Thêm hoặc xóa sản phẩm khỏi danh sách yêu thích của người dùng.\n"
                "Nếu không có action, sẽ thêm sản phẩm vào danh sách yêu thích.\n"
                "Nếu action là 'remove', sẽ xóa một sản phẩm khỏi danh sách yêu thích.\n"
                "Nếu action là 'remove-bulk', sẽ xóa nhiều sản phẩm khỏi danh sách yêu thích. \n"
                "Trường hợp xóa hàng loạt, cần cung cấp danh sách ID wishlist để xóa. \n"
                "Danh sách ID này được phân tách bằng dấu '|' (ví dụ: '1|2|3')."

)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def action_to_wishlist(request):
    """
    Thêm hoặc xóa sản phẩm khỏi danh sách yêu thích của người dùng.

    Các hành động được hỗ trợ:
    - Thêm sản phẩm vào danh sách yêu thích (mặc định nếu không có action).
    - Xóa một sản phẩm khỏi danh sách yêu thích (action = "remove").
    - Xóa nhiều sản phẩm khỏi danh sách yêu thích (action = "remove-bulk").

    Trường nhận vào:
    - `code`: mã sản phẩm (product.code)
    - `slug`: slug sản phẩm (product.slug)
    - `action`: 'remove', 'remove-bulk'
    - `delete_list`: danh sách ID wishlist để xóa hàng loạt
    """
    data = request.data
    user = request.user
    action = data.get('action', '')

    # === Trường hợp: Xóa hàng loạt ===
    if action == 'remove-bulk':
        ids = data.get('delete_list', '')
        ids = ids.split('|')
        count = WishList.objects.filter(user=user, id__in=ids).update(removed=True)
        return Response({
            'ok': True,
            'count': count,
            'action': action,
        })

    # === Xử lý thêm / xóa một sản phẩm ===
    code = data.get('code')
    slug = data.get('slug')

    # Ưu tiên tìm theo code, nếu không có thì tìm theo slug
    product = None
    if code:
        product = Product.objects.filter(code=code, status='A').first()
    elif slug:
        product = Product.objects.filter(slug=slug, status='A').first()

    if not product:
        return Response({
            'ok': False,
            'msg': 'Product not found or not available.'
        }, status=400)

    # === Xóa một sản phẩm khỏi danh sách yêu thích ===
    if action == 'remove':
        wishlist = WishList.objects.filter(user=user, product=product).first()
        if wishlist:
            wishlist.removed = True
            wishlist.save()

    # === Thêm một sản phẩm vào danh sách yêu thích ===
    else:
        wishlist, created = WishList.objects.get_or_create(user=user, product=product)
        wishlist.removed = False
        wishlist.save()

    # Đếm lại số lượng yêu thích
    num = WishList.objects.filter(user=user, removed=False).count()
    return Response({
        'ok': True,
        'num': num,
        'action': action,
    })
