# MFriends deployment guide

## DNS

Create wildcard DNS for `*.denchy.cyou` pointing to the VPS IP. Required hosts:

- `mfriends.denchy.cyou`
- `api.denchy.cyou`
- `ws.denchy.cyou`
- `cdn.denchy.cyou`
- `mail.denchy.cyou`
- `dev.denchy.cyou`

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
- SMTP credentials for `mail@denchy.cyou`
- optional external moderation API variables
- optional TURN variables from a TURN provider

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

After wildcard DNS resolves to the VPS:

```bash
sudo certbot --nginx \
  -d denchy.cyou \
  -d '*.denchy.cyou' \
  --manual --preferred-challenges dns
sudo systemctl reload nginx
```

If DNS-01 wildcard automation is not available, issue separate HTTP certificates:

```bash
sudo certbot --nginx \
  -d mfriends.denchy.cyou \
  -d api.denchy.cyou \
  -d ws.denchy.cyou \
  -d cdn.denchy.cyou \
  -d dev.denchy.cyou
```

## WebSocket deployment

`ws.denchy.cyou/ws` proxies to the same FastAPI process. Nginx keeps `Upgrade` and `Connection` headers and uses long read/send timeouts.

## WebRTC

The app uses STUN by default:

```js
stun:stun.l.google.com:19302
```

For production reliability, add TURN credentials from Coturn, Twilio, Metered or Cloudflare Calls. Do not relay video through the FastAPI VPS.

## Operations

```bash
sudo journalctl -u mfriends-api -f
sudo nginx -t
curl -fsS https://api.denchy.cyou/api/health
```

## Production structure

```text
/opt/mfriends
├── app/backend
├── frontend
├── data/mfriends.sqlite3
├── uploads
├── logs
└── scripts
```
