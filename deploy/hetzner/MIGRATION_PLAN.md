# Migration Plan: GCP Cloud Run → Hetzner Cloud

> **Status**: Draft, awaiting user execution.
> **Last updated**: 2026-04-25
> **Owner**: hai.pham@genesisda.com

---

## Context (read this first — applies to all phases)

### What we are doing
Move the Django backend (`jones-api`) and PostgreSQL database from Google Cloud
Platform (Cloud Run + Cloud SQL, asia-southeast1) to a single Hetzner Cloud VPS
running Docker Compose (Frankfurt or Falkenstein). Frontend stays on Vercel.

### Why
- GCP Cloud SQL minimum-viable tier is overpriced (~700–900k VND/mo) for a
  catalog of ~40 products with low traffic.
- Audience is USA-based (`jones.com`, English content, target Los Angeles).
  Hetzner Frankfurt → US east-coast is ~100ms vs GCP Singapore → US ~200ms.
- Hetzner CCX23 (4 vCPU dedicated, 16 GB RAM, 160 GB SSD, 20 TB egress) costs
  €31/mo (~800k VND) — same budget but **4× CPU, 4× RAM, 16× storage**.

### Current GCP state (do not change anything until Phase 5)
- **Project**: `jones`, region `asia-southeast1`
- **Cloud Run service**: `jones-api`, current revision `jones-api-00036-vtt`
- **Cloud Run image**: `asia-southeast1-docker.pkg.dev/jones/jones/jones-api:latest`
- **Cloud SQL instance**: `jones-db` (PostgreSQL 16, ENTERPRISE edition,
  `db-custom-1-3840`)
- **Cloud SQL connection string in Cloud Run env**:
  `postgres://jones:Jones2026!@/jones?host=/cloudsql/jones:asia-southeast1:jones-db`
- **Domain mapping**: `api.jones.com` → `jones-api` via Cloud Run
  domain mapping (CNAME to `ghs.googlehosted.com.`)
- **Media bucket**: `gs://jones-media` (~35 MB, public-read)
- **GCP env vars** Cloud Run uses (full list to replicate on Hetzner):
  `DATABASE_URL`, `DEBUG=False`, `ALLOWED_HOSTS=*`,
  `SITE_URL=https://jones.com`, `DJANGO_BASE_URL=https://api.jones.com`,
  `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `ADMIN_API_KEY`,
  `GS_BUCKET_NAME=jones-media`, `GS_DEFAULT_ACL=publicRead`.

### Counts to verify against after migration (DB integrity gate)
- Products (`pod_shop_product` where `status='A'`): **40**
- Brands (`pod_shop_brand`): **38**
- Categories (`pod_shop_category`): **5**
- (Verify exact totals from a fresh `SELECT COUNT(*)` immediately before cutover.)

### Critical risks (every phase must respect these)
1. **`backend/pod_shop/management/commands/seed_demo.py` overwrites Site
   domain (pk=1) AND ProductImage records for products 1–5 on every container
   start.** The Hetzner production entrypoint MUST NOT call `seed_demo`. The
   shipped `deploy/entrypoint.sh` calls it — Phase 2 ships a new
   `entrypoint.prod.sh` that omits it.
2. **`migrate --noinput` runs at startup.** If a migration changes column
   types in a destructive way, it could drop data. Before Phase 5 final
   cutover, run `python manage.py showmigrations` against the freshly
   restored DB and confirm no unexpected pending migrations.
3. **Image URLs in DB**: `pod_shop_productimage.image` stores paths like
   `products/<file>.jpg`. With Django storage backend `GS_BUCKET_NAME=...`,
   they resolve to `https://storage.googleapis.com/fulfillnext-media/...`.
   On Hetzner: either keep `GS_BUCKET_NAME` env var (continue serving from
   GCS — simplest) or migrate the bucket to local volume / Cloudflare R2
   and update settings. Default plan: **keep GCS bucket as-is** (35 MB,
   negligible cost, no rewrite needed).
4. **Production database password is currently in `env_vars.txt` at repo
   root.** Rotate it during Phase 3 (give the Hetzner Postgres a new
   password).

### Decisions locked in (change only if explicitly re-discussed)
- **Hetzner location**: Frankfurt (eu-central-1).
- **Hetzner plan**: CCX23 (4 dedicated vCPU, 16 GB RAM, 160 GB NVMe SSD,
  €31.90/mo).
