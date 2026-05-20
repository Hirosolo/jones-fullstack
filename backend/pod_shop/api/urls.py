# path: pod_shop/api/urls.py

from django.urls import path

from pod_shop.api.views.brand import listing as brand_listing
from pod_shop.api.views.brand import admin_crud as brand_admin
from pod_shop.api.views.category import listing as category_listing
from pod_shop.api.views.category import admin_crud as category_admin
from pod_shop.api.views.tags import listing as tags_listing
from pod_shop.api.views.tags import admin_crud as tag_admin
from pod_shop.api.views.product import detail as product_detail
from pod_shop.api.views.product import listing as product_listing
from pod_shop.api.views.product import admin_crud as product_admin
from pod_shop.api.views.product import slug_aliases as product_slug_aliases
from pod_shop.api.views.review import listing as review_listing
from pod_shop.api.views.review import post as review_post
from pod_shop.api.views.wishlist import detail as wishlist_detail
from pod_shop.api.views.wishlist import listing as wishlist_listing
from pod_shop.api.views.wishlist import post as wishlist_post
from pod_shop.api.views.cart import post as cart_post
from pod_shop.api.views.cart import listing as cart_listing
from pod_shop.api.views.cart import detail as cart_detail
from pod_shop.api.views import cms_content as cms_content_views

app_name = 'pod_shop_api'

urlpatterns = [
    path('brands-list/',
         brand_listing.BrandsListView.as_view(), name='brands_list_api'),
    path('brand-groups/',
         brand_listing.BrandGroupsView.as_view(), name='brand_groups_api'),
    path('brand-product-list/',
         brand_listing.BrandProductsListView.as_view(), name='brand_product_list_api'),
    path('categories-list/',
        category_listing.CategoriesListView.as_view(), name='categories_list_api'),
    path('category-product-list/',
        category_listing.CategoryProductsListView.as_view(), name='category_product_list_api'),
    path('tags-list/',
        tags_listing.TagsListView.as_view(), name='tags_list_api'),
    path('tag-product-list/',
        tags_listing.TagProductsListView.as_view(), name='tag_product_list_api'),
    path('product-detail/',
        product_detail.product_detail_view, name='product_detail_api'),
    path('featured-products/',
        product_listing.featured_products_view, name='featured_products_list_api'),
    path('best-selling-products/',
        product_listing.best_selling_products_view, name='best_selling_products_list_api'),
    path('latest-products/',
        product_listing.latest_products_view, name='latest_products_list_api'),
    path('weekly-bestsellers/',
        product_listing.weekly_bestsellers_view, name='weekly_bestsellers_list_api'),
    path('product-slug-aliases/',
        product_slug_aliases.product_slug_aliases_view, name='product_slug_aliases_api'),
    path('cms/site-content/',
        cms_content_views.cms_content_get_view, name='cms_content_get_api'),
    path('cms/site-content/save/',
        cms_content_views.cms_content_set_view, name='cms_content_set_api'),
    path('search-products/',
        product_listing.search_products_view, name='search_products_api'),
    path('sitemap-products/',
        product_listing.sitemap_products_view, name='sitemap_products_api'),
    path('product-review/',
        review_listing.ProductReviewListView.as_view(), name='product_review_list_api'),
    path('product-review-create/',
        review_post.ProductReviewCreateView.as_view(), name='product_review_create_api'),
    path('get-wishlist/',
        wishlist_listing.UserWishListView.as_view(), name='wishlist_list_api'),
    path('check-item-wishlist/',
        wishlist_detail.check_item_wishlist, name='check_item_wishlist_api'),
    path('action-to-wishlist/',
        wishlist_post.action_to_wishlist, name='action_to_wishlist_api'),

    # Cart API
    path('add-to-cart/',
        cart_post.add_to_cart_view, name='add_to_cart_api'),
    path('cart-items/',
        cart_listing.get_cart_items_view, name='cart_items_list_api'),
    path('remove-cart-item/',
        cart_post.remove_from_cart_view, name='remove_cart_item_api'),
    path('update-cart-quantity/',
        cart_post.update_cart_quantity_view, name='update_cart_quantity_api'),
    path('create-order/',
         cart_post.create_order_view, name='create_order_api'),
    path('merge-cart-on-login/',
        cart_post.merge_cart_on_login_view, name='merge_cart_on_login_api'),
    path('get-order-list/',
        cart_listing.list_orders_view, name='list_orders_view_api'),
    path('get-order-detail/',
        cart_detail.order_detail_view, name='get_order_detail_api'),

    # Admin Product CRUD API
    path('admin-products/',
        product_admin.admin_product_list, name='admin_product_list_api'),
    path('admin-products/options/',
        product_admin.admin_product_options, name='admin_product_options_api'),
    path('admin-products/create/',
        product_admin.admin_product_create, name='admin_product_create_api'),
    path('admin-products/<int:pk>/update/',
        product_admin.admin_product_update, name='admin_product_update_api'),
    path('admin-products/<int:pk>/delete/',
        product_admin.admin_product_delete, name='admin_product_delete_api'),

    # Admin Brand CRUD API
    path('admin-brands/',
        brand_admin.admin_brand_list, name='admin_brand_list_api'),
    path('admin-brands/create/',
        brand_admin.admin_brand_create, name='admin_brand_create_api'),
    path('admin-brands/<int:pk>/update/',
        brand_admin.admin_brand_update, name='admin_brand_update_api'),
    path('admin-brands/<int:pk>/delete/',
        brand_admin.admin_brand_delete, name='admin_brand_delete_api'),

    # Admin Category CRUD API
    path('admin-categories/',
        category_admin.admin_category_list, name='admin_category_list_api'),
    path('admin-categories/create/',
        category_admin.admin_category_create, name='admin_category_create_api'),
    path('admin-categories/<int:pk>/update/',
        category_admin.admin_category_update, name='admin_category_update_api'),
    path('admin-categories/<int:pk>/delete/',
        category_admin.admin_category_delete, name='admin_category_delete_api'),

    # Admin Tag CRUD API
    path('admin-tags/',
        tag_admin.admin_tag_list, name='admin_tag_list_api'),
    path('admin-tags/create/',
        tag_admin.admin_tag_create, name='admin_tag_create_api'),
    path('admin-tags/<int:pk>/update/',
        tag_admin.admin_tag_update, name='admin_tag_update_api'),
    path('admin-tags/<int:pk>/delete/',
        tag_admin.admin_tag_delete, name='admin_tag_delete_api'),
]