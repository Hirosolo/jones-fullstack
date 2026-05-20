"""
Sync product reviews between .com (Django) and .shop (WooCommerce).

Mapping rule: 1 SP .com ↔ 1 SP .shop, khóa bằng slug giống hệt.
Dedup: Review.wp_review_id giữ id review WP, đảm bảo idempotent.

Hai entry-points:
- import_from_shop(dry_run=False) — pull reviews từ .shop về .com
- push_to_shop(review)            — push 1 review vừa tạo trên .com lên .shop

Auth: WooCommerce REST API consumer key/secret (HTTP Basic).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional
from urllib.parse import urlencode

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


# ─── Config ─────────────────────────────────────────────────────────────
def _get_settings():
    """Đọc env tại lúc gọi (không cache) để test/override dễ hơn."""
    base = (os.environ.get('WP_SHOP_BASE_URL') or '').rstrip('/')
    ck = os.environ.get('WP_SHOP_WC_CONSUMER_KEY') or ''
    cs = os.environ.get('WP_SHOP_WC_CONSUMER_SECRET') or ''
    return base, ck, cs


class WPSyncConfigError(RuntimeError):
    pass


class WPSyncAPIError(RuntimeError):
    pass


def _client():
    base, ck, cs = _get_settings()
    if not (base and ck and cs):
        raise WPSyncConfigError(
            'Missing WP_SHOP_BASE_URL / WP_SHOP_WC_CONSUMER_KEY / WP_SHOP_WC_CONSUMER_SECRET'
        )
    sess = requests.Session()
    sess.auth = HTTPBasicAuth(ck, cs)
    sess.headers.update({'Accept': 'application/json', 'User-Agent': 'jones-com-sync/1.0'})
    return sess, base


def _wc_get(path: str, params: Optional[dict] = None, timeout: int = 20) -> requests.Response:
    sess, base = _client()
    url = f'{base}/wp-json/wc/v3{path}'
    if params:
        url = f'{url}?{urlencode(params)}'
    return sess.get(url, timeout=timeout)


def _wc_post(path: str, json_body: dict, timeout: int = 20) -> requests.Response:
    sess, base = _client()
    url = f'{base}/wp-json/wc/v3{path}'
    return sess.post(url, json=json_body, timeout=timeout)


# ─── Product slug ↔ WC product_id cache ─────────────────────────────────
@dataclass
class _ProductMap:
    by_slug: dict       # str → int
    by_id: dict         # int → str

    def remember(self, slug: str, pid: int):
        if slug:
            self.by_slug[slug] = pid
        if pid:
            self.by_id[pid] = slug


def _build_product_map() -> _ProductMap:
    """Pre-fetch toàn bộ slug→id từ .shop. Gọi 1 lần trước khi import N reviews."""
    pmap = _ProductMap(by_slug={}, by_id={})
    page = 1
    per_page = 100
    while True:
        resp = _wc_get('/products', params={
            'per_page': per_page, 'page': page,
            'status': 'publish',
            '_fields': 'id,slug',
        })
        if resp.status_code != 200:
            raise WPSyncAPIError(f'GET /products page={page} → {resp.status_code} {resp.text[:200]}')
        items = resp.json() or []
        for it in items:
            pmap.remember(it.get('slug') or '', int(it.get('id') or 0))
        if len(items) < per_page:
            break
        page += 1
        if page > 100:  # safety, 10k SP max
            break
    return pmap


def _resolve_slug_for_product(pid: int, pmap: _ProductMap) -> Optional[str]:
    """Lookup slug, fallback gọi /products/<id> nếu cache miss."""
    if pid in pmap.by_id:
        return pmap.by_id[pid]
    resp = _wc_get(f'/products/{pid}', params={'_fields': 'id,slug'})
    if resp.status_code != 200:
        return None
    data = resp.json() or {}
    slug = data.get('slug') or ''
    if slug:
        pmap.remember(slug, pid)
    return slug or None


# ─── Importer: .shop → .com ──────────────────────────────────────────────
def import_from_shop(dry_run: bool = False, only_approved: bool = True) -> dict:
    """
    Pull reviews từ WC `/products/reviews` về Django.

    Returns: {fetched, created, updated, skipped_no_product, skipped_unapproved, errors}
    """
    from pod_shop.models import Product, Review  # late import để tránh circular

    stats = {
        'fetched': 0, 'created': 0, 'updated': 0,
        'skipped_no_product': 0, 'skipped_unapproved': 0, 'errors': 0,
    }

    pmap = _build_product_map()
    logger.info('product map built: %d slugs', len(pmap.by_slug))

    page = 1
    per_page = 100
    while True:
        params = {'per_page': per_page, 'page': page, 'status': 'approved' if only_approved else 'all'}
        resp = _wc_get('/products/reviews', params=params)
        if resp.status_code != 200:
            raise WPSyncAPIError(f'GET /products/reviews → {resp.status_code} {resp.text[:200]}')
        batch = resp.json() or []
        if not batch:
            break

        for wp in batch:
            stats['fetched'] += 1
            wp_id = int(wp.get('id') or 0)
            wp_status = (wp.get('status') or '').lower()
            if only_approved and wp_status != 'approved':
                stats['skipped_unapproved'] += 1
                continue

            wc_pid = int(wp.get('product_id') or 0)
            slug = _resolve_slug_for_product(wc_pid, pmap)
            if not slug:
                stats['skipped_no_product'] += 1
                logger.warning('wp review %s: no slug for wc_product_id=%s', wp_id, wc_pid)
                continue

            try:
                product = Product.objects.get(slug=slug)
            except Product.DoesNotExist:
                stats['skipped_no_product'] += 1
                logger.warning('wp review %s: .com Product slug=%r not found', wp_id, slug)
                continue

            payload = {
                'product': product,
                'rating': max(1, min(5, int(wp.get('rating') or 5))),
                'reviewer_name': (wp.get('reviewer') or '').strip()[:255],
                'content': _strip_html(wp.get('review') or ''),
                'content_safe': _strip_html(wp.get('review') or ''),
                'status': True,
            }
            wp_created_at = _parse_wp_date(wp.get('date_created_gmt') or wp.get('date_created') or '')

            if dry_run:
                logger.info('[dry-run] would upsert wp_review_id=%s slug=%s', wp_id, slug)
                continue

            existing = Review.objects.filter(wp_review_id=wp_id).first()
            if existing:
                changed = False
                for k, v in payload.items():
                    if getattr(existing, k) != v:
                        setattr(existing, k, v)
                        changed = True
                if changed:
                    existing.save()
                    stats['updated'] += 1
                target_pk = existing.pk
            else:
                row = Review.objects.create(wp_review_id=wp_id, **payload)
                stats['created'] += 1
                target_pk = row.pk

            # Override auto_now_add timestamps via raw .update() so created_at
            # mirrors the original WP review date instead of all 42 rows
            # collapsing onto the import time.
            if wp_created_at is not None:
                Review.objects.filter(pk=target_pk).update(
                    created_at=wp_created_at,
                    updated_at=wp_created_at,
                )

        if len(batch) < per_page:
            break
        page += 1
        if page > 200:  # 20k reviews max
            break

    return stats


def _strip_html(s: str) -> str:
    """Strip HTML tags lightly. WP review content thường là plain hoặc <p>."""
    import re
    return re.sub(r'<[^>]+>', '', s or '').strip()


def _parse_wp_date(s: str) -> Optional[datetime]:
    """WP REST trả ISO 8601 không TZ ('YYYY-MM-DDTHH:MM:SS').
    Dùng *_gmt và localize sang UTC để Django lưu đúng tz-aware."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


