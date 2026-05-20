# path: utils/api/urls.py

from django.urls import path

from utils.api.views.footer_menu import listing as footer_menu_listing
from utils.api.views.home_slider import listing as home_slider_listing
from utils.api.views.main_menu import listing as main_menu_listing
from utils.api.views.static_page import detail as static_page_detail
from utils.api.views.search import listing as search_listing

app_name = 'utils_api'

urlpatterns = [
    # Home API
    path('sliders/',
        home_slider_listing.HomeSliderViewAPI.as_view(), name='home_slider_api'),

    # Menu API
    path('main-menus/',
        main_menu_listing.MenuListAPIView.as_view(), name='main_menu_api'),
    path('footer-menus/',
        footer_menu_listing.FooterMenuListAPIView.as_view(), name='footer_menu_api'),
    # Search API
     path('search/', search_listing.ProductSearchAPIView.as_view(), name='search_api'),
    # Static Page API
    path('static-pages/',
        static_page_detail.StaticPageDetailView.as_view(), name='static_page_detail_api'),
]