- **OS**: Ubuntu 24.04 LTS.
- **Stack**: Docker Compose (`db: postgres:16`, `redis: redis:7-alpine`,
  `api: custom Django image`, `nginx: nginx:alpine`,
  `certbot: certbot/certbot`).
- **SSL**: Let's Encrypt via certbot, webroot challenge.
- **Media files**: keep on GCS for now (no migration). Re-evaluate after
  catalog grows.
- **CDN**: Cloudflare in front of Hetzner (free plan), DNS proxied.
- **Backup**: Hetzner daily snapshot (€2/mo) + weekly `pg_dump` to GCS bucket
  for off-site copy.

### Decisions still open (user must answer before Phase 0 finishes)
- [ ] DNS provider for `api.jones.com` (Cloudflare? Vercel? Google
      Domains? Other?) — needed for Phase 5 cutover.
- [ ] Email for Let's Encrypt (defaults to `hai.pham@genesisda.com`).
- [ ] Hetzner SSH public key (user provides; generate fresh ed25519 if none).

### Roles
- **U (User)**: tasks the user must do interactively (orders, console
  clicks, providing secrets).
- **A (Agent)**: tasks a subagent can fully script and execute.
- **U+A**: collaborative — agent prepares, user runs/verifies.

---

## Phase 0 — Decisions & account prep

**Goal**: lock in remaining decisions, provision the Hetzner server, hand IPs/keys to the next phase.

**Duration**: 1–2 hours.
**Downtime**: 0.
**Prereq**: none.

### Steps

1. **U** — Open a Hetzner Cloud account at <https://hetzner.com/cloud>, verify
   credit card / IBAN. Account verification can take 30–60 min on first sign-up.

2. **U** — In Hetzner Cloud Console:
   - Project → create project `jones`.
   - Security → SSH Keys → upload public key (or generate `ssh-keygen -t ed25519 -f ~/.ssh/hetzner_jones`).
   - Servers → Add Server:
     - Location: **Frankfurt**
     - Image: **Ubuntu 24.04**
     - Type: **CCX23** (Dedicated vCPU)
     - Networking: **enable IPv4 + IPv6**
     - SSH key: select uploaded key
     - Backups: **enable** (€2/mo, daily snapshots, 7 days retention)
     - Name: `jones-api-prod`
   - Wait ~30s for provisioning.

3. **U** — Cloudflare account at <https://cloudflare.com> if not yet existing.

4. **U** — Verify SSH access works:
   ```bash
   ssh -i ~/.ssh/hetzner_fulfillnext root@<HETZNER_IPV4>
   exit
   ```

5. **U** — Hand off to Phase 1 with these values written down:
   - Hetzner IPv4 address: `xxx.xxx.xxx.xxx`
   - Hetzner IPv6 address: `xxxx:xxxx::xxxx`
   - Path to SSH private key
   - Current DNS provider for `api.fulfillnext.com`
   - Let's Encrypt email
   - Cloudflare account email (if using Cloudflare for DNS)

### Phase 0 done when
- [ ] Hetzner server is reachable via SSH from user's machine.
- [ ] All "Decisions still open" items above are filled in.

---

## Phase 1 — Server bootstrap & hardening

**Goal**: harden the bare Ubuntu install, install Docker, create app user.

**Duration**: 30 min.
**Downtime**: 0.
**Prereq**: Phase 0 complete (server reachable).

### What to script (A)

Create `deploy/hetzner/scripts/bootstrap.sh` that, when run as root on the
Hetzner box, performs:

1. `apt-get update && apt-get -y dist-upgrade`
2. Install: `curl ca-certificates gnupg lsb-release ufw fail2ban htop git
   unattended-upgrades`
3. Enable `unattended-upgrades` for security patches.
4. Create user `deploy`, add to `sudo` group, copy root's `authorized_keys`.
5. SSH config (`/etc/ssh/sshd_config.d/99-hardening.conf`):
   - `PermitRootLogin no`
   - `PasswordAuthentication no`
   - `KbdInteractiveAuthentication no`
   - Reload sshd.
6. UFW:
   - default deny incoming, allow outgoing
   - allow 22/tcp (ssh), 80/tcp (http), 443/tcp (https)
   - `ufw --force enable`
