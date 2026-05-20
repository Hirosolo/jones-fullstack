"""
Management command to rename demo product images to SEO-friendly names.

Replaces generic filenames like `demo_product_5.jpg` with descriptive
slugified names like `godzilla-atomic-bomb-custom-watch-abc12.jpg`.

Usage:
    python manage.py rename_seo_images          # dry-run (preview only)
    python manage.py rename_seo_images --apply   # actually rename files
"""

import os
import shutil

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from unidecode import unidecode

from pod_shop.models import ProductImage


class Command(BaseCommand):
    help = 'Rename product images to SEO-friendly filenames based on product name'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            default=False,
            help='Actually rename the files (default is dry-run)',
        )

    def handle(self, *args, **options):
        from django.conf import settings

        apply = options['apply']
        media_root = settings.MEDIA_ROOT

        images = ProductImage.objects.filter(removed=False).exclude(image='').select_related('product')
        renamed_count = 0
        skipped_count = 0

        for img in images:
            old_path = str(img.image)
            old_basename = os.path.basename(old_path)

            # Skip if already has SEO-friendly name (contains product slug)
            product_slug = slugify(unidecode(img.product.name)) if img.product else ''
            if product_slug and product_slug[:20] in old_basename:
                skipped_count += 1
                continue

            # Skip if not a generic demo name
            if not old_basename.startswith('demo_'):
                skipped_count += 1
                continue

            # Build new SEO-friendly filename
            extension = os.path.splitext(old_basename)[1].lower() or '.jpg'
            # Keep the directory structure, just rename the file
            old_dir = os.path.dirname(old_path)
            # Use first 50 chars of slug to keep filename reasonable
            slug_part = product_slug[:50] if product_slug else 'product'
            # Add a short unique suffix from old filename to avoid collisions
            import hashlib
            short_hash = hashlib.md5(old_path.encode()).hexdigest()[:6]
            new_basename = f'{slug_part}-{short_hash}{extension}'
            new_path = os.path.join(old_dir, new_basename)

            old_abs = os.path.join(media_root, old_path)
            new_abs = os.path.join(media_root, new_path)

            if apply:
                if os.path.exists(old_abs):
                    # Copy (don't move) so thumbnails and any references still work
                    os.makedirs(os.path.dirname(new_abs), exist_ok=True)
                    shutil.copy2(old_abs, new_abs)
                    # Update DB
                    img.image = new_path
                    img.save(update_fields=['image'])
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {old_path} → {new_path}'))
                    renamed_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'  ✗ File not found: {old_abs}'))
            else:
                self.stdout.write(f'  [DRY-RUN] {old_path} → {new_path}')
                renamed_count += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'[{mode}] {renamed_count} images renamed, {skipped_count} skipped'
        ))
        if not apply and renamed_count > 0:
            self.stdout.write(self.style.WARNING(
                'Run with --apply to actually rename the files.'
            ))
