from django.apps import AppConfig


class MyshopConfig(AppConfig):
    """
    Cấu hình cho app myshop
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myshop'

    def ready(self):
        """
        Đăng ký signal khi app được load
        """
        try:
            import myshop.signals
        except ImportError:
            pass
