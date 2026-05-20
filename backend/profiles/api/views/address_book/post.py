# profiles/api/views/address_book/post.py

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from profiles.api.serializers import ShippingAddressSerializer
from profiles.models import Profile, Shipping


@extend_schema(
    summary="Tạo hoặc cập nhật địa chỉ giao hàng",
    description="Tạo hoặc cập nhật địa chỉ giao hàng của người dùng. Nếu có id trong request, địa chỉ sẽ được cập nhật. Nếu không có id, địa chỉ mới sẽ được tạo.",
    request=ShippingAddressSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "message": {"type": "string"},
                "shippingAddress": {"type": "object", "additionalProperties": True}
            }
        },
        200: {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "message": {"type": "string"},
                "shippingAddress": {"type": "object", "additionalProperties": True}
            }
        },
        400: {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "message": {"type": "string"},
                "errors": {"type": "object", "additionalProperties": True}
            }
        },
        404: {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "message": {"type": "string"}
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manage_shipping_address(request):
    """
    Create or update shipping address based on presence of shipping_id in request data
    """
    user = request.user
    data = request.data.copy()
    shipping_id = data.get('id')

    try:
        profile = Profile.objects.get(user=user)

        if shipping_id:
            try:
                shipping_address = Shipping.objects.get(
                    pk=shipping_id,
                    profile=profile,
                    removed=False
                )

                serializer = ShippingAddressSerializer(
                    shipping_address,
                    data=data,
                    partial=True
                )

                if serializer.is_valid():
                    updated_address = serializer.save()
                    return Response({
                        'ok': True,
                        'message': 'Shipping address updated successfully',
                        'shippingAddress': ShippingAddressSerializer(updated_address).data
                    })

                return Response({
                    'ok': False,
                    'message': 'Invalid data provided',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            except Shipping.DoesNotExist:
                return Response({
                    'ok': False,
                    'message': 'Shipping address not found or not accessible'
                }, status=status.HTTP_404_NOT_FOUND)

        else:
            serializer = ShippingAddressSerializer(data=data)
            if serializer.is_valid():
                shipping_address = serializer.save(profile=profile)
                return Response({
                    'ok': True,
                    'message': 'Shipping address created successfully',
                    'shippingAddress': ShippingAddressSerializer(shipping_address).data
                }, status=status.HTTP_201_CREATED)

            return Response({
                'ok': False,
                'message': 'Invalid data provided',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Profile.DoesNotExist:
        return Response({
            'ok': False,
            'message': 'User profile not found'
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    summary="Xóa địa chỉ giao hàng",
    description="Xóa địa chỉ giao hàng của người dùng. Địa chỉ sẽ được đánh dấu là đã xóa thay vì bị xóa hoàn toàn.",
    responses={
        200: {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "message": {"type": "string"}
            }
        },
        404: {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean"},
                "message": {"type": "string"}
            }
        }
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_shipping_address(request, pk):
    """
    Soft delete a shipping address (mark as removed)
    """
    user = request.user

    try:
        profile = Profile.objects.get(user=user)

        try:
            shipping_address = Shipping.objects.get(pk=pk, profile=profile, removed=False)

            # Soft delete by marking as removed
            shipping_address.removed = True
            shipping_address.save()

            return Response({
                'ok': True,
                'message': 'Shipping address deleted successfully'
            })

        except Shipping.DoesNotExist:
            return Response({
                'ok': False,
                'message': 'Shipping address not found or not accessible'
            }, status=status.HTTP_404_NOT_FOUND)

    except Profile.DoesNotExist:
        return Response({
            'ok': False,
            'message': 'User profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
