"""
Replace jones.shop references in Product description fields
(desc / desc_short) with jones.com.

Three independent transforms (applied in order):

1. Literal logo home-link href: `href='https://jones.shop/'` ->
   `href='https://jones.com/'` (single & double quote variants).
2. Literal WordPress logo image URL:
   `https://jones.shop/wp-content/uploads/2026/04/cropped-Jones_logo-scaled-1.png`
   -> `https://www.jones.com/images/jones_logo.png`.
3. Plain-text mentions: any `jones.shop` NOT followed by `/` ->
   `jones.com`. Negative lookahead leaves URLs with paths
   (e.g. `/shipping-returns`, `/returns`) untouched on purpose because
   those paths don't exist on .com.

Usage:
    python manage.py fix_shop_links            # dry-run (lists changed products)
    python manage.py fix_shop_links --apply    # write changes to DB
"""
import re

from django.core.management.base import BaseCommand

from pod_shop.models import Product

_IMG_OLD = (
    'https://jones.shop/wp-content/uploads/2026/04/'
    'cropped-Jones_logo-scaled-1.png'
)
_IMG_NEW = 'https://www.fulfillnext.com/images/fulfillnext_logo.png'

_LITERAL_REPLACEMENTS = [
    ("href='https://fulfillnext.shop/'", "href='https://fulfillnext.com/'"),
    ('href="https://fulfillnext.shop/"', 'href="https://fulfillnext.com/"'),
    (_IMG_OLD, _IMG_NEW),
]

# Plain-text mentions (case-insensitive): fulfillnext.shop NOT followed by '/'.
# Capture group preserves original casing of "fulfillnext" / "FulfillNext" etc.
_TEXT_RE = re.compile(r'(fulfillnext)\.shop(?!/)', re.IGNORECASE)

_FIELDS = ['desc', 'desc_short']


def _transform(s: str) -> str:
    out = s
    for old, new in _LITERAL_REPLACEMENTS:
        out = out.replace(old, new)
    out = _TEXT_RE.sub(lambda m: m.group(1) + '.com', out)
    return out


class Command(BaseCommand):
    help = 'Replace fulfillnext.shop in Product desc/desc_short with fulfillnext.com'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            default=False,
            help='Write changes; without this flag the command is a dry-run',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        changed_products = 0

        for p in Product.objects.only('id', 'name', *_FIELDS).iterator():
            old_desc = p.desc or ''
            old_short = p.desc_short or ''
            new_desc = _transform(old_desc)
            new_short = _transform(old_short)

            if new_desc == old_desc and new_short == old_short:
                continue

            tags = []
            if new_desc != old_desc:
                tags.append('desc')
            if new_short != old_short:
                tags.append('desc_short')
            self.stdout.write(
                f'  Product #{p.id} "{p.name}" [{",".join(tags)}]'
            )

            if apply:
                if new_desc != old_desc:
                    p.desc = new_desc
                if new_short != old_short:
                    p.desc_short = new_short
                p.save(update_fields=_FIELDS)
            changed_products += 1

        mode = 'Applied' if apply else 'Dry-run'
        self.stdout.write(
            self.style.SUCCESS(f'\n{mode}: {changed_products} product(s) affected')
        )
        if not apply and changed_products:
            self.stdout.write('  Run with --apply to commit changes.')
