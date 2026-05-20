# path: utils/api/common.py
# Description: Định nghĩa các cấu hình chung cho API.

from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework import serializers


# Định nghĩa serializer
class SampleAuthSerializer(serializers.Serializer):
    ok = serializers.BooleanField()


# Decorator để mô tả schema
@extend_schema(
    responses=SampleAuthSerializer,
    summary="API mẫu cho việc xác thực",
    description="API mẫu cho việc xác thực"
)
@api_view(['GET'])
def sample_auth_view(request):
    """
    API mẫu cho việc xác thực
    """
    return Response({
        'ok': True
    })


class OpenGraphSerializer(serializers.Serializer):
    """
    Serializer cho dữ liệu Open Graph
    """
    title = serializers.CharField()
    description = serializers.CharField()
    images = serializers.ListField(child=serializers.CharField())
    url = serializers.CharField()


class ItemsListPagination(PageNumberPagination):
    """
    Phân trang cho danh sách items
    """
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response(
            {
                'total': self.page.paginator.count,
                'current': self.page.number,
                'num_pages': self.page.paginator.num_pages,
                'items': data,
            }
        )

