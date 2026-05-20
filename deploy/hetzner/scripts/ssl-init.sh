#!/usr/bin/env bash
# Phase 5 — Obtain Let's Encrypt cert and switch nginx to HTTPS.
# Prereq: api.jones.com DNS already points to this server's IP.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$COMPOSE_DIR"

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi
EMAIL="${LETSENCRYPT_EMAIL:?Set LETSENCRYPT_EMAIL in .env}"

# Accept domain(s) as CLI args, default to api.jones.com
if [ "$#" -eq 0 ]; then
  DOMAINS=("api.jones.com")
else
  DOMAINS=("$@")
fi
PRIMARY="${DOMAINS[0]}"
DOMAIN_FLAGS=()
for d in "${DOMAINS[@]}"; do DOMAIN_FLAGS+=(-d "$d"); done

EXPECTED=$(curl -s -4 ifconfig.me || true)
for d in "${DOMAINS[@]}"; do
  RESOLVED=$(getent ahostsv4 "$d" | awk '{print $1; exit}' || true)
  if [ -n "$EXPECTED" ] && [ -n "$RESOLVED" ] && [ "$EXPECTED" != "$RESOLVED" ]; then
    echo "ERROR: $d resolves to $RESOLVED, but this server is $EXPECTED."
    echo "       Update DNS first, wait for propagation, then re-run."
    exit 1
  fi
done

echo "==> Ensuring nginx is up with HTTP-only config…"
docker compose up -d nginx

echo "==> Requesting Let's Encrypt cert for: ${DOMAINS[*]}"
docker compose run --rm certbot \
  "certbot certonly --webroot -w /var/www/certbot \
   --cert-name $PRIMARY ${DOMAIN_FLAGS[*]} \
   --expand --email $EMAIL \
   --agree-tos --non-interactive --no-eff-email"

echo "==> Switching nginx to HTTPS config (cert path: $PRIMARY)…"
sed "s|__CERT_NAME__|${PRIMARY}|g" nginx/api.fulfillnext.com.https.conf \
  > nginx/api.fulfillnext.com.conf

echo "==> Reloading nginx…"
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload

echo
echo "================================================================"
echo "  ✅ SSL ACTIVE for: ${DOMAINS[*]}"
echo "  Cert name: $PRIMARY (covers all listed domains via SAN)"
echo "  Cert auto-renews via certbot — set up cron in Phase 6."
echo "  Test: curl -I https://${DOMAINS[0]}/"
echo "================================================================"
