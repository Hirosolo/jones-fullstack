# utils/context_processors.py


def site_common(request):
    """
    Thêm thông tin trang web vào ngữ cảnh toàn trang.
    """
    from django.conf import settings
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DESC': settings.SITE_DESC,
        'SITE_URL': settings.SITE_URL,
        'SITE_LOGO': settings.SITE_LOGO,
        'SITE_FAVICON': settings.SITE_FAVICON,
        'SITE_META_IMAGE': settings.SITE_META_IMAGE,
        'PROFILE_AVATAR_DEFAULT': settings.PROFILE_AVATAR_DEFAULT,
    }