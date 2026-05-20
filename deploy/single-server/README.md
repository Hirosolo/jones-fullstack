# Jones — Tài liệu deploy trên 1 server vật lý (FE + BE + DB cùng datacenter)

Tài liệu này mô tả kiến trúc và quy trình triển khai toàn bộ stack Jones (Next.js frontend + Django backend + PostgreSQL + Redis + nginx) lên **một server Ubuntu duy nhất**. Toàn bộ service chạy qua Docker Compose, FE/BE/DB nằm trên cùng một mạng nội bộ Docker → BE ↔ DB latency dưới 1 ms, FE ↔ BE đi qua container network không qua public Internet.

Mục tiêu: thay thế kiến trúc tách rời (FE Vercel + BE Hetzner) bằng setup colocate hoàn toàn, giảm latency network và đơn giản hoá vận hành theo phương án anh leader đã nêu.

> **Lưu ý**: tài liệu này tập trung mô tả kiến trúc, requirements, quy trình. Toàn bộ artifact deploy thực tế (Dockerfile, docker-compose.yml, nginx vhosts, scripts) team đang dùng tham khảo tại `deploy/hetzner/` — kế thừa được phần lớn, chỉ cần bổ sung service `web` (Next.js standalone) và vhost nginx cho domain frontend.

---

## 1. Tổng quan kiến trúc

```
                                  Internet
                                     │
                                 443 / 80
                                     │
                          ┌──────────▼──────────┐
                          │       nginx         │   (reverse proxy + TLS)
                          │     :80 / :443      │
                          └─────┬──────────┬────┘
                                │          │
                  www.<domain>  │          │  api.<domain>
                                │          │
                       ┌────────▼──┐   ┌──▼──────────┐
                       │  Next.js  │   │  Django     │
                       │  :3000    │   │  :8000      │
                       │  (web)    │   │  (api)      │
                       └─────┬─────┘   └─┬─────────┬─┘
                             │           │         │
                       (SSR fetch)       │         │
                             │           │         │
                             └───────────┼─────────┤
                                         │         │
                                  ┌──────▼──┐  ┌──▼────┐
                                  │ Postgres│  │ Redis │
                                  │ (db)    │  │       │
                                  └─────────┘  └───────┘

       Docker networks:
         - front : nginx ↔ web, nginx ↔ api          (public-facing)
         - back  : web/api ↔ db, web/api ↔ redis     (internal only)
```

**Đặc điểm:**
- Chỉ có nginx expose port 80/443 ra ngoài. DB, Redis, api, web đều "private" — không bind ra host.
- FE Next.js gọi BE Django qua hostname `api:8000` qua mạng Docker bridge — không qua public DNS/TLS.
- Static + media được nginx serve trực tiếp từ volume mounted của Django container.
- DB và Redis chỉ tiếp xúc với api/web qua network `back` riêng biệt, không expose ra `front`.

---

## 2. Yêu cầu server

| Mục | Tối thiểu | Khuyên dùng |
|-----|-----------|-------------|
| OS | Ubuntu 24.04 LTS | Ubuntu 24.04 LTS |
| CPU | 4 vCPU | 6–8 vCPU |
| RAM | 8 GB | 16 GB |
| Disk | 100 GB SSD | 200 GB NVMe |
| Mạng | 1 Gbps unmetered | 1 Gbps + DDoS protection |
| Vị trí | Cùng region với phần lớn khách | US (East/West) cho khách US |
| IP | 1 IPv4 tĩnh public | + IPv6 nếu có |

**Lưu ý chọn datacenter:**
- Đặt máy ở **datacenter gần khách hàng cuối** (US-East nếu khách Mỹ bờ Đông, US-West nếu bờ Tây).
- Tránh datacenter "rẻ" ở region xa: BE↔DB nhanh nhưng FE → user lại chậm — phản tác dụng.
- Tier-1 ISP (Lumen, NTT, Cogent…) là điểm cộng vì peering tốt với Google/Cloudflare → ít hop.

**Provider gợi ý:**
- Hetzner Cloud (Falkenstein DE, Ashburn US) — giá tốt, network ổn.
- OVHcloud (US East/West, EU) — có option bare-metal.
- DigitalOcean droplet (NYC3 / SFO3) — đơn giản, managed firewall.
- AWS Lightsail / GCP Compute Engine — nếu muốn tích hợp managed services về sau.

---

## 3. Trỏ DNS

