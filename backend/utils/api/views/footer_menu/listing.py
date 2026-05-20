# path: utils/api/views/footer_menu/listing.py

from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from utils.api.serializers import FooterMenuGroupSerializer
from utils.models import FooterMenuGroup


@extend_schema(
    summary="API Footer Menu",
    description="List footer menu"
)
class FooterMenuListAPIView(ListAPIView):
    """
    Danh sách menu
    """
    queryset = FooterMenuGroup.objects.prefetch_related('footer_menu_items').all()
    serializer_class = FooterMenuGroupSerializer
    permission_classes = [AllowAny]

