# path: utils/api/views/search/listing.py

from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from pod_shop.api.serializers import ProductSerializer
from pod_shop.models import Product
from utils.api.common import ItemsListPagination


@extend_schema(
    summary="Product Search API",
    description="Search across products catalog",
    tags=["Search"],
    parameters=[
        OpenApiParameter(
            name='q',
            description='Search query (searches in title, description, SKU)',
            required=False
        ),
        OpenApiParameter(
            name='page',
            description='Page number for pagination',
            required=False
        ),
        OpenApiParameter(
            name='page_size',
            description='Number of items per page (default: 10)',
            required=False
        )
    ],
)
class ProductSearchAPIView(APIView):
    """
    Search API endpoint for products
    """
    serializer_class = ProductSerializer  # Remove the parentheses
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user = request.user
        query = request.query_params.get('q', '')

        # Start with base query
        product_filter = Q(status='A')

        # Add search terms if provided
        if query:
            product_filter &= (
                Q(name__icontains=query)

            )

        # Query the products
        products = Product.objects.filter(product_filter).order_by('-created_at')
        # Use the ItemsListPagination for consistent pagination
        paginator = ItemsListPagination()
        page = paginator.paginate_queryset(products, request)

        # Serialize the products
        serializer = ProductSerializer(page, many=True, context={'user': user})

        # Return full serializer data
        return paginator.get_paginated_response(serializer.data)