Trước khi deploy, trỏ 3 record A về IP server:

| Record | Type | Value |
|--------|------|-------|
| `jones.com` (apex) | A | `<server IP>` |
| `www.jones.com` | A | `<server IP>` |
| `api.jones.com` | A | `<server IP>` |

Đợi DNS propagate (5 phút – 1 giờ) trước khi sang bước SSL. Verify bằng `dig +short <domain>` trên máy local.

---

## 4. Phase 1 — Bootstrap server (cứng hoá + cài Docker)

SSH vào server với quyền root rồi thực hiện theo trình tự:

1. **System update**
   ```bash
   apt update && apt -y dist-upgrade
   ```

2. **Cài base packages**
   ```bash
   apt install -y curl ca-certificates gnupg ufw fail2ban htop git rsync \
                  unattended-upgrades apt-listchanges
   ```

3. **Bật unattended security upgrades** — tự patch CVE mỗi đêm:
   ```bash
   echo 'APT::Periodic::Update-Package-Lists "1";
   APT::Periodic::Unattended-Upgrade "1";
   APT::Periodic::AutocleanInterval "7";' > /etc/apt/apt.conf.d/20auto-upgrades
   ```

4. **Tạo deploy user (sudo nopasswd)**
   ```bash
   adduser --disabled-password --gecos '' deploy
   echo "deploy ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-deploy
   chmod 0440 /etc/sudoers.d/90-deploy
   # Copy SSH key của root sang deploy
   install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
   install -m 600 -o deploy -g deploy /root/.ssh/authorized_keys /home/deploy/.ssh/
   ```

5. **Cứng hoá SSH** — tắt password auth, chỉ key-based:
   ```bash
   sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
   sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
   systemctl restart ssh
   ```

6. **Bật firewall** — chỉ allow 22, 80, 443:
   ```bash
   ufw default deny incoming
   ufw default allow outgoing
   ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
   ufw --force enable
   ```

7. **Cài Docker CE + Compose plugin** (chính thức từ docker.com):
   ```bash
   install -m 0755 -d /etc/apt/keyrings
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
     -o /etc/apt/keyrings/docker.asc
   chmod a+r /etc/apt/keyrings/docker.asc
   . /etc/os-release
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
     https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" \
     > /etc/apt/sources.list.d/docker.list
   apt update
   apt install -y docker-ce docker-ce-cli containerd.io \
                  docker-buildx-plugin docker-compose-plugin
   systemctl enable --now docker
   usermod -aG docker deploy
   ```

Logout root, login lại bằng `deploy` để docker group có hiệu lực:

```bash
ssh deploy@<server-ip>
docker ps   # phải chạy được không cần sudo
```

> Toàn bộ các bước trên team đã viết sẵn script idempotent ở `deploy/hetzner/scripts/bootstrap.sh` — có thể dùng lại nguyên xi cho server mới.

---

## 5. Phase 2 — Chuẩn bị stack Docker Compose

Cấu trúc thư mục được khuyến nghị:

```
/srv/jones/                          # repo clone về đây
└── deploy/single-server/                  # thư mục compose chạy trong này
    ├── docker-compose.yml                 # định nghĩa 5 service
    ├── .env                               # biến môi trường (gitignore)
    ├── Dockerfile.api                     # build Django image
    ├── Dockerfile.web                     # build Next.js standalone
    ├── entrypoint.api.sh                  # entrypoint Django (migrate + collectstatic)
    ├── nginx/                             # nginx config + vhost
    ├── media-bucket/                      # ảnh sản phẩm (gitignore, bind-mount)
    └── scripts/                           # ssl-init, daily-backup
```

**Compose stack mô tả:**

| Service | Image / Build | Purpose | Expose |
|---------|---------------|---------|--------|
| `db` | `postgres:16-alpine` | Lưu data | nội bộ network `back` |
| `redis` | `redis:7-alpine` | Cache, session | nội bộ network `back` |
| `api` | Build từ `backend/` | Django + gunicorn | nội bộ network `back` + `front` |
| `web` | Build Next.js standalone từ `frontend/` | Next.js server | nội bộ network `back` + `front` |
| `nginx` | `nginx:alpine` | Reverse proxy + SSL + serve static/media | host 80/443 |

**Tham khảo file mẫu**: stack BE hiện đang chạy trên Hetzner ở `deploy/hetzner/docker-compose.yml`. Để áp dụng cho single-server, **add thêm service `web`** với pattern:

- Build từ Dockerfile multi-stage (deps → builder → runner) với `output: 'standalone'` của Next.js (đã hỗ trợ sẵn trong `frontend/next.config.ts` khi env `DOCKER_BUILD=1`).
- Bake `NEXT_PUBLIC_*` env vars vào build-args (vì Next.js inline chúng vào client bundle tại build-time, runtime env không có tác dụng).
- Runtime expose port 3000, internal-only.
- Pass thêm runtime env `DJANGO_INTERNAL_URL=http://api:8000` để SSR fetch đi qua container network thay vì public DNS.

---

## 6. Phase 3 — Biến môi trường `.env`

File `.env` (gitignore) đặt cạnh `docker-compose.yml`. Bắt buộc:

| Biến | Ví dụ | Generate |
|------|-------|----------|
| `WEB_DOMAIN` | `www.jones.com` | — |
| `API_DOMAIN` | `api.jones.com` | — |
| `POSTGRES_DB` | `jones` | — |
| `POSTGRES_USER` | `django` | — |
| `POSTGRES_PASSWORD` | (random) | `openssl rand -base64 32` |
| `DJANGO_SECRET_KEY` | (random) | `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `ADMIN_API_KEY` | (random) | `openssl rand -hex 21` |
| `LETSENCRYPT_EMAIL` | `ops@yourcompany.com` | — |

Tuỳ chọn:

| Biến | Mục đích |
|------|----------|
| `NEXT_PUBLIC_GA_ID` | Google Analytics tracking ID |
| `NEXT_PUBLIC_GOOGLE_ADS_ID` | Google Ads conversion ID |
| `WP_SHOP_BASE_URL`, `WP_SHOP_WC_CONSUMER_KEY`, `WP_SHOP_WC_CONSUMER_SECRET` | Nếu sync product/review từ WooCommerce source store |

> Mẫu `.env.example` tham khảo: `deploy/hetzner/.env.example` (chỉ cần bổ sung `WEB_DOMAIN` cho frontend).

---

## 7. Phase 4 — Build + khởi động stack

```bash
cd /srv/jones/deploy/single-server

# Bring up infra trước
docker compose up -d db redis
sleep 10
docker compose ps   # cả 2 phải UP/HEALTHY

# Build api + web (lần đầu 5-10 phút)
docker compose build api web

# Start everything
docker compose up -d
docker compose ps   # 5 containers phải UP
```

Verify HTTP-only:

```bash
curl -H "Host: api.jones.com" http://localhost/api/shop/brands-list/
curl -H "Host: www.jones.com"  http://localhost/
```

Cả 2 phải trả `200 OK`.

---

## 8. Phase 5 — Restore data (nếu migrate từ Hetzner)

Skip nếu deploy mới hoàn toàn.

Nếu migrate từ instance đang chạy:

```bash
# Trên server cũ — dump DB:
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  | gzip -9 > /tmp/dump-latest.sql.gz

# scp lên server mới
scp /tmp/dump-latest.sql.gz deploy@<new-server-ip>:/tmp/

# Trên server mới — restore:
gunzip -c /tmp/dump-latest.sql.gz | \
  docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

# Copy media files
rsync -avz <old-server>:/srv/fulfillnext-api/deploy/hetzner/media-bucket/ \
           /srv/jones/deploy/single-server/media-bucket/

docker compose restart api
```

---

## 9. Phase 6 — Bật SSL Let's Encrypt

Đợi DNS đã propagate. Sau đó:

```bash
# 1) Verify DNS trỏ đúng
dig +short www.jones.com api.jones.com

# 2) Issue cert qua certbot container (cần webroot challenge)
docker compose run --rm certbot 'certbot certonly --webroot -w /var/www/certbot \
   --cert-name jones.com -d jones.com -d www.jones.com \
   --email <your-email> --agree-tos --non-interactive --no-eff-email'

docker compose run --rm certbot 'certbot certonly --webroot -w /var/www/certbot \
   --cert-name api.jones.com -d api.jones.com \
   --email <your-email> --agree-tos --non-interactive --no-eff-email'

