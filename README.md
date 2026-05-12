# MFriends

MFriends is a production-oriented, low-RAM fullstack platform for finding friends, teammates and activity buddies. It is not a dating app.

## Stack

- Frontend: HTML, CSS, Vanilla JavaScript
- Backend: Python FastAPI
- Database: SQLite
- Realtime: WebSocket
- Video calls: WebRTC P2P signaling only
- Reverse proxy: Nginx virtual hosts
- Hosting target: small VPS with 512 MB RAM

## Domains

Use wildcard DNS for `*.denchy.cyou`:

```text
mfriends.denchy.cyou → static frontend
api.denchy.cyou      → FastAPI REST API
ws.denchy.cyou       → WebSocket chat + WebRTC signaling
cdn.denchy.cyou      → uploads/static files
mail.denchy.cyou     → email services for mail@denchy.cyou
dev.denchy.cyou      → protected development environment
```

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

## Security model

This repository includes:

- JWT access and refresh tokens
- password hashing
- email verification and password reset flows
- rate limiting and anti-spam checks
- upload validation
- moderation hooks for external APIs
- report, block and trust-score storage
- WebSocket authentication
- typing indicators and realtime messaging
- WebRTC signaling without relaying media through the VPS
- verification placeholders with temporary storage and auto-delete windows
- admin moderation queue, suspicious users, analytics and AI moderation logs

AI moderation hooks are intentionally provider-neutral. Configure an external moderation API in environment variables; no local AI model is required.
