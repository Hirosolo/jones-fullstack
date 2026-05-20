# path: utils/api/views/home_slider/listing.py

from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from utils.api.serializers import HomeSliderSerializer
from utils.models import HomeSlider


@extend_schema(
    summary="Slider trang chủ",
    description="Danh sách tất cả các slider trang chủ"
)
class HomeSliderViewAPI(ListAPIView):
    """
    Danh sách tất cả các slider trang chủ
    """
    serializer_class = HomeSliderSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return HomeSlider.objects.filter(status=True).order_by('order')

