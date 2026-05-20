"""
Reassign brand.league for known IPs that landed in the catch-all "Other"
bucket. The header mega-menu groups brands by league; when too many brands
fall back to "Other" the dropdown gets noisy.

Mapping rules follow project_categories_locked.md / product_taxonomy_workflow:
  - Movie / TV franchise -> "Movie"
  - Rock / metal band    -> "Rock Band"
  - Pop / hip-hop / R&B  -> "Music"
  - Anime / manga        -> "Culture"
  - Card / video game IP -> "Video Game"

Usage:
    python manage.py fix_brand_leagues            # dry-run
    python manage.py fix_brand_leagues --apply    # write changes
"""
from django.core.management.base import BaseCommand

from pod_shop.models import Brand


# name (case-insensitive match) -> target league
BRAND_LEAGUE_MAP = {
    # --- Music (pop / hip-hop / R&B / folk) ---
    'Charlie Puth': 'Music',
    'Chris Brown': 'Music',
    'DMX': 'Music',
    'Harry Styles': 'Music',
    'Justin Bieber': 'Music',
    'Noah Kahan': 'Music',
    'Pepe Aguilar': 'Music',
    'Snoop Dogg': 'Music',

    # --- Rock Band (rock / metal / metalcore) ---
    'Bad Omens': 'Rock Band',
    'Five Finger Death Punch': 'Rock Band',
    'Foo Fighters': 'Rock Band',
    'Phil Campbell': 'Rock Band',
    'Rockville': 'Rock Band',
    'Slash': 'Rock Band',

    # --- Movie / TV franchise / comics ---
    'DC': 'Movie',
    'Doctor Who': 'Movie',
    'Friday The 13th': 'Movie',
    'G.I. Joe': 'Movie',
    'Game of Thrones': 'Movie',
    'House of the Dragon': 'Movie',
    'La La Land': 'Movie',
    'Marvel': 'Movie',
    'Mission Impossible': 'Movie',
    'Pirates of the Caribbean': 'Movie',
    'Predator': 'Movie',
    'Taxi Driver': 'Movie',
    'The Texas Chainsaw Massacre': 'Movie',

    # --- Culture (anime / manga) ---
    'Gundam': 'Culture',
    'Jujutsu Kaisen': 'Culture',
    'My Hero Academia': 'Culture',

    # --- Video Game (TCG / video game IP) ---
    'Magic The Gathering': 'Video Game',
}


class Command(BaseCommand):
    help = 'Reassign Brand.league for known IPs currently in the "Other" bucket.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Persist changes. Without this flag the command is a dry-run.',
        )

    def handle(self, *args, **opts):
        apply_changes = opts['apply']
        updated, skipped, missing = [], [], []

        for name, target_league in BRAND_LEAGUE_MAP.items():
            brand = Brand.objects.filter(name__iexact=name).first()
            if brand is None:
                missing.append(name)
                continue
            current = (brand.league or '').strip()
            if current == target_league:
                skipped.append((brand.name, current))
                continue
            updated.append((brand.name, current or '(empty)', target_league))
            if apply_changes:
                brand.league = target_league
                brand.save(update_fields=['league'])

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nfix_brand_leagues — {'APPLY' if apply_changes else 'DRY RUN'}\n"
        ))
        if updated:
            self.stdout.write(self.style.SUCCESS(f'Updated ({len(updated)}):'))
            for name, old, new in updated:
                self.stdout.write(f'  {name}: {old!r} -> {new!r}')
        if skipped:
            self.stdout.write(self.style.WARNING(
                f'\nAlready correct ({len(skipped)}): {", ".join(n for n, _ in skipped)}'
            ))
        if missing:
            self.stdout.write(self.style.ERROR(
                f'\nNot found in DB ({len(missing)}): {", ".join(missing)}'
            ))
        if not apply_changes:
            self.stdout.write(self.style.NOTICE(
                '\nDry-run only. Re-run with --apply to persist.'
            ))
