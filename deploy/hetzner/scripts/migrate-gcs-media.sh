#!/usr/bin/env bash
# One-off migration: copy contents of gs://fulfillnext-media into the
# Hetzner host's media-bucket/ directory so Django + nginx can serve
# product images locally with no GCP dependency.
#
# Run this once on a workstation that has `gcloud` authenticated to the
# fulfillnext project. It downloads to /tmp, then scps to the Hetzner
# host. After it succeeds, the GCP project / bucket can be deleted.
#
# Usage:
#   bash deploy/hetzner/scripts/migrate-gcs-media.sh deploy@5.78.185.209
set -euo pipefail

HETZNER_TARGET="${1:-deploy@5.78.185.209}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/hetzner_fulfillnext}"
PROJECT="${PROJECT:-fulfillnext}"
BUCKET="${BUCKET:-fulfillnext-media}"
LOCAL_DIR="${LOCAL_DIR:-/tmp/gcs-media-backup}"
REMOTE_DIR="${REMOTE_DIR:-/srv/fulfillnext-api/deploy/hetzner/media-bucket}"

echo "==> Downloading gs://${BUCKET}/* to ${LOCAL_DIR}/ …"
mkdir -p "$LOCAL_DIR"
gcloud storage cp -r "gs://${BUCKET}/*" "${LOCAL_DIR}/" --project="$PROJECT"

echo
echo "==> Files downloaded:"
find "$LOCAL_DIR" -type f | wc -l
du -sh "$LOCAL_DIR"

echo
echo "==> Creating tarball …"
TARBALL="/tmp/media-bucket-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -C "$LOCAL_DIR" -czf "$TARBALL" .

echo
echo "==> Uploading to ${HETZNER_TARGET}:${REMOTE_DIR}/ …"
ssh -i "$SSH_KEY" "$HETZNER_TARGET" "mkdir -p ${REMOTE_DIR}"
scp -i "$SSH_KEY" "$TARBALL" "${HETZNER_TARGET}:/tmp/media-bucket.tar.gz"

echo
echo "==> Extracting on Hetzner …"
ssh -i "$SSH_KEY" "$HETZNER_TARGET" "tar -C ${REMOTE_DIR} -xzf /tmp/media-bucket.tar.gz && rm /tmp/media-bucket.tar.gz && echo Files in remote: && find ${REMOTE_DIR} -type f | wc -l && du -sh ${REMOTE_DIR}"

echo
echo "================================================================"
echo "  ✅ MIGRATION COMPLETE"
echo "  Local copy: ${LOCAL_DIR}/"
echo "  Tarball:    ${TARBALL}"
echo "  Hetzner:    ${HETZNER_TARGET}:${REMOTE_DIR}/"
echo
echo "  Next steps:"
echo "  1. Recreate api + nginx containers so the new bind mount takes effect:"
echo "     ssh ${HETZNER_TARGET} 'cd /srv/fulfillnext-api/deploy/hetzner && \\"
echo "        docker compose down api nginx && docker compose up -d api nginx'"
echo "  2. Verify a product image:"
echo "     curl -I https://api.fulfillnext.com/media/<some-file>.jpg"
echo "  3. Push the FE rewrite changes (next.config.ts) so Vercel routes"
echo "     /images/* to Hetzner instead of GCS."
echo "  4. After ≥24h with no issues, delete gs://${BUCKET} and"
echo "     decommission the GCP project."
echo "================================================================"
