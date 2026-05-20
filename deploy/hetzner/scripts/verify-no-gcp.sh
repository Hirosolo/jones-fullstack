#!/usr/bin/env bash
# Run on the Hetzner host. Prints evidence that no GCP dependency remains
# so the operator can safely delete the GCP project.
set -e
cd "$(dirname "$0")/.."

echo '=== 1. BE outbound to GCP in last 30m ==='
LOGS=$( (docker compose logs api --since 30m 2>&1; docker compose logs nginx --since 30m 2>&1) | grep -iE 'storage.googleapis|googleapis\.com|google\.cloud|gs://' || true )
if [ -z "$LOGS" ]; then
  echo "(no GCP outbound)"
else
  echo "$LOGS"
fi

echo
echo '=== 2. Container env: any GS_ or GOOGLE_ vars? ==='
ENV_HITS=$(docker compose exec -T api env | grep -iE 'GS_|GOOGLE_' || true)
if [ -z "$ENV_HITS" ]; then
  echo "(none — clean)"
else
  echo "$ENV_HITS"
fi

echo
echo '=== 3. Django storage backend ==='
docker compose exec -T api python <<'PY'
import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jones.settings")
django.setup()
from django.conf import settings
print("BACKEND:    ", settings.STORAGES["default"]["BACKEND"])
print("MEDIA_URL:  ", settings.MEDIA_URL)
print("MEDIA_ROOT: ", settings.MEDIA_ROOT)
PY

echo
echo '=== 4. /secrets dir mounted? (should NOT exist) ==='
docker compose exec -T api ls /secrets 2>&1 | head -3 || true

echo
echo '=== 5. media-bucket file count ==='
docker compose exec -T api find /app/media -type f | wc -l

echo
echo '=== 6. requirements.txt has google-cloud-storage? ==='
docker compose exec -T api pip show google-cloud-storage 2>&1 | grep -E '^(Name|Version):' || echo '(not installed)'
echo '(Note: package may still be installed but unused — safe to leave)'

echo
echo '================================================================'
echo '  Migration verification done.'
echo '  If sections 1, 2, 4 above show "(none)" / "(no GCP outbound)"'
echo '  and section 3 shows FileSystemStorage + /media/ + /app/media,'
echo '  then the GCP project can be deleted safely.'
echo '================================================================'