7. fail2ban with default ssh jail.
8. Install Docker CE (official repo) + docker-compose-plugin v2.
9. Add `deploy` to `docker` group.
10. `mkdir -p /srv/fulfillnext-api && chown deploy:deploy /srv/fulfillnext-api`
11. Print: "Bootstrap complete. Re-login as deploy@<IP>."

### Steps

1. **A** — write the script and commit at `deploy/hetzner/scripts/bootstrap.sh`.

2. **U** — copy script to server and run:
   ```bash
   scp -i ~/.ssh/hetzner_fulfillnext deploy/hetzner/scripts/bootstrap.sh root@<IP>:/tmp/
   ssh -i ~/.ssh/hetzner_fulfillnext root@<IP> 'bash /tmp/bootstrap.sh'
   ```

3. **U** — verify, exit root, log back in as `deploy`:
   ```bash
   ssh -i ~/.ssh/hetzner_fulfillnext deploy@<IP>
   docker --version          # → Docker version 27.x
   docker compose version    # → Docker Compose version v2.x
   ufw status                # → 22/tcp, 80/tcp, 443/tcp ALLOW
   ```

### Phase 1 done when
- [ ] Root login disabled, only `deploy` user with key auth works.
- [ ] `docker` and `docker compose` commands work as `deploy` user without sudo.
- [ ] UFW shows correct rules; fail2ban is active.
- [ ] `/srv/fulfillnext-api` exists and is owned by `deploy`.

---

## Phase 2 — App stack files & local build

**Goal**: produce all Hetzner config files in the repo, build the production
Docker image locally to validate it.

**Duration**: 1–2 hours (mostly authoring; build is ~3 min).
**Downtime**: 0.
**Prereq**: Phase 1 done; the agent has access to the repo at
`e:\Repo_LEE_DUNG_GROUPS\codencl`.

### What to author (A)

Create the following files under `deploy/hetzner/`:

```
deploy/hetzner/
├── MIGRATION_PLAN.md          # this file (already created)
├── docker-compose.yml
├── Dockerfile.prod            # adapted from deploy/Dockerfile, NO seed_demo
├── entrypoint.prod.sh         # migrate + collectstatic ONLY (no seed_demo)
├── .env.example
├── nginx/
│   ├── nginx.conf             # main http config, gzip, security headers
│   └── api.fulfillnext.com.conf  # server block + SSL + proxy_pass
├── postgres/
│   └── init.sql               # CREATE USER django + database (idempotent)
└── scripts/
    ├── bootstrap.sh           # Phase 1
    ├── export-from-gcp.sh     # Phase 3
    ├── import-to-hetzner.sh   # Phase 3
    ├── ssl-init.sh            # Phase 4
    └── final-cutover.sh       # Phase 5
```

### Key requirements per file

**`Dockerfile.prod`**: same base (`python:3.10-slim`) and deps as `deploy/Dockerfile`, but copy `entrypoint.prod.sh` instead of `entrypoint.sh` so seed_demo never runs.

**`entrypoint.prod.sh`**:
```bash
#!/usr/bin/env bash
set -e
mkdir -p /app/logs /app/static /app/media
python -c "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','pezura.settings'); django.setup(); from django.db import connection; connection.ensure_connection()" || echo "[entrypoint] DB warmup failed"
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
```
Note: NO `seed_demo`, NO `regenerate_slugs`.

**`docker-compose.yml`** (skeleton — agent fills in env, healthchecks, networks):
```yaml
services:
  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redisdata:/data

  api:
    build:
      context: ../..
      dockerfile: deploy/hetzner/Dockerfile.prod
    restart: always
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
    environment:
      DATABASE_URL: postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      DEBUG: "False"
      ALLOWED_HOSTS: api.fulfillnext.com,localhost
      SITE_URL: ${SITE_URL}
      DJANGO_BASE_URL: https://api.fulfillnext.com
      CSRF_TRUSTED_ORIGINS: ${CSRF_TRUSTED_ORIGINS}
      CORS_ALLOWED_ORIGINS: ${CORS_ALLOWED_ORIGINS}
      ADMIN_API_KEY: ${ADMIN_API_KEY}
      GS_BUCKET_NAME: ${GS_BUCKET_NAME}
      GS_DEFAULT_ACL: publicRead
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
    volumes:
      - media:/app/media
      - static:/app/static

  nginx:
    image: nginx:alpine
    restart: always
    ports: ["80:80", "443:443"]
    depends_on: [api]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/api.fulfillnext.com.conf:/etc/nginx/conf.d/default.conf:ro
      - certbot-etc:/etc/letsencrypt:ro
      - certbot-www:/var/www/certbot:ro
      - static:/var/www/static:ro
      - media:/var/www/media:ro

  certbot:
    image: certbot/certbot
    volumes:
      - certbot-etc:/etc/letsencrypt
      - certbot-www:/var/www/certbot

volumes:
  pgdata:
  redisdata:
  media:
  static:
  certbot-etc:
  certbot-www:
```

