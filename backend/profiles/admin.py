from django.contrib import admin

from profiles.models import Profile, Shipping


class ShippingInline(admin.StackedInline):
    """
    Hiển thị Shipping trong trang Profile
    """
    model = Shipping
    extra = 1


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'email', 'code']
    list_display_links = ['full_name', 'user', 'code']
    autocomplete_fields = ['user']
    readonly_fields = ('code',)
    inlines = [ShippingInline]

@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ['address_book_name', 'is_default', 'profile']
    list_display_links = ['address_book_name',]