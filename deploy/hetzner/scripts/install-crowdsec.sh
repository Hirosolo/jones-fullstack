#!/usr/bin/env bash
# install-crowdsec.sh
#
# CrowdSec installer for FulfillNext Hetzner box (Ubuntu 24.04).
#
# What it does:
#   1. Installs CrowdSec engine + iptables firewall bouncer
#   2. Installs nginx parser + scraper detection scenarios
#   3. Hooks CrowdSec to the nginx Docker container (no host log mount needed)
#   4. Adds DOCKER-USER chain to bouncer so blocks fire BEFORE Docker NAT
#
# Run as root on the Hetzner host:
#   sudo bash deploy/hetzner/scripts/install-crowdsec.sh
#
# Idempotent — safe to re-run.

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Run as root (use sudo)." >&2
  exit 1
fi

NGINX_CONTAINER="${NGINX_CONTAINER:-fulfillnext-nginx-1}"
BOUNCER_CFG="/etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml"

echo "=== [1/6] Add CrowdSec apt repo ==="
if ! command -v cscli >/dev/null 2>&1; then
  curl -fsSL https://install.crowdsec.net | bash
fi

echo "=== [2/6] Install CrowdSec engine + iptables bouncer ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y crowdsec crowdsec-firewall-bouncer-iptables

echo "=== [3/6] Install nginx parser + scraper scenarios ==="
cscli collections install crowdsecurity/nginx --force || true
cscli scenarios install crowdsecurity/http-bad-user-agent --force || true
cscli scenarios install crowdsecurity/http-crawl-non_statics-ratio --force || true
cscli scenarios install crowdsecurity/http-probing --force || true
cscli scenarios install crowdsecurity/http-sensitive-files --force || true

echo "=== [4/6] Configure acquisition (read nginx Docker container logs) ==="
# Verify the container actually exists; fail fast if not.
if ! docker ps --format '{{.Names}}' | grep -qx "$NGINX_CONTAINER"; then
  echo "ERROR: nginx container '$NGINX_CONTAINER' not running." >&2
  echo "Override with: NGINX_CONTAINER=<name> sudo bash $0" >&2
  exit 1
fi

mkdir -p /etc/crowdsec/acquis.d
cat >/etc/crowdsec/acquis.d/nginx-docker.yaml <<EOF
source: docker
container_name:
  - ${NGINX_CONTAINER}
labels:
  type: nginx
EOF

echo "=== [5/6] Add DOCKER-USER chain to firewall bouncer ==="
# Docker writes its own iptables rules in DOCKER-* chains hooked early.
# Generic INPUT/FORWARD blocks miss container traffic. DOCKER-USER is
# Docker's official extension point for user rules to run BEFORE NAT.
if [ -f "$BOUNCER_CFG" ]; then
  if ! grep -q "DOCKER-USER" "$BOUNCER_CFG"; then
    sed -i '/^iptables_chains:/a\  - DOCKER-USER' "$BOUNCER_CFG"
    echo "Added DOCKER-USER to $BOUNCER_CFG"
  else
    echo "DOCKER-USER already present in $BOUNCER_CFG"
  fi
else
  echo "WARN: $BOUNCER_CFG not found — bouncer config may be elsewhere." >&2
fi

echo "=== [6/6] Restart services ==="
systemctl restart crowdsec
systemctl restart crowdsec-firewall-bouncer
sleep 2

echo
echo "=== Health check ==="
echo "--- crowdsec status ---"
systemctl is-active crowdsec || true
echo "--- bouncer status ---"
systemctl is-active crowdsec-firewall-bouncer || true
echo "--- enabled scenarios ---"
cscli scenarios list -o raw 2>/dev/null | head -20 || true
echo "--- bouncers ---"
cscli bouncers list -o raw 2>/dev/null || true

cat <<'EOF'

Done. Useful commands:

  cscli metrics              # log lines parsed, alerts triggered
  cscli decisions list       # currently banned IPs
  cscli alerts list          # alert history
  tail -f /var/log/crowdsec.log

To test from another machine (NOT on this server):

  for i in $(seq 1 50); do
    curl -s -A "AhrefsBot" https://api.fulfillnext.com/api/shop/products/ >/dev/null
  done
  # Wait 30-60s, then on this server:
  cscli decisions list

Whitelist your office/home IP (so you never get blocked by mistake):

  cscli decisions add --ip <your.ip.addr> --type whitelist --duration 99y
EOF
