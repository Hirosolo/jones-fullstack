from django.apps import AppConfig


class PodShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pod_shop'

    def ready(self):
        """
        Đăng ký signal khi app được load
        """
        try:
            import pod_shop.signals
        except ImportError:
            pass