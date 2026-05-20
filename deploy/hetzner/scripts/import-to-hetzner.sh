#!/usr/bin/env bash
# Phase 3 / Phase 5 — Restore a Cloud SQL dump into the Hetzner Postgres.
# Run on the Hetzner box, in /srv/fulfillnext-api/deploy/hetzner.
set -euo pipefail

DUMP_FILE="${1:-}"
if [ -z "$DUMP_FILE" ] || [ ! -f "$DUMP_FILE" ]; then
  echo "Usage: $0 <path-to-dump.sql>" >&2
  exit 1
fi

# Discover compose file directory (script lives in scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$COMPOSE_DIR"

# Load .env so we have POSTGRES_USER / POSTGRES_DB
if [ -f .env ]; then
  set -a; . ./.env; set +a
fi
: "${POSTGRES_USER:?POSTGRES_USER not set in .env}"
: "${POSTGRES_DB:?POSTGRES_DB not set in .env}"

echo "==> Stopping api container…"
docker compose stop api || true

echo "==> Recreating database '${POSTGRES_DB}'…"
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres <<SQL
DROP DATABASE IF EXISTS ${POSTGRES_DB};
CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};
SQL

echo "==> Restoring dump (this may take a few minutes)…"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DUMP_FILE"

echo "==> Verifying counts…"
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'SQL'
SELECT 'products (active)' AS metric, COUNT(*) AS n FROM pod_shop_product WHERE status='A'
UNION ALL SELECT 'products (all)',     COUNT(*)      FROM pod_shop_product
UNION ALL SELECT 'brands',             COUNT(*)      FROM pod_shop_brand
UNION ALL SELECT 'categories',         COUNT(*)      FROM pod_shop_category
UNION ALL SELECT 'tags',               COUNT(*)      FROM pod_shop_tag
UNION ALL SELECT 'product_images',     COUNT(*)      FROM pod_shop_productimage
UNION ALL SELECT 'articles',           COUNT(*)      FROM articles_article
UNION ALL SELECT 'users',              COUNT(*)      FROM auth_user;

SELECT id, domain, name FROM django_site WHERE id=1;
SQL

echo
echo "================================================================"
echo "  ✅ RESTORE COMPLETE"
echo "  Compare counts above with production:"
echo "    products(active) → expect 40"
echo "    brands           → expect 38"
echo "    categories       → expect 5"
echo "    Site domain      → MUST be 'www.fulfillnext.com' or similar,"
echo "                       NOT 'localhost:8000' (would mean seed_demo ran)"
echo "================================================================"
echo "  Next: docker compose up -d api"
echo "================================================================"
