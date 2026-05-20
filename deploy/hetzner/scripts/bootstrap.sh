#!/usr/bin/env bash
# Hetzner Cloud server bootstrap — Phase 1 of MIGRATION_PLAN.md
# Run as root on a fresh Ubuntu 24.04 server.
# Usage:  curl -sSL <url>/bootstrap.sh | sudo bash
#  or:    scp bootstrap.sh root@<IP>:/tmp/ && ssh root@<IP> 'bash /tmp/bootstrap.sh'

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "This script must run as root." >&2
  exit 1
fi

DEPLOY_USER="deploy"
APP_DIR="/srv/fulfillnext-api"

echo "=== [1/9] System update ==="
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y dist-upgrade

echo "=== [2/9] Install base packages ==="
apt-get install -y --no-install-recommends \
  curl ca-certificates gnupg lsb-release \
  ufw fail2ban htop git \
  unattended-upgrades apt-listchanges

echo "=== [3/9] Enable unattended security upgrades ==="
cat >/etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
sed -i 's|^//\(\s*"\${distro_id}:\${distro_codename}-security";\)|\1|' \
  /etc/apt/apt.conf.d/50unattended-upgrades || true

echo "=== [4/9] Create deploy user ==="
if ! id -u "$DEPLOY_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash -G sudo "$DEPLOY_USER"
  echo "$DEPLOY_USER ALL=(ALL) NOPASSWD: /usr/bin/apt-get, /usr/bin/systemctl, /usr/sbin/ufw" \
    >/etc/sudoers.d/90-deploy
  chmod 440 /etc/sudoers.d/90-deploy
fi
mkdir -p /home/$DEPLOY_USER/.ssh
if [ -f /root/.ssh/authorized_keys ]; then
  cp /root/.ssh/authorized_keys /home/$DEPLOY_USER/.ssh/authorized_keys
fi
chmod 700 /home/$DEPLOY_USER/.ssh
chmod 600 /home/$DEPLOY_USER/.ssh/authorized_keys 2>/dev/null || true
chown -R $DEPLOY_USER:$DEPLOY_USER /home/$DEPLOY_USER/.ssh

echo "=== [5/9] Harden SSH ==="
# Test that deploy user has key access BEFORE disabling root.
if [ ! -s /home/$DEPLOY_USER/.ssh/authorized_keys ]; then
  echo "ERROR: /home/$DEPLOY_USER/.ssh/authorized_keys is empty." >&2
  echo "Refusing to disable root login (would lock you out)." >&2
  exit 1
fi
cat >/etc/ssh/sshd_config.d/99-hardening.conf <<'EOF'
# fulfillnext hardening — Phase 1
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
ClientAliveInterval 300
ClientAliveCountMax 2
EOF
# Validate config before reload
sshd -t
systemctl reload ssh || systemctl reload sshd

echo "=== [6/9] Configure UFW firewall ==="
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'ssh'
ufw allow 80/tcp comment 'http'
ufw allow 443/tcp comment 'https'
ufw --force enable
ufw status verbose

echo "=== [7/9] Configure fail2ban ==="
cat >/etc/fail2ban/jail.d/sshd.local <<'EOF'
[sshd]
enabled = true
port    = ssh
filter  = sshd
maxretry = 5
findtime = 10m
bantime  = 1h
EOF
systemctl enable --now fail2ban
systemctl restart fail2ban

echo "=== [8/9] Install Docker CE + Compose plugin ==="
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    >/etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
fi
systemctl enable --now docker
usermod -aG docker $DEPLOY_USER

echo "=== [9/9] Prepare app directory ==="
mkdir -p "$APP_DIR"
chown $DEPLOY_USER:$DEPLOY_USER "$APP_DIR"

echo
echo "================================================================"
echo "  ✅ BOOTSTRAP COMPLETE"
echo "================================================================"
echo "  Re-login as:   ssh -i ~/.ssh/hetzner_fulfillnext $DEPLOY_USER@<IP>"
echo "  App dir:       $APP_DIR (owned by $DEPLOY_USER)"
echo "  Docker:        $(docker --version | cut -d, -f1)"
echo "  Compose:       $(docker compose version | head -n1)"
echo "  UFW:           open 22, 80, 443"
echo "  fail2ban:      active (5 retries / 10m → ban 1h)"
echo "  Root SSH:      DISABLED (only $DEPLOY_USER user, key auth only)"
echo "================================================================"
echo "  Next: Phase 2 (deploy app stack)"
echo "================================================================"