**`.env.example`** (full list of vars; user copies to `.env` and fills):
```
POSTGRES_DB=fulfillnext
POSTGRES_USER=django
POSTGRES_PASSWORD=<generate-strong>
DJANGO_SECRET_KEY=<generate-50-chars>
ADMIN_API_KEY=<copy-from-current-cloud-run-env>
SITE_URL=https://www.fulfillnext.com
CSRF_TRUSTED_ORIGINS=https://fulfillnext.com,https://www.fulfillnext.com,https://api.fulfillnext.com
CORS_ALLOWED_ORIGINS=https://fulfillnext.com,https://www.fulfillnext.com
GS_BUCKET_NAME=fulfillnext-media
LETSENCRYPT_EMAIL=hai.pham@genesisda.com
```

**`nginx/api.fulfillnext.com.conf`**: 80 → 301 to 443, 443 with Let's Encrypt
cert, `proxy_pass http://api:8000;`, set `X-Forwarded-*` headers, serve
`/static/` and `/media/` from volumes.

### Steps

1. **A** — author all files, commit with message
   `feat(deploy): add Hetzner Cloud production stack`.
2. **A** — locally validate by running `docker compose -f deploy/hetzner/docker-compose.yml config`
   (must parse without errors).
3. **A** — locally build the image to catch syntax errors:
   `docker build -f deploy/hetzner/Dockerfile.prod -t test-api .`
4. **A** — push to git so the Hetzner box can pull.

### Phase 2 done when
- [ ] All files exist in `deploy/hetzner/`.
- [ ] `docker compose config` validates.
- [ ] `docker build` succeeds locally.
- [ ] Commit pushed to `master`.

---

## Phase 3 — Database migration (initial dry run)

**Goal**: pg_dump from Cloud SQL → restore into Hetzner Postgres → verify
counts. This is a **dry run** — final dump happens in Phase 5 to capture
last-minute writes.

**Duration**: 1–2 hours.
**Downtime**: 0 (production keeps serving from GCP).
**Prereq**: Phases 1 + 2 done; Hetzner has Docker Compose stack ready (but
api container does not need to be running yet).

### Steps

1. **A** — write `deploy/hetzner/scripts/export-from-gcp.sh`:
   ```bash
   #!/usr/bin/env bash
   set -e
   PROJECT=fulfillnext
   INSTANCE=fulfillnext-db
   DB=fulfillnext
   BUCKET=fulfillnext_cloudbuild
   STAMP=$(date +%Y%m%d-%H%M%S)
   GCS_PATH="gs://${BUCKET}/migration/dump-${STAMP}.sql"

   echo "Exporting ${DB} from ${INSTANCE} to ${GCS_PATH}…"
   gcloud sql export sql ${INSTANCE} ${GCS_PATH} \
     --database=${DB} --project=${PROJECT}

   echo "Downloading dump locally…"
   gsutil cp ${GCS_PATH} ./dump-${STAMP}.sql
   echo "Dump saved: ./dump-${STAMP}.sql ($(du -h dump-${STAMP}.sql | cut -f1))"
   ```

2. **A** — write `deploy/hetzner/scripts/import-to-hetzner.sh`:
   ```bash
   #!/usr/bin/env bash
   set -e
   DUMP_FILE=$1
   if [ -z "$DUMP_FILE" ]; then echo "Usage: $0 <dump.sql>"; exit 1; fi

   cd /srv/fulfillnext-api/deploy/hetzner

   echo "Stopping api container if running…"
   docker compose stop api || true

   echo "Recreating database…"
   docker compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS fulfillnext;"
   docker compose exec -T db psql -U postgres -c "CREATE DATABASE fulfillnext OWNER django;"

   echo "Restoring dump…"
   docker compose exec -T db psql -U django fulfillnext < "$DUMP_FILE"

   echo "Verifying counts…"
   docker compose exec -T db psql -U django fulfillnext -c "
     SELECT 'products' AS t, COUNT(*) FROM pod_shop_product WHERE status='A'
     UNION ALL SELECT 'brands', COUNT(*) FROM pod_shop_brand
     UNION ALL SELECT 'categories', COUNT(*) FROM pod_shop_category;
   "
   ```

