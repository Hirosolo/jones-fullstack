#!/usr/bin/env bash
# Production entrypoint for Hetzner.
# DELIBERATELY does NOT call `seed_demo` — that command overwrites
# Site (pk=1) and ProductImage records on every container start (see
# backend/pod_shop/management/commands/seed_demo.py). The production DB
# is restored from a real Cloud SQL dump in Phase 3, so seeding would
# corrupt real data.
set -e

mkdir -p /app/logs /app/static /app/media

echo "[entrypoint] Waiting for database…"
python -c "
import django, os, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jones.settings')
django.setup()
from django.db import connection
for i in range(30):
    try:
        connection.ensure_connection()
        print('[entrypoint] DB ready.')
        break
    except Exception as e:
        print(f'[entrypoint] DB not ready ({e}); retrying ({i+1}/30)…')
        time.sleep(2)
else:
    raise SystemExit('[entrypoint] DB connection failed after 60s')
"

echo "[entrypoint] Running migrations…"
python manage.py migrate --noinput

echo "[entrypoint] Collecting static files…"
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Starting: $*"
exec "$@"
