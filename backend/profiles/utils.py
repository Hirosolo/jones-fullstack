from utils.common import resolve_upload


def upload_profile_avatar(instance, filename):
    """
    Upload profile avatar
    """
    return resolve_upload(instance.user, filename, "profiles")