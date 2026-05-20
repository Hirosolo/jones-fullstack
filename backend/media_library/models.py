import os
from django.db import models
from django.utils.text import slugify


def slugified_upload_to(instance, filename):
    """Lowercase + hyphenate the filename (stripping the extension first),
    then reattach a lowercase extension. This keeps product image URLs SEO-
    friendly: /images/tampa-bay-buccaneers-50th-anniversary-1976-2026-1.jpg
    instead of the admin-uploaded `Tampa_Bay_Buccaneers_.._1.JPG`.
    """
    stem, ext = os.path.splitext(filename)
    slug = slugify(stem) or 'image'
    return f'{slug}{ext.lower()}'


class MediaAsset(models.Model):
    """Simple image upload record. The file lives on the configured storage
    (GCS in prod, local FS in dev); the public URL is derived from
    MEDIA_URL / GS_CUSTOM_ENDPOINT in settings."""

    image = models.ImageField(upload_to=slugified_upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Image'
        verbose_name_plural = 'Images'

    def __str__(self):
        return self.image.name if self.image else f'MediaAsset #{self.pk}'
