# path: myshop/api/urls.py

from django.urls import path

from myshop.api.views.brand import listing as brand_listing
from myshop.api.views.category import listing as category_listing
from myshop.api.views.product import detail as product_detail
from myshop.api.views.product import listing as product_listing
from myshop.api.views.product.listing import ProductListView
from myshop.api.views.review import listing as review_listing
from myshop.api.views.review import post as review_post
from myshop.api.views.tags import listing as tags_listing
from myshop.api.views.wishlist import detail as wishlist_detail
from myshop.api.views.wishlist import listing as wishlist_listing
from myshop.api.views.wishlist import post as wishlist_post
from myshop.api.views.cart import post as cart_post
from myshop.api.views.cart import listing as cart_listing

app_name = 'myshop_api'

urlpatterns = [
    # Specific patterns FIRST to avoid conflicts
    path('categories-list/',
        category_listing.CategoriesListView.as_view(), name='categories_list_api'),
    path('category-product-list/',
        category_listing.CategoryProductsListView.as_view(), name='category_product_list_api'),
    path('brands-list/',
        brand_listing.BrandsListView.as_view(), name='brands_list_api'),
    path('brand-product-list/',
        brand_listing.BrandProductsListView.as_view(), name='brand_product_list_api'),
    path('tags-list/',
        tags_listing.TagsListView.as_view(), name='tags_list_api'),
    path('tag-product-list/',
        tags_listing.TagProductsListView.as_view(), name='tag_product_list_api'),
    path('featured-products/',
        product_listing.featured_products_view, name='featured_products_list_api'),
    path('best-selling-products/',
        product_listing.best_selling_products_view, name='best_selling_products_list_api'),
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
        cart_listing.CartItemListView.as_view(), name='cart_items_list_api'),
    path('remove-cart-item/',
        cart_post.remove_from_cart_view, name='remove_cart_item_api'),
    path('update-cart-quantity/',
        cart_post.update_cart_quantity_view, name='update_cart_quantity_api'),
    path('create-order/',
         cart_post.create_order_view, name='create_order_api'),
    path('merge-cart-on-login/',
        cart_post.merge_cart_on_login_view, name='merge_cart_on_login_api'),

    # Product detail patterns
    path('product-detail/',
        product_detail.product_detail_view, name='product_detail_api'),
    path('', ProductListView.as_view(), name='product_list_api'),

    # Slug pattern MUST be LAST to avoid conflicts with other patterns
    path('<slug:slug>/',
        product_detail.product_detail_view, name='product_detail_by_slug_api'),

]