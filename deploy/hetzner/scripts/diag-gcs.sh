#!/usr/bin/env bash
# Diagnose GCS auth + bucket write access from inside the api container.
set -e
cd /srv/fulfillnext-api/deploy/hetzner

echo "=== Env in api container ==="
docker compose exec -T api env | grep -E 'GS_BUCKET|GOOGLE_APPLICATION'

echo
echo "=== Service account from key file ==="
docker compose exec -T api python -c "import json; d=json.load(open('/secrets/gcs-key.json')); print('email:', d['client_email']); print('project:', d.get('project_id'))"

echo
echo "=== List bucket (read access) ==="
docker compose exec -T api python <<'PYEOF'
import os
from google.cloud import storage
try:
    client = storage.Client()
    bucket = client.bucket(os.environ['GS_BUCKET_NAME'])
    print(f'bucket.exists(): {bucket.exists()}')
    blobs = list(client.list_blobs(bucket.name, max_results=3))
    print(f'sample blobs: {[b.name for b in blobs]}')
except Exception as e:
    print(f'READ FAIL: {type(e).__name__}: {e}')
PYEOF

echo
echo "=== Upload tiny test blob (write access) ==="
docker compose exec -T api python <<'PYEOF'
import os, time
from google.cloud import storage
try:
    client = storage.Client()
    bucket = client.bucket(os.environ['GS_BUCKET_NAME'])
    name = f'test-uploads/hetzner-{int(time.time())}.txt'
    blob = bucket.blob(name)
    blob.upload_from_string('test from hetzner container')
    print(f'WRITE OK: {name}')
    blob.delete()
    print('DELETE OK')
except Exception as e:
    print(f'WRITE FAIL: {type(e).__name__}: {e}')
PYEOF
