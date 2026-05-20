from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from .models import MediaAsset


class _MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class _MultiFileField(forms.FileField):
    """Form field accepting multiple files at once.
    Django 5 ships the widget but not the field, so define it once."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', _MultiFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data]
        return [single(data, initial)]


class BulkMediaUploadForm(forms.Form):
    images = _MultiFileField(
        label='Images',
        help_text='Giữ Ctrl/Cmd để chọn nhiều file một lúc.',
    )


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'image_name', 'public_url', 'uploaded_at')
    readonly_fields = ('uploaded_at', 'public_url_display', 'preview')
    fields = ('image', 'preview', 'public_url_display', 'uploaded_at')
    list_per_page = 50
    change_list_template = 'admin/media_library/mediaasset/change_list.html'

    def thumbnail(self, obj):
        if not obj.image:
            return ''
        return format_html(
            '<img src="{}" style="height:60px;width:60px;object-fit:cover;border-radius:4px" />',
            obj.image.url,
        )
    thumbnail.short_description = ''

    def image_name(self, obj):
        return obj.image.name if obj.image else ''
    image_name.short_description = 'File'

    def public_url(self, obj):
        if not obj.image:
            return ''
        return format_html(
            '<a href="{0}" target="_blank" style="font-family:monospace">{0}</a>',
            obj.image.url,
        )
    public_url.short_description = 'URL'

    def public_url_display(self, obj):
        if not obj.image:
            return '(save first)'
        return format_html(
            '<div style="display:flex;gap:8px;align-items:center">'
            '<input value="{0}" readonly style="flex:1;padding:6px;font-family:monospace" onclick="this.select()" />'
            '<button type="button" onclick="navigator.clipboard.writeText(\'{0}\');this.innerText=\'Copied!\';setTimeout(()=>this.innerText=\'Copy\',1500)">Copy</button>'
            '</div>',
            obj.image.url,
        )
    public_url_display.short_description = 'Public URL (paste into FE admin)'

    def preview(self, obj):
        if not obj.image:
            return '(save first)'
        return format_html(
            '<img src="{}" style="max-width:320px;max-height:320px;border-radius:6px" />',
            obj.image.url,
        )
    preview.short_description = 'Preview'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'bulk-upload/',
                self.admin_site.admin_view(self.bulk_upload_view),
                name='media_library_mediaasset_bulk_upload',
            ),
        ]
        return custom + urls

    def bulk_upload_view(self, request):
        if request.method == 'POST':
            form = BulkMediaUploadForm(request.POST, request.FILES)
            files = request.FILES.getlist('images')
            if form.is_valid() and files:
                created = []
                for f in files:
                    asset = MediaAsset.objects.create(image=f)
                    created.append(asset)
                self.message_user(
                    request,
                    f'Đã upload {len(created)} ảnh.',
                    messages.SUCCESS,
                )
                return redirect('admin:media_library_mediaasset_changelist')
            if not files:
                form.add_error('images', 'Phải chọn ít nhất 1 file.')
        else:
            form = BulkMediaUploadForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Bulk upload images',
            'form': form,
            'opts': self.model._meta,
            'has_view_permission': True,
        }
        return render(request, 'admin/media_library/mediaasset/bulk_upload.html', context)
