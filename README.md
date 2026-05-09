# MFriends

MFriends is a production-oriented, low-RAM platform for finding friends, teammates and activity buddies. It is not a dating app.

The project is designed for a single domain:

```text
malinacode.is-a.dev
├── /mfriends   static frontend
├── /api        FastAPI REST API
├── /ws         WebSocket chat + WebRTC signaling
└── /uploads    protected/static uploaded files
```

Dynamic DNS is expected to use:

```text
malinacode.is-a.dev CNAME → malinacode.duckdns.org → current VPS IP
```

## Stack

- Frontend: HTML, CSS, Vanilla JavaScript
- Backend: Python FastAPI
- Database: SQLite
- Realtime: WebSocket
- Video calls: WebRTC P2P signaling only
- Reverse proxy: Nginx
- Hosting target: small VPS with 512 MB RAM

## Local development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m backend.app.db.init_db
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```text
Open frontend/mfriends/index.html
```

or serve it with any static file server.

## Checks

```bash
ruff check backend tests
pytest
```

## Production deployment

See:

- `docs/VPS_SETUP.md`
- `docs/DEPLOYMENT.md`
- `deploy/nginx/mfriends.conf`
- `deploy/systemd/mfriends-api.service`
- `deploy/systemd/duckdns-mfriends.service`
- `deploy/systemd/duckdns-mfriends.timer`

## Security model

This repository includes:

- JWT access tokens and refresh tokens
- password hashing
- email verification and password reset flows
- rate limiting and anti-spam checks
- upload validation
- moderation hooks for external APIs
- report and trust-score storage
- WebSocket authentication
- WebRTC signaling without relaying media through the VPS

AI moderation hooks are intentionally provider-neutral. Configure an external moderation API in environment variables; no local AI model is required.
