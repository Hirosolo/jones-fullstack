from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from utils.forms import HomeSliderAdminForm, StaticPageAdminForm
from utils.models import HomeSlider, SubMenuItem, SubMenuGroup, \
    MainMenu, FooterMenuGroup, FooterMenuItem, StaticPage
from utils.widgets import ImageWidget


@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    """
    Quản lý slider trên trang chủ
    """
    list_display = ('has_image', 'title', 'link', 'order', 'status')
    list_display_links = ('title',)
    search_fields = ('title', 'link')
    ordering = ('order', 'status')
    list_per_page = 10
    list_max_show_all = 100
    empty_value_display = '-empty-'
    save_on_top = True
    form = HomeSliderAdminForm

    @admin.display(description='Hình ảnh')
    def has_image(self, obj: HomeSlider):
        if obj.image:
            s = obj.image.url  # Đường dẫn ảnh
            i = f'<img src="{s}" width="120" height="80" />'  # Ảnh slider với kích thước 120x80
            h = f'<a href="{s}" target="_blank" rel="noopener">{i}</a>'  # Tạo link ảnh slider
            return format_html(h)  # Trả về ảnh slider
        return '-empty-'  # Trả về -empty- nếu không có slider

    formfield_overrides = {
        models.ImageField: {'widget': ImageWidget}
    }


class SubMenuItemInline(admin.TabularInline):
    """
    Hiển thị danh sách các mục con trong nhóm menu
    """
    model = SubMenuItem
    extra = 0
    fields = ('name', 'link', 'target', 'rel', 'order')
    show_change_link = True


class SubMenuGroupInline(admin.StackedInline):
    """
    Hiển thị danh sách các nhóm menu trong menu chính
    """
    model = SubMenuGroup
    extra = 0
    fields = ('name', 'order')
    show_change_link = True


@admin.register(MainMenu)
class MainMenuAdmin(admin.ModelAdmin):
    """
    Quản lý menu chính
    """
    list_display = ('name', 'link', 'target', 'rel', 'order')
    list_editable = ('order',)
    ordering = ('order',)
    search_fields = ('name',)
    inlines = [SubMenuGroupInline]
    save_on_top = True


@admin.register(SubMenuGroup)
class SubMenuGroupAdmin(admin.ModelAdmin):
    """
    Quản lý nhóm menu con
    """
    list_display = ('name', 'main_menu', 'order')
    list_editable = ('order',)
    list_filter = ('main_menu',)
    ordering = ('main_menu', 'order')
    search_fields = ('name',)
    inlines = [SubMenuItemInline]
    save_on_top = True


@admin.register(SubMenuItem)
class SubMenuItemAdmin(admin.ModelAdmin):
    """
    Quản lý mục menu con
    """
    list_display = ('name', 'link', 'target', 'rel', 'group', 'order')
    list_editable = ('order',)
    list_filter = ('group',)
    ordering = ('group', 'order')
    search_fields = ('name',)
    save_on_top = True


class FooterMenuItemInline(admin.TabularInline):
    """
    Hiển thị danh sách các mục trong nhóm menu chân trang
    """
    model = FooterMenuItem
    extra = 0
    fields = ('group', 'label', 'link', 'order', 'target', 'rel')
    ordering = ['order']


@admin.register(FooterMenuGroup)
class FooterMenuGroupAdmin(admin.ModelAdmin):
    """
    Quản lý nhóm menu chân trang
    """
    list_display = ('title', 'order')
    ordering = ['order']
    inlines = [FooterMenuItemInline]
    save_on_top = True


@admin.register(FooterMenuItem)
class FooterMenuItemAdmin(admin.ModelAdmin):
    """
    Quản lý mục menu chân trang
    """
    list_display = ('label', 'group', 'link', 'order', 'target', 'rel')
    list_filter = ('group',)
    search_fields = ('label', 'link')
    ordering = ['group', 'order']
    save_on_top = True


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    """
    Quản lý các trang tĩnh
    """
    list_display = ('title', 'slug', 'status', 'excerpt')
    list_editable = ('status',)
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    form = StaticPageAdminForm
    save_on_top = True

