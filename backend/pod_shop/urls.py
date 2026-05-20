from django.urls import path

from utils.views import fake_view, home_view

app_name = 'pod_shop'

urlpatterns = [
    path('', home_view, name='home_view'),
    path('p/<slug>/', fake_view, name='product_detail'),
    path('c/<slug>/', fake_view, name='category_detail'),
    path('b/<slug>/', fake_view, name='brand_detail'),
    path('t/<slug>/', fake_view, name='tags_detail'),
]