3. **U** — locally (laptop with `gcloud` auth):
   ```bash
   bash deploy/hetzner/scripts/export-from-gcp.sh
   # produces dump-YYYYMMDD-HHMMSS.sql
   scp dump-*.sql deploy@<HETZNER_IP>:/srv/fulfillnext-api/
   ```

4. **U** — on Hetzner:
   ```bash
   cd /srv/fulfillnext-api
   git clone https://github.com/huytam2022/Pezura.git .   # or pull if exists
   cd deploy/hetzner
   cp .env.example .env
   $EDITOR .env                                            # fill all values
   docker compose up -d db redis                          # start DB only
   sleep 10
   bash scripts/import-to-hetzner.sh /srv/fulfillnext-api/dump-*.sql
   ```

5. **U** — verify counts match production:
   - Run on Hetzner: the SELECT in step 2 above. Expected:
     `products=40, brands=38, categories=5` (re-fetch live counts before
     comparing, in case admin added new items meanwhile).
   - Run on GCP for comparison:
     ```bash
     curl -A "Mozilla/5.0" "https://api.fulfillnext.com/api/shop/sitemap-products/?page_size=1" \
       | grep -oE '"total":[0-9]+'
     ```

### Phase 3 done when
- [ ] Dump file exists locally and on Hetzner.
- [ ] `pg_restore` ran without errors.
- [ ] Product / brand / category counts match GCP within ±1 (admin may
      have added 1 between dump and verify — acceptable).
- [ ] `docker compose logs db` shows no errors.

---

## Phase 4 — Deploy app + SSL on Hetzner

**Goal**: bring up the full stack, obtain Let's Encrypt cert, verify
endpoints work via direct IP / Host header trick. **DNS is NOT yet pointed
at Hetzner.**

**Duration**: 1 hour.
**Downtime**: 0.
**Prereq**: Phase 3 done (DB restored on Hetzner).

### Steps

1. **U** — on Hetzner, ensure `.env` is filled, then:
   ```bash
   cd /srv/fulfillnext-api/deploy/hetzner
   docker compose build api
   docker compose up -d api nginx
   docker compose logs -f api      # watch for "Listening at: http://0.0.0.0:8000"
   ```

2. **U** — sanity check (HTTP, not yet HTTPS):
   ```bash
   curl -H "Host: api.fulfillnext.com" http://localhost/api/shop/brands-list/
   # expect JSON, 200
   ```
   From outside server (over the public IP):
   ```bash
   curl -H "Host: api.fulfillnext.com" http://<HETZNER_IP>/api/shop/sitemap-products/?page=1
   ```

3. **A** — write `deploy/hetzner/scripts/ssl-init.sh`:
   ```bash
   #!/usr/bin/env bash
   set -e
   DOMAIN=api.fulfillnext.com
   EMAIL=${LETSENCRYPT_EMAIL:-hai.pham@genesisda.com}
   cd /srv/fulfillnext-api/deploy/hetzner
   docker compose run --rm certbot certonly \
     --webroot -w /var/www/certbot \
     -d "$DOMAIN" --email "$EMAIL" \
     --agree-tos --non-interactive --no-eff-email
   docker compose exec nginx nginx -s reload
   ```

4. **U** — **Pre-flight**: this requires `api.fulfillnext.com` to resolve to
   `<HETZNER_IP>`. Two options:
   - **Option A (recommended)**: temporarily edit local `/etc/hosts` on the
     server to point `api.fulfillnext.com` to `127.0.0.1`. **No** —
     Let's Encrypt verifies from external. Need real DNS or use
     `--manual` mode. Use Option B instead.
   - **Option B**: temporarily add a DNS A record `api-test.fulfillnext.com
     → <HETZNER_IP>` and request cert for that name first to confirm
     plumbing works. Then in Phase 5, after DNS cutover, request cert
     for `api.fulfillnext.com`. Adjust `ssl-init.sh` to take a domain arg.
   - **Option C (simpler)**: skip SSL until Phase 5. After DNS cuts over,
     run ssl-init then. Means cutover takes longer (~30 min vs 10 min)
     because you're requesting cert during downtime.

   **Default decision**: Option C — defer cert to Phase 5.