# ─── Forward push: .com → .shop ──────────────────────────────────────────
def push_to_shop(review, timeout: int = 10) -> Optional[int]:
    """
    Push 1 Review .com lên .shop. Update review.wp_review_id nếu thành công.
    Trả về wp_review_id (hoặc None nếu fail).

    Fail-soft: log lỗi, không raise (caller không nên phụ thuộc kết quả).
    """
    try:
        if review.wp_review_id:
            return review.wp_review_id  # đã sync rồi

        slug = (review.product.slug or '').strip()
        if not slug:
            logger.warning('push_to_shop: review #%s has no product slug', review.pk)
            return None

        # Lookup product_id trên .shop bằng slug (1-vs-1 strict)
        resp = _wc_get('/products', params={'slug': slug, '_fields': 'id,slug', 'per_page': 1})
        if resp.status_code != 200:
            logger.error('push_to_shop: lookup slug=%s failed: %s', slug, resp.status_code)
            return None
        items = resp.json() or []
        if not items:
            logger.warning('push_to_shop: slug=%s not found on .shop', slug)
            return None
        wc_pid = int(items[0].get('id') or 0)

        body = {
            'product_id': wc_pid,
            'review': review.content or review.subject or '',
            'reviewer': (review.reviewer_name
                         or (review.user.get_full_name() if review.user else '')
                         or 'Anonymous')[:255],
            'reviewer_email': _reviewer_email(review),
            'rating': max(1, min(5, int(review.rating or 5))),
            'status': 'approved' if review.status else 'hold',
        }
        post = _wc_post('/products/reviews', body, timeout=timeout)
        if post.status_code not in (200, 201):
            logger.error('push_to_shop: POST review failed %s: %s',
                         post.status_code, post.text[:300])
            return None
        wp_id = int((post.json() or {}).get('id') or 0)
        if wp_id:
            review.wp_review_id = wp_id
            # save() chạy lại Product.save() để recompute avg rating — không vấn đề
            review.save(update_fields=['wp_review_id'])
        return wp_id or None
    except WPSyncConfigError as e:
        logger.warning('push_to_shop skipped (config): %s', e)
        return None
    except Exception as e:  # noqa: BLE001 — fail-soft
        logger.exception('push_to_shop unexpected error: %s', e)
        return None


def _reviewer_email(review) -> str:
    """WC bắt buộc reviewer_email. Dùng email user nếu có, fallback dummy."""
    if review.user and getattr(review.user, 'email', ''):
        return review.user.email
    return f'anon-{review.pk or "new"}@jones.local'
