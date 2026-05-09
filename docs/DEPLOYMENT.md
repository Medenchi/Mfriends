# MFriends deployment guide

## Routing

Use a single shared domain. MFriends does not require a subdomain and should not take over `/` if other projects already live on the same VPS:

- `https://malinacode.is-a.dev/mfriends/` → static frontend
- `https://malinacode.is-a.dev/api/` → FastAPI
- `wss://malinacode.is-a.dev/ws` → WebSocket chat and WebRTC signaling
- `https://malinacode.is-a.dev/uploads/` → validated uploads

If the same domain hosts multiple projects, include `deploy/nginx/mfriends.conf` alongside the other project location blocks and keep MFriends limited to these paths.

## Deploy

```bash
git clone https://github.com/Medenchi/Mfriends.git
cd Mfriends
sudo bash deploy/scripts/install-vps.sh "$PWD"
sudo nano /opt/mfriends/.env
```

Set:

- `SECRET_KEY`
- `DATABASE_PATH=/opt/mfriends/data/mfriends.sqlite3`
- `UPLOAD_DIR=/opt/mfriends/uploads`
- SMTP credentials for `mail@malinacode.is-a.dev`
- `DUCKDNS_DOMAIN=malinacode`
- `DUCKDNS_TOKEN`
- optional external moderation API variables

Initialize database:

```bash
sudo -u mfriends /opt/mfriends/venv/bin/python -m backend.app.db.init_db
```

Start backend:

```bash
sudo systemctl enable --now mfriends-api
sudo systemctl status mfriends-api
```

## SSL

After DNS resolves to the VPS:

```bash
sudo certbot --nginx -d malinacode.is-a.dev --redirect
sudo systemctl reload nginx
```

## WebRTC

The app uses STUN by default:

```js
stun:stun.l.google.com:19302
```

For production reliability, add TURN credentials from a provider such as Coturn, Twilio, Metered or Cloudflare Calls. Do not relay video through the FastAPI VPS.

## Operations

```bash
sudo journalctl -u mfriends-api -f
sudo journalctl -u duckdns-mfriends.service -n 100
sudo nginx -t
curl -fsS https://malinacode.is-a.dev/api/health
```
