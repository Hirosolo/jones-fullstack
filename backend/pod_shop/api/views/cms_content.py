"""
CMS site-content singleton API.

GET  /api/shop/cms/site-content/        — public read (whatever's in the DB
                                          gets rendered on the public site
                                          anyway, so no auth needed).
POST /api/shop/cms/site-content/save/   — admin write, X-Admin-Key required.
"""
import os
from functools import wraps

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pod_shop.models import CMSContent


def admin_api_key_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        admin_key = request.headers.get('X-Admin-Key', '')
        expected_key = (
            getattr(settings, 'ADMIN_API_KEY', None)
            or os.environ.get('ADMIN_API_KEY', '')
        )
        if not expected_key or admin_key != expected_key:
            return Response(
                {'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED
            )
        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(['GET'])
@permission_classes([AllowAny])
def cms_content_get_view(request):
    """Read the singleton CMS payload. Empty dict if never written."""
    obj = CMSContent.get_solo()
    return Response(obj.payload or {})


@api_view(['POST'])
@permission_classes([AllowAny])
@admin_api_key_required
def cms_content_set_view(request):
    """Replace the singleton CMS payload."""
    payload = request.data
    if not isinstance(payload, dict):
        return Response(
            {'error': 'Expected a JSON object as request body.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    obj = CMSContent.get_solo()
    obj.payload = payload
    obj.save()
    return Response({'success': True, 'updated_at': obj.updated_at.isoformat()})
