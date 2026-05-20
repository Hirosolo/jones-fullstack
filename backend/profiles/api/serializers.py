# profiles/api/serializers.py
from os import removedirs

from allauth.socialaccount.models import SocialAccount
from dj_rest_auth.serializers import UserDetailsSerializer
from django.contrib.auth import get_user_model
from django.db.models import Sum
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from profiles.models import Shipping

User = get_user_model()
class SocialAccountSerializer(serializers.ModelSerializer):
    """
    Serializer cho model SocialAccount
    """
    class Meta:
        model = SocialAccount
        fields = (
            'provider', 'uid', 'extra_data'
        )

    provider = serializers.CharField()
    uid = serializers.CharField()
    extra_data = serializers.JSONField()


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Profile
    """
    class Meta:
        model = SocialAccount
        fields = (
            '__all__'
        )


class CustomUserDetailsSerializer(UserDetailsSerializer):
    """
    Serializer cho model User
    """
    social_accounts = serializers.SerializerMethodField()
    code = serializers.CharField(source='user_profile_set.code', read_only=True)
    wish_list_count = serializers.SerializerMethodField()
    cart_item_count = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='user_profile_set.created_at', read_only=True)
    updated_at = serializers.DateTimeField(source='user_profile_set.updated_at', read_only=True)
    ip = serializers.CharField(source='user_profile_set.ip', read_only=True)
    ua = serializers.CharField(source='user_profile_set.ua', read_only=True)
    metadata = serializers.JSONField(source='user_profile_set.metadata', read_only=True)

    @extend_schema_field(SocialAccountSerializer(many=True))
    def get_social_accounts(self, obj):
        social_accounts = SocialAccount.objects.filter(user=obj)
        return [{
            'provider': account.provider,
            'picture': account.extra_data.get('picture', '') if account.provider == 'google' else ''
        } for account in social_accounts]

    @extend_schema_field(serializers.IntegerField())
    def get_wish_list_count(self, obj):
        return obj.user_wishlists.filter(removed=False).count() if hasattr(obj, 'user_wishlists') else 0

    # Lấy số lượng sản phẩm trong giỏ hàng, bao gồm cả số lượng của mỗi sản phẩm
    @extend_schema_field(serializers.IntegerField())
    def get_cart_item_count(self, obj):
        return obj.cart_items.filter(removed=False).aggregate(total=Sum('quantity'))['total'] or 0 if hasattr(obj, 'cart_items') else 0

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + (
            'social_accounts',
            'code',
            'created_at',
            'updated_at',
            'ip',
            'ua',
            'metadata',
            'wish_list_count',
            'cart_item_count',
        )


class ShippingAddressSerializer(serializers.ModelSerializer):
    """
    Serializer cho model Shipping
    """
    class Meta:
        model = Shipping
        fields = [
            'id', 'address_book_name', 'first_name', 'last_name',
            'email', 'street', 'state', 'city',
            'country', 'zip_code', 'is_default'
        ]

