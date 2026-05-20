# path: utils/api/views/main_menu/listing.py

from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from utils.api.serializers import MainMenuSerializer
from utils.models import MainMenu


@extend_schema(
    summary="API Main Menu",
    description="List main menu"
)
class MenuListAPIView(ListAPIView):
    """
    Danh sách menu
    """
    queryset = MainMenu.objects.prefetch_related('menu_groups_set__menu_items_set').all()
    serializer_class = MainMenuSerializer
    permission_classes = [AllowAny]

