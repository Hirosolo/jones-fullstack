from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """
    Cấu hình cho app profiles
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profiles'

    def ready(self):
        """
        Đăng ký signal khi app được load
        """
        try:
            import profiles.signals
        except ImportError:
            pass
