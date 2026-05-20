from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe


class ImageWidget(AdminFileWidget):
    """
    Hiển thị ảnh trong trang admin
    """
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and hasattr(value, 'url'):
            image_url = value.url
            output.append(f'<img src="{image_url}" style="max-width: 200px; max-height: 100%;"/>')
        output.append(super().render(name, value, attrs))
        return mark_safe(u''.join(output))
