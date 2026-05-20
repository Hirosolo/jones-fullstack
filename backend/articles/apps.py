from django.apps import AppConfig


class ArticlesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'articles'

    def ready(self):
        """
        Đăng ký signal khi app được load
        """
        try:
            import articles.signals
        except ImportError:
            pass
