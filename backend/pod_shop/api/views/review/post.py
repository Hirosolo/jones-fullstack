# path: pod_shop/api/views/review/post.py

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound, ValidationError

from pod_shop.api.serializers import ReviewCreateUpdateSerializer
from pod_shop.models import Product, Review


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'product_code': {
                    'type': 'string',
                    'description': 'Mã sản phẩm cần đánh giá',
                },
                'product_slug': {
                    'type': 'string',
                    'description': 'Slug của sản phẩm cần đánh giá',
                },
                'rating': {
                    'type': 'integer',
                    'description': 'Đánh giá của người dùng (1-5) - Bắt buộc',
                },
                'reviewer_name': {
                    'type': 'string',
                    'description': 'Tên người đánh giá (bắt buộc nếu có opinion/content và không đăng nhập)',
                },
                'subject': {
                    'type': 'string',
                    'description': 'Tiêu đề đánh giá / Opinion (optional)',
                },
                'content': {
                    'type': 'string',
                    'description': 'Nội dung đánh giá chi tiết (optional)',
                }
            },
        }
    },
    responses={200: ReviewCreateUpdateSerializer(many=True)},
    summary='API để tạo đánh giá sản phẩm.',
    description='''API này cho phép người dùng tạo đánh giá cho sản phẩm.
    
    **Logic validation:**
    - Nếu chỉ đánh giá số sao (không có opinion/content): KHÔNG cần điền tên
    - Nếu có opinion (subject) HOẶC review chi tiết (content): BẮT BUỘC phải điền tên (nếu không đăng nhập)
    
    **Người dùng có thể là khách (anonymous) hoặc đã đăng nhập.**'''
)
class ProductReviewCreateView(generics.CreateAPIView):
    """
    API để tạo đánh giá sản phẩm
    """
    serializer_class = ReviewCreateUpdateSerializer
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        """
        Thêm request vào context để serializer có thể truy cập
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        product_code = self.request.data.get("product_code")
        product_slug = self.request.data.get("product_slug")

        if product_code:
            product = get_object_or_404(Product, code=product_code)
        elif product_slug:
            product = get_object_or_404(Product, slug=product_slug)
        else:
            raise NotFound("Missing product_code or product_slug.")

        # Kiểm tra user nếu user đăng nhập
        user = None
        if self.request.user.is_authenticated:
            user = getattr(self.request.user, "user", None)
            if Review.objects.filter(user=user, product=product).exists():
                raise ValidationError("You have already reviewed this product.")

        serializer.save(
            user=user,  # None nếu anonymous
            product=product,
            status=False  # chưa duyệt
        )

