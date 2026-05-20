"""
Management command to regenerate Product slugs from their name field.

Use when the AutoSlugField max_length was raised and existing rows still
hold the old truncated slug. Setting slug to an empty string triggers
django-autoslug to re-populate from `name` on save, producing the full
humanised slug and appending -1/-2 suffixes on the rare collision.

Usage:
    python manage.py regenerate_slugs
    python manage.py regenerate_slugs --dry-run
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from pod_shop.models import Product


class Command(BaseCommand):
    help = 'Regenerate slugs for all Product rows from their name field.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List what would change without saving.',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        changed = 0
        unchanged = 0
        total = Product.objects.count()

        self.stdout.write(f'Scanning {total} products...')

        with transaction.atomic():
            for product in Product.objects.all().order_by('id'):
                old_slug = product.slug
                product.slug = ''  # Triggers AutoSlugField repopulation on save.
                if dry:
                    self.stdout.write(f'  [{product.pk:>4}] {old_slug} -> (would regen from name)')
                    continue
                product.save()
                new_slug = product.slug
                if old_slug == new_slug:
                    unchanged += 1
                    continue
                changed += 1
                self.stdout.write(f'  [{product.pk:>4}] {old_slug}  ->  {new_slug}')

            if dry:
                transaction.set_rollback(True)

        summary = f'changed={changed} unchanged={unchanged} total={total}'
        if dry:
            self.stdout.write(self.style.WARNING(f'DRY RUN: {summary} (no writes)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Done: {summary}'))
