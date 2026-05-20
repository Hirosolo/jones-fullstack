from django.apps import AppConfig


class UtilsConfig(AppConfig):
    """
    Cấu hình cho app Utils
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'utils'

    def ready(self):
        """
        Đăng ký signal khi app được load
        """
        try:
            import utils.signals
        except ImportError:
            pass
