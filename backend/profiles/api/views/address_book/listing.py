# profiles/api/views/address_book/listing.py

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from profiles.api.serializers import ShippingAddressSerializer
from profiles.models import Profile, Shipping


@extend_schema(
    tags=['Shipping Address'],
    description="Lấy danh sách địa chỉ giao hàng của người dùng",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_shipping_addresses(request):
    """
    Get user's shipping addresses using JWT token authentication.
    The user is identified by the JWT token in the Authorization header.
    Only returns non-removed shipping addresses.
    """
    user = request.user

    try:
        profile = Profile.objects.get(user=user)
        shipping_addresses = Shipping.objects.filter(
            profile=profile,
            removed=False
        ).order_by('-is_default', '-id')

        serializer = ShippingAddressSerializer(shipping_addresses, many=True)

        return Response({
            'ok': True,
            'shippingAddresses': serializer.data
        })
    except Profile.DoesNotExist:
        return Response({
            'ok': False,
            'message': 'User profile not found'
        }, status=status.HTTP_404_NOT_FOUND)

