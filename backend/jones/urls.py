"""
URL configuration for jones project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView, TokenBlacklistView

from utils.api import common
from utils.views import fake_view
from profiles.api.views.account.social_auth import GoogleLogin
from django.http import HttpResponse


def robots_txt(request):
    content = [
        "User-agent: *",
        "Disallow: /",
        "Disallow: /acp/",
        "",
        "# This is an API server, no crawling allowed",
        "# Main website: https://jones.com/",
    ]
    return HttpResponse("\n".join(content), content_type="text/plain")


urlpatterns = [
    path("robots.txt", robots_txt),   

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Admin Panel
    path('admin/', include('utils.admin_urls')),
    
    path('acp/', admin.site.urls),

    # auth API
    path('api/sample-auth/', common.sample_auth_view, name='sample_auth_api'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # API for profiles
    path('api/profiles/', include('profiles.api.urls'), name='profiles_api'),

    # API for shop
    path('api/products/', include('myshop.api.urls'), name='myshop_api'),
    path('api/shop/', include('pod_shop.api.urls'), name='pod_shop_api'),

    # API for articles
    path('api/articles/', include('articles.api.urls'), name='articles_api'),

    # API for utils
    path('api/utils/', include('utils.api.urls'), name='utils_api'),

    # Register myshop site URLs so the `myshop` namespace is available in templates
    path('shop/', include(("myshop.urls", "myshop"), namespace='myshop'),),

    # Fake view
    path('articles/', fake_view, name='article_listing'),
    path('articles/<slug:slug>/', fake_view, name='article_detail'),
    path('articles/category/<slug:slug>/', fake_view, name='article_category'),
    path('articles/tag/<slug:slug>/', fake_view, name='article_tag'),
    path('page/<slug:slug>/', fake_view, name='static_page'),

    # DJANGO
    path('api/django/auth/', include('allauth.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('', include('pod_shop.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve media files in production (when DEBUG=False)
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
