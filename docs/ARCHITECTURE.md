# MFriends architecture

## Backend modules

- `api/auth.py` — JWT auth, email verification, password reset request
- `api/profiles.py` — profile CRUD and people discovery
- `api/requests.py` — friend/teammate requests and chat creation
- `api/chat.py` — chat list and messages
- `api/moderation.py` — report intake and trust summary
- `api/verification.py` — selfie, voice code and liveness placeholders
- `api/uploads.py` — validated image/audio uploads
- `realtime/routes.py` — WebSocket chat and WebRTC signaling
- `services/moderation.py` — external API moderation hook
- `services/email.py` — SMTP sender and HTML templates

## Database

SQLite tables:

- `users`
- `profiles`
- `chats`
- `chat_members`
- `messages`
- `friendships`
- `requests`
- `reports`
- `moderation_logs`
- `verification_states`
- `trust_scores`
- `email_tokens`
- `upload_files`

## Safety

MFriends is friendship-first, not dating. Safety is built into:

- rate limits per IP/user
- JWT token validation
- password hashing
- upload MIME allow-list
- moderation logs
- scam/spam heuristics
- external AI moderation hooks
- trust-score signals
- report records
- temporary verification files

## WebRTC

The VPS handles only signaling messages:

- `webrtc.offer`
- `webrtc.answer`
- `webrtc.ice`

Audio/video media flows directly between browsers.
