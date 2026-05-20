# path: utils/api/serializers.py
from django.conf import settings
from django.template.defaultfilters import truncatechars
from django.templatetags.static import static
from django.utils.html import strip_tags
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from utils.api.common import OpenGraphSerializer
from utils.models import (HomeSlider, SubMenuItem, SubMenuGroup, MainMenu, FooterMenuItem, FooterMenuGroup,
                          StaticPage)


class HomeSliderSerializer(serializers.ModelSerializer):
    """
    Serializer cho model HomeSlider
    """
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HomeSlider
        fields = ['title', 'desc_safe', 'image_url', 'link', 'button_text', 'order', 'status']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return ''


class SubMenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer cho model SubMenuItem
    """
    class Meta:
        model = SubMenuItem
        fields = ['name', 'link', 'target', 'rel', 'order']


class SubMenuGroupSerializer(serializers.ModelSerializer):
    """
    Serializer cho model SubMenuGroup
    """
    items = SubMenuItemSerializer(many=True, read_only=True, source='menu_items_set')

    class Meta:
        model = SubMenuGroup
        fields = ['name', 'order', 'items']


class MainMenuSerializer(serializers.ModelSerializer):
    """
    Serializer cho model MainMenu
    """
    groups = SubMenuGroupSerializer(many=True, read_only=True, source='menu_groups_set')

    class Meta:
        model = MainMenu
        fields = ['name', 'link', 'target', 'rel', 'order', 'groups']


class FooterMenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer cho model FooterMenuItem
    """
    class Meta:
        model = FooterMenuItem
        fields = ['label', 'link', 'order', 'target', 'rel']


class FooterMenuGroupSerializer(serializers.ModelSerializer):
    """
    Serializer cho model FooterMenuGroup
    """
    items = FooterMenuItemSerializer(source='footer_menu_items', many=True, read_only=True)

    class Meta:
        model = FooterMenuGroup
        fields = ['title', 'order', 'items']


class StaticPageSerializer(serializers.ModelSerializer):
    """
    Serializer cho model StaticPage
    """
    open_graph = serializers.SerializerMethodField()

    @extend_schema_field(OpenGraphSerializer)
    def get_open_graph(self, obj: StaticPage):
        """
        Lấy dữ liệu Open Graph cho trang tĩnh
        """
        default_og_image = static('img/default.png')  # Ảnh mặc định
        images = (
            [obj.meta_image.url] if obj.meta_image
            else [default_og_image]
        )

        # Lấy tiêu đề và mô tả Open Graph
        title = obj.meta_title if obj.meta_title else obj.title
        desc = (
            obj.meta_desc if obj.meta_desc
            else truncatechars(strip_tags(obj.excerpt), 145) if obj.excerpt
            else settings.SITE_DESC
        )

        return {
            'title': title,
            'description': desc,
            'images': images,
            'url': obj.full_url()
        }

    class Meta:
        model = StaticPage
        fields = [
            'title', 'slug', 'excerpt_safe', 'status', 'meta_title',
            'meta_desc', 'meta_image', 'created_at', 'updated_at', 'open_graph'
        ]
