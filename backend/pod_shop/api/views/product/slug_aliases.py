# path: pod_shop/api/views/product/slug_aliases.py
"""Public read-only endpoint returning the full slug-alias map.

Consumed by the Next.js middleware to 301-redirect /p/<old-slug>/ to the
product's current slug. Payload is intentionally a flat {old: new} dict
(no nesting, no metadata) to keep the bundle as small as possible —
middleware fetches this on every cold edge invocation.

Cached at 5 minutes:
  - Django-side via @cache_page so concurrent middleware fetches across
    Vercel regions don't hammer Postgres.
  - FE-side via `next: { revalidate: 300 }` in the middleware fetch.

Both caches must be reasonably short so a freshly-renamed product becomes
redirectable within a few minutes of the admin save.
"""
from django.views.decorators.cache import cache_page
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from pod_shop.models import ProductSlugAlias


@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 5)
def product_slug_aliases_view(request):
    """Return {old_slug: current_slug} for every alias in the system.

    Joins Product to read the *current* slug rather than storing it
    redundantly on the alias row — Product.slug is the source of truth and
    can drift if multiple renames chain.
    """
    rows = (
        ProductSlugAlias.objects
        .select_related('product')
        .values_list('old_slug', 'product__slug')
    )
    aliases = {old: current for old, current in rows if old and current and old != current}
    return Response({'aliases': aliases})