# 3) Swap nginx config từ HTTP-only sang HTTPS edition
# (template HTTPS đã có sẵn trong deploy/hetzner/nginx/*.https.conf — tham khảo và adapt)
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
```

Verify:

```bash
curl -sI https://www.jones.com/  | grep "^HTTP"     # → HTTP/2 200
curl -sI https://api.jones.com/ | grep "^HTTP"
```

**Auto-renew** (cert có hạn 90 ngày):

```bash
sudo crontab -e
# Thêm dòng:
0 3 * * * cd /srv/jones/deploy/single-server && docker compose run --rm certbot 'certbot renew' && docker compose exec nginx nginx -s reload
```

---

## 10. Phase 7 — Backup automation

**Daily backup** — cron job 2 giờ sáng hàng ngày:

```bash
#!/usr/bin/env bash
# /srv/jones/scripts/daily-backup.sh
set -euo pipefail
cd /srv/jones/deploy/single-server
set -a; . ./.env; set +a

BACKUP_ROOT=/srv/jones/backups
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p "$BACKUP_ROOT/db" "$BACKUP_ROOT/media"

# DB dump (consistent snapshot từ trong container db)
docker compose exec -T db sh -c \
  "pg_dump -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\"" \
  | gzip -9 > "$BACKUP_ROOT/db/dump-$TS.sql.gz"

# Media archive
tar -czf "$BACKUP_ROOT/media/media-$TS.tar.gz" -C . media-bucket

