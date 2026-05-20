from django.apps import AppConfig


class MediaLibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'media_library'
    verbose_name = 'Media Library'

    def ready(self):
        from django.contrib import admin
        from django.apps import apps

        # Strip every admin registration except MediaAsset so the admin UI
        # shows only the image upload section. Done in ready() to run after
        # all other apps have registered their models.
        keep = {('media_library', 'mediaasset')}
        for model, _ in list(admin.site._registry.items()):
            key = (model._meta.app_label, model._meta.model_name)
            if key not in keep:
                try:
                    admin.site.unregister(model)
                except admin.sites.NotRegistered:
                    pass

        admin.site.site_header = 'Jones Media'
        admin.site.site_title = 'Jones Media'
        admin.site.index_title = 'Upload images'
