# MFriends

MFriends — fullstack-платформа для безопасного поиска друзей, тиммейтов и людей по интересам. Это не dating app: фокус только на дружбе, играх, учёбе, coding buddy, study buddy и совместных онлайн/офлайн активностях.

## Стек

- Frontend: HTML, CSS, Vanilla JavaScript
- Backend: Python FastAPI
- Database: SQLite + WAL
- Realtime: WebSocket
- Video calls: WebRTC P2P, backend только для signaling
- Reverse proxy: Nginx virtual hosts
- Target hosting: маленький VPS от 512 MB RAM

## Домены

Нужен wildcard DNS для `*.denchy.cyou`:

```text
mfriends.denchy.cyou → статический frontend
api.denchy.cyou      → FastAPI REST API
ws.denchy.cyou       → WebSocket chat + WebRTC signaling
cdn.denchy.cyou      → uploads/static files
mail.denchy.cyou     → SMTP/email для mail@denchy.cyou
dev.denchy.cyou      → закрытая dev-среда
```

## Как запустить локально

1. Подготовь Python-окружение:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

2. Создай SQLite-базу:

```bash
python -m backend.app.db.init_db
```

3. Запусти backend:

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Открой frontend одним из вариантов.

Просто файлом:

```text
frontend/mfriends/index.html
```

Или через статический сервер:

```bash
python3 -m http.server 8010 --directory frontend/mfriends
```

После этого открой:

```text
http://127.0.0.1:8010
```

Локальный frontend сам ходит в API по `/api`, поэтому для полного локального режима удобнее проксировать через nginx или открыть backend/frontend под одной точкой. Для быстрой проверки backend API доступен тут:

```text
http://127.0.0.1:8000/api/health
```

## Проверки перед PR/deploy

```bash
ruff check backend tests
pytest -q tests
python3 -m compileall backend
```

## Что уже есть

- JWT access/refresh tokens
- register/login
- email verification и password reset
- профили: avatar, bio, interests, games, hobbies, city/district, friendship preference, trust score
- discovery по интересам/играм/городу/району/верификации
- заявки на онлайн/офлайн активности
- reward validation: можно обучение/коучинг/gaming help/shared tasks, нельзя dating/adult/paid companionship
- realtime chat, typing indicators, image sending, voice placeholder
- WebRTC signaling для P2P calls
- reports, blocks, anti-spam, moderation logs
- hooks под внешние AI moderation API
- verification placeholders: selfie, voice code, liveness
- admin queue, reports dashboard, analytics
- Nginx/systemd/deploy configs под VPS

## Продакшен

Смотри:

- `docs/VPS_SETUP.md`
- `docs/DEPLOYMENT.md`
- `deploy/nginx/mfriends.conf`
- `deploy/systemd/mfriends-api.service`

## Важно про безопасность

Точная GPS-локация не показывается. WebRTC-видео не идёт через VPS. AI-модерация сделана через provider-neutral hooks: локальные AI-модели не запускаются.