# Retention: xoá > 14 ngày
find "$BACKUP_ROOT" -type f -mtime +14 -delete
```

```bash
sudo crontab -e
# Thêm dòng:
0 2 * * * /srv/jones/scripts/daily-backup.sh
```

**Off-site backup (cần thiết)** — sync sang S3 / Backblaze B2 / Wasabi mỗi tuần:

```bash
# Setup rclone 1 lần qua: rclone config
sudo crontab -e
# Chủ nhật 4 giờ sáng:
0 4 * * 0 rclone sync /srv/jones/backups/ remote:jones-backup/
```

---

## 11. Verify deploy thành công — Checklist

- [ ] `docker compose ps` → 5 services UP (db, redis, api, web, nginx)
- [ ] `curl -sI https://www.jones.com/` → `HTTP/2 200`
- [ ] `curl -sI https://api.jones.com/api/shop/brands-list/` → `HTTP/2 200`
- [ ] Browser test homepage → render đúng, DevTools Network không có 4xx/5xx
- [ ] Browser test 1 product page → ảnh hiển thị, reviews load
- [ ] `/admin/` → login OK, list product hiện
- [ ] `docker compose logs --tail=20 api` → không Traceback
- [ ] `docker compose logs --tail=20 web` → "Ready in X ms"
- [ ] SSL Labs scan (https://www.ssllabs.com/ssltest/) → A hoặc A+

---

## 12. Update workflow (deploy code mới)

```bash
ssh deploy@<server-ip>
cd /srv/jones
git pull origin master

cd deploy/single-server
bash /srv/jones/scripts/daily-backup.sh   # backup trước khi update

# Rebuild image bị thay đổi
docker compose build api      # nếu backend/ thay đổi
docker compose build web      # nếu frontend/ thay đổi

# Replace container, giữ nguyên db/redis/nginx
docker compose up -d --no-deps api
docker compose up -d --no-deps web

# Verify
docker compose logs --tail=30 api
docker compose logs --tail=30 web
```

**Quan trọng:** `--no-deps` đảm bảo Postgres và Redis container KHÔNG bị restart → data volume `pgdata` không động vào.

Nếu chỉ thay đổi nginx config:

```bash
docker compose exec nginx nginx -t       # test config
docker compose exec nginx nginx -s reload   # hot reload, no downtime
```

---

## 13. Monitoring & Logs

**Logs realtime:**

```bash
docker compose logs -f api      # Django gunicorn
docker compose logs -f web      # Next.js server
docker compose logs -f nginx    # nginx access + error
docker compose logs -f db       # Postgres
```

**Disk + container metrics:**

```bash
df -h                           # disk tổng
docker system df                # docker overhead
du -sh deploy/single-server/media-bucket/
docker stats --no-stream        # CPU/RAM mỗi container
```

**Postgres slow queries (debug):**

```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "SELECT pid, now()-query_start AS duration, state, query
   FROM pg_stat_activity WHERE state != 'idle'
   ORDER BY duration DESC LIMIT 5;"
```

---

## 14. Troubleshooting

### Build error
```bash
docker compose build --no-cache <service>   # clean rebuild
```

### Web container 502 từ nginx
- Check `docker compose ps web` — UP?
- `docker compose logs --tail=100 web` — xem stack trace
- Common: `NEXT_PUBLIC_*` không được bake (phải pass qua build-args). Rebuild `--no-cache`.

### Api không kết nối được DB
- `docker compose ps db` — healthy?
- `docker compose exec api python manage.py dbshell` — test
- Entrypoint retry 30 lần × 2s = 60s, sau đó báo lỗi và container restart.

### Cert Let's Encrypt fail
- Common: rate limit (50 certs/tuần/domain). Đợi 1 tuần hoặc dùng `--staging` để test trước.
- DNS chưa propagate: `dig +short <domain>` → đúng IP trước khi issue.

### Restore DB từ backup
```bash
docker compose stop api      # tránh ghi đè
gunzip -c /srv/jones/backups/db/dump-YYYYMMDD-HHMMSS.sql.gz | \
  docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose start api
```

### Rollback deploy
```bash
git log --oneline -10
git checkout <commit-sha>
docker compose build api web
docker compose up -d --no-deps api web
```

---

## 15. Bảo trì định kỳ

| Tần suất | Việc |
|----------|------|
| Daily (auto) | DB + media backup cron |
| Weekly (auto) | rclone sync backup off-site |
| Monthly | `docker system prune -af` (giảm image overhead) |
| Quarterly | `apt update && apt upgrade` (kernel + system) |
| 6 tháng | Rotate `ADMIN_API_KEY`, `DJANGO_SECRET_KEY` |
| Yearly | Audit firewall, restore drill từ backup |

---

## 16. Đáp lời concerns của anh leader

> *"Setup chung một con server, chung nhà cung cấp + cùng datacenter là được. Miễn sao BE vs DB cùng mạng nội bộ sẽ đảm bảo tốc độ."*

✅ Đã thoả: cả 5 service (db, redis, api, web, nginx) chạy trên **cùng một host Linux**, qua **mạng Docker bridge** (`back`/`front`). Latency BE↔DB là loopback (~0.1ms), không qua public network.

> *"Nếu setup được mọi thứ trên một con Ubuntu thuần được chung một vị trí hết tự dưng web nó mượt thôi."*

✅ FE Next.js gọi API qua hostname `api:8000` qua mạng container (`back`), **không qua public Internet**, không qua DNS resolve hop. Page load TTFB cải thiện 50-150ms so với setup tách rời (FE Vercel ↔ BE Hetzner qua public HTTPS).

> *"Tuỳ thuộc trình độ DevOps cấu hình tối ưu là đc."*

Stack tuân thủ Docker best practice: image phân lớp (deps → builder → runner), non-root runtime user, healthcheck Postgres, restart policy `always`, log rotation qua nginx buffered. Tune thêm khi cần dựa trên `docker compose logs` + `docker stats` realtime metric.

> *"Tài liệu hướng dẫn setup chi tiết tụi e cứ viết kĩ vào gửi a a xem thử rồi a setup lên thẳng server bên a xem ntn."*

✅ Tài liệu này. Mẫu artifact tham khảo (Dockerfile.prod, docker-compose.yml, nginx vhosts, ssl-init.sh, bootstrap.sh, weekly-backup.sh) hiện đang chạy production tại `deploy/hetzner/` của repo — anh có thể clone về, adapt 2 chỗ chính:
1. Thêm service `web` (Next.js) vào docker-compose.
2. Thêm vhost nginx cho `www.jones.com` trỏ về `web:3000`.

---

## 17. References trong repo

| Path | Mục đích |
|------|----------|
| `deploy/hetzner/docker-compose.yml` | Reference compose stack đang chạy production (cần thêm service `web`) |
| `deploy/hetzner/Dockerfile.prod` | Reference Django image build |
| `deploy/hetzner/entrypoint.prod.sh` | Reference Django entrypoint (migrate + collectstatic + gunicorn) |
| `deploy/hetzner/nginx/` | Reference nginx vhost templates (HTTP + HTTPS) |
| `deploy/hetzner/scripts/bootstrap.sh` | Reference server bootstrap idempotent |
| `deploy/hetzner/scripts/ssl-init.sh` | Reference Let's Encrypt issue + swap |
| `deploy/hetzner/scripts/weekly-backup.sh` | Reference backup pattern |
| `deploy/hetzner/.env.example` | Reference biến môi trường BE |
| `frontend/next.config.ts` | Frontend đã hỗ trợ `output: 'standalone'` khi build với `DOCKER_BUILD=1` |