### Phase 4 done when
- [ ] `docker compose ps` shows `api`, `db`, `redis`, `nginx` all healthy.
- [ ] `curl -H "Host: api.fulfillnext.com" http://<HETZNER_IP>/api/shop/brands-list/`
      returns the same JSON as production.
- [ ] `docker compose logs api` shows no error spam.
- [ ] Admin endpoint loads via Host header trick:
      `curl -H "Host: api.fulfillnext.com" http://<HETZNER_IP>/acp/login/`
      returns Django login HTML (200).

---

## Phase 5 — DNS cutover

**Goal**: switch `api.fulfillnext.com` to the Hetzner IP. **This is the only
phase with downtime** (~10–30 min).

**Duration**: 30 min active, plus DNS propagation wait.
**Downtime**: 10–30 min.
**Prereq**: Phases 1–4 all green; user has reviewed verification checklist.

### T-24 hours

1. **U** — In current DNS provider, change TTL of `api.fulfillnext.com` A/CNAME
   record to **300 seconds**. Wait ≥ existing TTL (usually 1 hour) to ensure
   resolvers honor the new low TTL.

### Cutover (T = 0)

1. **U** — announce maintenance window if needed.

2. **U** — drain Cloud Run traffic (so no further writes to the GCP DB):
   ```bash
   gcloud run services update fulfillnext-api \
     --project=fulfillnext --region=asia-southeast1 \
     --no-traffic
   ```
   (This sets all revisions to 0% traffic. Site goes down at this point.)

3. **U** — final dump from Cloud SQL to capture writes between Phase 3 and
   now:
   ```bash
   bash deploy/hetzner/scripts/export-from-gcp.sh
   scp dump-*.sql deploy@<HETZNER_IP>:/srv/fulfillnext-api/final-dump.sql
   ```

4. **U** — on Hetzner, import final dump:
   ```bash
   cd /srv/fulfillnext-api/deploy/hetzner
   bash scripts/import-to-hetzner.sh /srv/fulfillnext-api/final-dump.sql
   docker compose up -d api
   ```

5. **U** — change DNS record:
   - Remove existing CNAME `api.fulfillnext.com → ghs.googlehosted.com`.
   - Add A record `api.fulfillnext.com → <HETZNER_IPV4>`, TTL 300.
   - (Optional) AAAA record → `<HETZNER_IPV6>`.

6. **U** — wait ~5 min, then verify DNS propagation:
   ```bash
   dig api.fulfillnext.com +short
   # → should return <HETZNER_IPV4>
   ```

7. **U** — issue Let's Encrypt cert for the now-public domain:
   ```bash
   bash /srv/fulfillnext-api/deploy/hetzner/scripts/ssl-init.sh
   ```

8. **U** — verify HTTPS works:
   ```bash
   curl -A "Mozilla/5.0" https://api.fulfillnext.com/api/shop/brands-list/
   curl -A "Mozilla/5.0" https://api.fulfillnext.com/acp/login/
   curl -A "Mozilla/5.0" https://api.fulfillnext.com/api/shop/sitemap-products/?page=1 \
     | grep -oE '"total":[0-9]+'
   ```

9. **U** — verify FE works against new BE:
   - Open <https://www.fulfillnext.com/> in incognito.
   - Navigate to a product detail page.
   - Open admin Next.js (`/admin`), add a test product, save. Confirm product
     appears in BE via API.

### Rollback procedure (if any verification fails)

1. Change DNS A record back to the old CNAME `ghs.googlehosted.com`.
2. Restore Cloud Run traffic:
   ```bash
   gcloud run services update-traffic fulfillnext-api \
     --project=fulfillnext --region=asia-southeast1 --to-latest
   ```
3. Wait ~5 min for DNS to revert.
4. Note: any writes that happened against the Hetzner DB after step 4 of
   cutover are LOST in this rollback. Check Hetzner DB for new data and
   re-export → import to Cloud SQL if rollback persists more than briefly.

