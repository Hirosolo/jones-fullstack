#!/usr/bin/env bash
# Phase 3 / Phase 5 — Export Cloud SQL DB to a SQL dump file.
# Run on a machine that has `gcloud` authenticated to project fulfillnext.
set -euo pipefail

PROJECT="${PROJECT:-fulfillnext}"
INSTANCE="${INSTANCE:-fulfillnext-db}"
DB="${DB:-fulfillnext}"
BUCKET="${BUCKET:-fulfillnext_cloudbuild}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OBJECT="migration/dump-${STAMP}.sql"
GCS_PATH="gs://${BUCKET}/${OBJECT}"
LOCAL_FILE="${LOCAL_FILE:-./dump-${STAMP}.sql}"

echo "==> Granting Cloud SQL service account write access to bucket…"
SA_EMAIL="$(gcloud sql instances describe "$INSTANCE" --project="$PROJECT" --format='value(serviceAccountEmailAddress)')"
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin" \
  --project="$PROJECT" >/dev/null || true

echo "==> Exporting ${DB} from ${INSTANCE} → ${GCS_PATH}…"
gcloud sql export sql "$INSTANCE" "$GCS_PATH" \
  --database="$DB" --project="$PROJECT"

echo "==> Downloading dump to ${LOCAL_FILE}…"
gcloud storage cp "$GCS_PATH" "$LOCAL_FILE"

SIZE=$(du -h "$LOCAL_FILE" | cut -f1)
echo
echo "================================================================"
echo "  ✅ EXPORT COMPLETE"
echo "  File:  ${LOCAL_FILE} (${SIZE})"
echo "  GCS:   ${GCS_PATH}"
echo "================================================================"
echo "  Next: scp ${LOCAL_FILE} deploy@<HETZNER_IP>:/srv/fulfillnext-api/"
echo "        then bash scripts/import-to-hetzner.sh /srv/fulfillnext-api/$(basename "$LOCAL_FILE")"
echo "================================================================"
