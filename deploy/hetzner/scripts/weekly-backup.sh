#!/usr/bin/env bash
# Phase 6 — Off-site DB backup (in addition to Hetzner snapshot).
# Schedule via cron:  0 4 * * 0 /srv/jones/deploy/hetzner/scripts/weekly-backup.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$COMPOSE_DIR"

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi
: "${POSTGRES_USER:?POSTGRES_USER not set}"
: "${POSTGRES_DB:?POSTGRES_DB not set}"

BACKUP_DIR="${BACKUP_DIR:-/srv/jones/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/db-${STAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "==> Dumping ${POSTGRES_DB} to ${OUT}…"
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --no-owner --no-acl | gzip -9 > "$OUT"

SIZE=$(du -h "$OUT" | cut -f1)
echo "==> Backup written: $OUT ($SIZE)"

echo "==> Pruning backups older than ${RETENTION_DAYS} days…"
find "$BACKUP_DIR" -name 'db-*.sql.gz' -mtime "+${RETENTION_DAYS}" -delete

echo "==> Current backups:"
ls -lh "$BACKUP_DIR"/db-*.sql.gz 2>/dev/null | tail -10

# Optional: upload to GCS for off-site copy.
# Uncomment + ensure gcloud is authenticated as a service account on the box.
# if command -v gsutil >/dev/null 2>&1; then
#   gsutil cp "$OUT" "gs://jones_cloudbuild/archive/$(basename "$OUT")"
# fi