### Phase 5 done when
- [ ] `dig api.fulfillnext.com` resolves to `<HETZNER_IPV4>` from
      multiple resolvers (Google `8.8.8.8`, Cloudflare `1.1.1.1`).
- [ ] HTTPS works with valid Let's Encrypt cert (browser shows lock).
- [ ] All shop API endpoints return correct data.
- [ ] Admin login works.
- [ ] FE pages load product data without errors.

---

## Phase 6 — Verify, monitor, cleanup

**Goal**: prove stability for 7 days, then decommission GCP.

**Duration**: 7 days passive monitoring + 1 hour cleanup.
**Downtime**: 0.
**Prereq**: Phase 5 complete.

### Day 0–7

1. **U** — daily check (5 min/day):
   - `docker compose ps` (all healthy).
   - `docker compose logs api --since 24h | grep -iE "error|critical"` (zero or expected only).
   - `htop` — CPU < 60% sustained, RAM with headroom > 4 GB.
   - `df -h` — disk < 60%.

2. **A/U** — set up Cloudflare in front of Hetzner:
   - Add `fulfillnext.com` to Cloudflare (already there if Vercel uses it).
   - For `api.fulfillnext.com`: enable Cloudflare proxy (orange cloud).
   - SSL/TLS mode: **Full (strict)**.
   - Caching: Bypass for `/api/`, `/acp/`; default cache for `/static/`,
     `/media/`.
   - Verify with `curl -I https://api.fulfillnext.com/` — should show
     `cf-ray:` header.

3. **A/U** — set up off-site DB backup (in addition to Hetzner snapshot):
   - Cron `pg_dump` weekly to Cloudflare R2 or back to GCS.
   - Script: `deploy/hetzner/scripts/weekly-backup.sh`.

### Day 7+ — decommission GCP

Only after 7 days of clean operation:

1. **U** — delete Cloud Run service:
   ```bash
   gcloud run services delete fulfillnext-api \
     --project=fulfillnext --region=asia-southeast1 --quiet
   ```

2. **U** — delete Cloud SQL instance (this is permanent):
   ```bash
   # Final safety dump first
   bash deploy/hetzner/scripts/export-from-gcp.sh
   # Move dump to long-term storage
   gsutil cp dump-*.sql gs://fulfillnext_cloudbuild/archive/

   gcloud sql instances delete fulfillnext-db \
     --project=fulfillnext --quiet
   ```

3. **U** — clean up Cloud Run domain mapping:
   ```bash
   gcloud beta run domain-mappings delete \
     --domain=api.fulfillnext.com \
     --project=fulfillnext --region=asia-southeast1 --quiet
   ```

4. **U** — keep `gs://fulfillnext-media` (still serving images) and
   `gs://fulfillnext_cloudbuild` (archive bucket) — minimal cost (~$0.10/mo).

5. **U** — adjust GCP billing budget alert from 1M VND down to 50k VND so
   any leftover charge surfaces immediately.

### Phase 6 done when
- [ ] 7 days of clean logs.
- [ ] Cloudflare proxy active, no SSL warnings.
- [ ] Off-site weekly backup confirmed (1 backup file in archive).
- [ ] Cloud Run + Cloud SQL deleted.
- [ ] Final monthly cost on Hetzner + GCS ≈ €34 (~870k VND).

---

## Appendix A — files index

| Path | Owned by | Phase | Purpose |
|---|---|---|---|
| `deploy/hetzner/MIGRATION_PLAN.md` | this doc | — | Plan |
| `deploy/hetzner/docker-compose.yml` | A | 2 | Stack |
| `deploy/hetzner/Dockerfile.prod` | A | 2 | Prod image (no seed_demo) |
| `deploy/hetzner/entrypoint.prod.sh` | A | 2 | Prod entrypoint |
| `deploy/hetzner/.env.example` | A | 2 | Env template |
| `deploy/hetzner/nginx/nginx.conf` | A | 2 | Main nginx |
| `deploy/hetzner/nginx/api.fulfillnext.com.conf` | A | 2 | Server block |
| `deploy/hetzner/postgres/init.sql` | A | 2 | Initial DB user |
| `deploy/hetzner/scripts/bootstrap.sh` | A | 1 | Server hardening |
| `deploy/hetzner/scripts/export-from-gcp.sh` | A | 3, 5 | Cloud SQL → SQL file |
| `deploy/hetzner/scripts/import-to-hetzner.sh` | A | 3, 5 | SQL file → local Postgres |
| `deploy/hetzner/scripts/ssl-init.sh` | A | 5 | Let's Encrypt cert |
| `deploy/hetzner/scripts/weekly-backup.sh` | A | 6 | Off-site DB backup |

