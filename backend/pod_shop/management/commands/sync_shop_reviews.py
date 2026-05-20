"""
One-shot importer: pull product reviews từ .shop (WooCommerce) về .com.

Usage:
    python manage.py sync_shop_reviews --dry-run
    python manage.py sync_shop_reviews
    python manage.py sync_shop_reviews --include-unapproved

Env c\u1ea7n (xem deploy/hetzner/.env.example):
    WP_SHOP_BASE_URL=https://jones.shop
    WP_SHOP_WC_CONSUMER_KEY=ck_xxx
    WP_SHOP_WC_CONSUMER_SECRET=cs_xxx
"""
from django.core.management.base import BaseCommand, CommandError

from pod_shop.services.wp_review_sync import (
    WPSyncAPIError,
    WPSyncConfigError,
    import_from_shop,
)


class Command(BaseCommand):
    help = 'Import product reviews từ .shop (WooCommerce) về .com (Django).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Không ghi DB, chỉ in ra số lượng sẽ create/update.',
        )
        parser.add_argument(
            '--include-unapproved', action='store_true',
            help='Import cả review chưa duyệt (status != approved). Mặc định bỏ qua.',
        )

    def handle(self, *args, **opts):
        dry = opts['dry_run']
        only_approved = not opts['include_unapproved']

        self.stdout.write(self.style.NOTICE(
            f'Import reviews from .shop (dry_run={dry}, only_approved={only_approved})'
        ))

        try:
            stats = import_from_shop(dry_run=dry, only_approved=only_approved)
        except WPSyncConfigError as e:
            raise CommandError(f'Config error: {e}')
        except WPSyncAPIError as e:
            raise CommandError(f'WP API error: {e}')

        self.stdout.write(self.style.SUCCESS('Done. Stats:'))
        for k, v in stats.items():
            self.stdout.write(f'  {k:>22}: {v}')
