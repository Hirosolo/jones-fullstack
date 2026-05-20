# path: profiles/api/urls.py

from django.urls import path

from profiles.api.views.address_book import listing as shipping_get
from profiles.api.views.address_book import post as shipping_post

app_name = 'profiles_api'

urlpatterns = [
    path('shipping-addresses/',
         shipping_get.get_shipping_addresses, name='get_shipping_addresses_api'),
    path('shipping-addresses/manage/',
         shipping_post.manage_shipping_address, name='manage_shipping_address_api'),
    path('shipping-addresses/delete/<int:pk>',
         shipping_post.delete_shipping_address, name='delete_shipping_address_api'),
]