## Appendix B — secrets & env vars

Generate locally before Phase 3:
- `POSTGRES_PASSWORD`: `openssl rand -base64 32`
- `DJANGO_SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(50))"`

Reuse from current Cloud Run env (read with `gcloud run services describe ...`):
- `ADMIN_API_KEY`
- `SITE_URL`
- `CSRF_TRUSTED_ORIGINS`
- `CORS_ALLOWED_ORIGINS`
- `GS_BUCKET_NAME`

Never commit `.env`. The repo only ships `.env.example`.

## Appendix C — verification queries (run on Hetzner DB after each restore)

```sql
-- Counts
SELECT 'products', COUNT(*) FROM pod_shop_product WHERE status='A'
UNION ALL SELECT 'brands', COUNT(*) FROM pod_shop_brand
UNION ALL SELECT 'categories', COUNT(*) FROM pod_shop_category
UNION ALL SELECT 'tags', COUNT(*) FROM pod_shop_tag
UNION ALL SELECT 'articles', COUNT(*) FROM articles_article
UNION ALL SELECT 'users', COUNT(*) FROM auth_user;

-- Spot-check Site (must be the production domain, not localhost!)
SELECT id, domain, name FROM django_site WHERE id=1;
-- If this shows localhost:8000, seed_demo ran in production — investigate.

-- Spot-check a recent product
SELECT id, name, slug, status, updated_at
FROM pod_shop_product
ORDER BY updated_at DESC LIMIT 5;

-- Confirm migrations are all applied
SELECT app, name FROM django_migrations ORDER BY id DESC LIMIT 10;
```

## Appendix D — known gotchas

- **Postgres dump SQL flavor**: `gcloud sql export sql` produces a Postgres
  plaintext dump. Restore via `psql`, not `pg_restore`.
- **Sequences after restore**: most plaintext dumps include `setval()` calls
  for sequences. Confirm by `SELECT last_value FROM pod_shop_product_id_seq;`
  — should be ≥ max(id) in pod_shop_product.
- **Time zone**: ensure Postgres TZ is UTC (default), and Django
  `TIME_ZONE = 'UTC'` (check `pezura/settings.py`).
- **`DEFAULT_FILE_STORAGE`**: if Django settings switch storage backend
  based on env (`if GS_BUCKET_NAME: use storages.backends.gcloud`), keeping
  `GS_BUCKET_NAME` set will continue using GCS. To migrate media off GCS
  later, unset that var and run a one-time copy script.
- **GCS service-account credentials**: Cloud Run had implicit auth via the
  default service account. On Hetzner, you need a JSON key:
  - In GCP Console → IAM → Service Accounts → create key for the SA that
    owns `fulfillnext-media` (or grant Storage Object Admin to a new SA).
  - Place key at `deploy/hetzner/secrets/gcs-key.json` (gitignored).
  - Mount into the api container: `volumes: ./secrets/gcs-key.json:/secrets/gcs-key.json:ro`
  - Set env: `GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcs-key.json`
- **Logging**: Django writes to `/app/logs/` per current settings. Either
  mount a volume or `LOGGING` to stdout (recommended for Docker). Adjust
  `pezura/settings.py` if needed.

---

## Sub-agent instructions

If you are a sub-agent invoked to execute one phase of this plan:

1. Re-read **Context** at the top of this file. Every phase depends on it.
2. Confirm prereqs in your phase's "Prereq" line. If unmet, stop and report.
3. Distinguish **U** (user) vs **A** (you) tasks. Never run **U** tasks; for
   those, output the exact commands the user should run.
4. After completing, re-run the "Phase X done when" checklist. Report each
   item as ✅ or ❌ with evidence (output excerpts).
5. Do not skip ahead to a later phase even if you have time. Each phase is
   atomic.
6. Never delete GCP resources before Phase 6 day-7+ (irreversible).
7. Never disable `sshd_config PasswordAuthentication` before confirming
   the user's SSH key works (lockout risk).
8. Report any deviation from the plan back to the parent agent.
