# Hetzner Deployment

Production stack for `api.fulfillnext.com` running on a Hetzner Cloud VPS.

> **Companion document**: [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) — the
> phase-by-phase migration playbook from GCP Cloud Run + Cloud SQL.
> Every command below is referenced from a phase there.

## Layout

```
deploy/hetzner/
├── MIGRATION_PLAN.md        # The plan (read this first)
├── README.md                # This file (operator handbook)
├── docker-compose.yml       # Stack: db, redis, api, nginx, certbot
├── Dockerfile.prod          # Production Django image (no seed_demo!)
├── entrypoint.prod.sh       # Production entrypoint (migrate + collectstatic only)
├── .env.example             # Template — copy to .env, fill all values
├── nginx/
│   ├── nginx.conf
│   ├── api.fulfillnext.com.conf       # HTTP-only, used during cert acquisition
│   └── api.fulfillnext.com.https.conf # Swapped in by ssl-init.sh
├── postgres/                          # (reserved for future init scripts)
├── media-bucket/                      # gitignored — product images live here
└── scripts/
    ├── bootstrap.sh         # Phase 1 — server hardening + Docker install
    ├── export-from-gcp.sh   # Phase 3/5 — pg dump from Cloud SQL
    ├── import-to-hetzner.sh # Phase 3/5 — pg restore into local Postgres
    ├── ssl-init.sh          # Phase 5 — Let's Encrypt cert + nginx switch
    └── weekly-backup.sh     # Phase 6 — off-site DB dump (cron)
```

## Quick start

Assumes Phase 0 + Phase 1 (bootstrap) are already done — server up, deploy
user with passwordless sudo, Docker installed.

```bash
# On Hetzner box, as deploy user:
cd /srv/fulfillnext-api
git clone https://github.com/huytam2022/Pezura.git .   # or `git pull`
cd deploy/hetzner

# 1. Configure env
cp .env.example .env
$EDITOR .env

# 2. Pre-populate media-bucket/ with existing product images
#    (one-off migration from old GCS bucket — see scripts/migrate-gcs-media.sh)
mkdir -p media-bucket

# 3. Bring up DB + Redis first
docker compose up -d db redis
sleep 10

# 4. Restore production data
#    (Run scripts/export-from-gcp.sh on your laptop first, scp result up)
bash scripts/import-to-hetzner.sh /srv/fulfillnext-api/dump-*.sql

# 5. Build + start the api
docker compose build api
docker compose up -d api nginx

# 6. Verify with Host header (DNS still pointing at GCP)
curl -H "Host: api.fulfillnext.com" http://localhost/api/shop/brands-list/

# 7. Cutover DNS (Phase 5), then SSL
bash scripts/ssl-init.sh
```

## Common operations

```bash
# Tail logs
docker compose logs -f api

# Restart api after pulling new code
git pull
docker compose build api && docker compose up -d api

# Postgres shell
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB

# Redis CLI
docker compose exec redis redis-cli

# One-off Django command
docker compose exec api python manage.py <cmd>

# Renew SSL (cron should do this automatically)
docker compose run --rm certbot "certbot renew" \
  && docker compose exec nginx nginx -s reload
```

## Recovery

If `docker compose up` fails to start, never run `seed_demo` — it will
overwrite Site (pk=1) and ProductImage records on real data. The
production entrypoint (`entrypoint.prod.sh`) deliberately omits it.

If the api container won't start because migrations fail, get a shell:

```bash
docker compose run --rm --entrypoint bash api
# then inspect with: python manage.py showmigrations
```

To roll back to GCP, see Phase 5 "Rollback procedure" in
MIGRATION_PLAN.md.
