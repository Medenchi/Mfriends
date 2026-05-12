#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/mfriends"
REPO_DIR="${1:-$(pwd)}"

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx curl rsync apache2-utils

sudo useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin mfriends 2>/dev/null || true
sudo mkdir -p "$APP_DIR"/{app,frontend,data,uploads,logs,scripts}
sudo rsync -a --delete "$REPO_DIR"/backend "$APP_DIR"/app/
sudo rsync -a --delete "$REPO_DIR"/frontend/mfriends/ "$APP_DIR"/frontend/
sudo rsync -a "$REPO_DIR"/deploy/scripts/ "$APP_DIR"/scripts/
sudo chmod +x "$APP_DIR"/scripts/*.sh

if [[ ! -f "$APP_DIR/.env" ]]; then
  sudo cp "$REPO_DIR/.env.example" "$APP_DIR/.env"
  echo "Edit $APP_DIR/.env before starting services."
fi

if [[ ! -f /etc/nginx/.mfriends-dev.htpasswd ]]; then
  sudo htpasswd -bc /etc/nginx/.mfriends-dev.htpasswd devin change-this-dev-password
  echo "Change /etc/nginx/.mfriends-dev.htpasswd before exposing dev.denchy.cyou."
fi

sudo python3 -m venv "$APP_DIR"/venv
sudo "$APP_DIR"/venv/bin/pip install --upgrade pip
sudo "$APP_DIR"/venv/bin/pip install "$REPO_DIR"

sudo chown -R mfriends:mfriends "$APP_DIR"
sudo cp "$REPO_DIR"/deploy/systemd/mfriends-api.service /etc/systemd/system/
sudo cp "$REPO_DIR"/deploy/nginx/mfriends.conf /etc/nginx/sites-available/mfriends.conf
sudo ln -sf /etc/nginx/sites-available/mfriends.conf /etc/nginx/sites-enabled/mfriends.conf
sudo nginx -t
sudo systemctl daemon-reload

echo "Next: configure wildcard DNS, issue certbot certs for denchy.cyou, then systemctl enable --now mfriends-api nginx"
