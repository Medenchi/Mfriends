# Архитектура MFriends

MFriends — friendship-first fullstack-платформа для поиска друзей, тиммейтов, study/coding buddy и безопасных онлайн/офлайн активностей. Это явно не dating app.

## Domain architecture

Wildcard DNS должен направлять `*.denchy.cyou` на VPS. Nginx роутит по virtual host:

- `mfriends.denchy.cyou` → статический HTML/CSS/vanilla JS frontend
- `api.denchy.cyou` → FastAPI REST API
- `ws.denchy.cyou` → WebSocket chat и WebRTC signaling
- `cdn.denchy.cyou` → uploads/static files
- `mail.denchy.cyou` → SMTP/IMAP endpoint для `mail@denchy.cyou`
- `dev.denchy.cyou` → защищённая dev-среда

## Backend modules

- `api/auth.py` — JWT auth, refresh tokens, email verification, password reset, cooldowns
- `api/profiles.py` — CRUD профиля и фильтры people discovery
- `api/requests.py` — activity/direct requests, reward validation, создание чатов
- `api/chat.py` — список чатов, сообщения, изображения, voice placeholders
- `api/moderation.py` — reports, blocks, safety summary, admin queue, analytics
- `api/verification.py` — selfie, voice code, liveness placeholders с временным хранением
- `api/uploads.py` — безопасные uploads для image/audio/avatar
- `realtime/routes.py` — WebSocket chat, typing indicators, WebRTC signaling
- `services/moderation.py` — hook под внешнюю AI moderation API для toxicity/spam/scam/harassment
- `services/email.py` — SMTP sender и HTML email templates от `mail@denchy.cyou`

## Database

SQLite tables:

- `users`
- `profiles`
- `friendships`
- `chats`
- `chat_members`
- `messages`
- `requests`
- `blocks`
- `reports`
- `moderation_logs`
- `trust_scores`
- `verification_states`
- `email_tokens`
- `upload_files`
- `activity_events`

SQLite работает в WAL mode, а Uvicorn запускается одним worker — так проект нормально живёт на VPS с 512 MB RAM.

## Safety

Безопасность встроена в:

- rate limits по IP/user
- JWT token validation
- password hashing через bcrypt
- upload MIME allow-list и лимиты размера
- city/district discovery без realtime GPS
- reports и blocks
- moderation logs и trust-score signals
- local scam/spam heuristics + external AI hooks
- reward rules, которые блокируют dating/adult/paid-companionship payments
- временные verification files с auto-delete windows

## WebRTC

VPS занимается только signaling:

- `webrtc.offer`
- `webrtc.answer`
- `webrtc.ice`

Audio/video идут напрямую между браузерами. STUN включён по умолчанию, TURN вынесен в environment placeholders.
