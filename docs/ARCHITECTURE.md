# MFriends architecture

MFriends is a friendship-first fullstack platform for finding friends, teammates, study/coding buddies and safe online/offline activities. It is explicitly not a dating app.

## Domain architecture

Wildcard DNS should point `*.denchy.cyou` to the VPS. Nginx routes by virtual host:

- `mfriends.denchy.cyou` → static HTML/CSS/vanilla JS frontend
- `api.denchy.cyou` → FastAPI REST API
- `ws.denchy.cyou` → WebSocket chat and WebRTC signaling
- `cdn.denchy.cyou` → uploads/static files
- `mail.denchy.cyou` → SMTP/IMAP service endpoint for `mail@denchy.cyou`
- `dev.denchy.cyou` → protected development environment

## Backend modules

- `api/auth.py` — JWT auth, refresh tokens, email verification, password reset and cooldowns
- `api/profiles.py` — profile CRUD and people discovery filters
- `api/requests.py` — activity requests, direct requests, reward validation and chat creation
- `api/chat.py` — chat list, messages, image attachments and voice placeholders
- `api/moderation.py` — reports, blocks, safety summary, admin queue and analytics
- `api/verification.py` — selfie, voice code and liveness placeholders with temporary storage
- `api/uploads.py` — secure image/audio/avatar uploads
- `realtime/routes.py` — WebSocket chat, typing indicators and WebRTC signaling
- `services/moderation.py` — external AI moderation hook for toxicity/spam/scam/harassment
- `services/email.py` — SMTP sender and HTML email templates from `mail@denchy.cyou`

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

SQLite runs with WAL mode and one Uvicorn worker for 512 MB VPS compatibility.

## Safety

Safety is built into:

- rate limits per IP/user
- JWT token validation
- password hashing with bcrypt
- upload MIME allow-list and upload size limits
- city/district discovery without realtime GPS
- report and block records
- moderation logs and trust-score signals
- scam/spam local heuristics plus external AI hooks
- reward rules blocking dating/adult/paid-companionship payments
- temporary verification files with auto-delete windows

## WebRTC

The VPS handles signaling only:

- `webrtc.offer`
- `webrtc.answer`
- `webrtc.ice`

Audio/video media flows directly between browsers. STUN is enabled by default and TURN config is represented by environment placeholders.
