# path: myshop/api/views/review/post.py

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied

from myshop.api.serializers import ReviewCreateUpdateSerializer
from myshop.models import Product, Review


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='product_code',
            type=str,
            description='Mã sản phẩm cần đánh giá',
            required=False
        ),
        OpenApiParameter(
            name='product_slug',
            type=str,
            description='Slug của sản phẩm cần đánh giá',
            required=False
        )
    ],
    responses={200: ReviewCreateUpdateSerializer(many=True)},
    summary='API để tạo đánh giá sản phẩm.',
    description='API này cho phép người dùng tạo đánh giá cho sản phẩm. Người dùng có thể là khách hoặc đã đăng nhập.'
)
class ProductReviewCreateView(generics.CreateAPIView):
    """
    API để tạo đánh giá sản phẩm
    """
    serializer_class = ReviewCreateUpdateSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        product_code = self.request.query_params.get("product_code")
        product_slug = self.request.query_params.get("product_slug")

        if product_code:
            product = get_object_or_404(Product, code=product_code)
        elif product_slug:
            product = get_object_or_404(Product, slug=product_slug)
        else:
            raise NotFound("Missing product_code or product_slug.")

        # Kiểm tra profile nếu user đăng nhập
        profile = None
        if self.request.user.is_authenticated:
            profile = getattr(self.request.user, "profile", None)
            if Review.objects.filter(profile=profile, product=product).exists():
                raise ValidationError("You have already reviewed this product.")

        serializer.save(
            profile=profile,  # None nếu anonymous
            product=product,
            status=False  # chưa duyệt
        )

