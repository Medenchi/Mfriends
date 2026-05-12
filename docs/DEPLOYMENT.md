# Деплой MFriends

## DNS

Создай wildcard DNS для `*.denchy.cyou`, который смотрит на IP VPS. Нужные hostnames:

- `mfriends.denchy.cyou`
- `api.denchy.cyou`
- `ws.denchy.cyou`
- `cdn.denchy.cyou`
- `mail.denchy.cyou`
- `dev.denchy.cyou`

## Установка на VPS

```bash
git clone https://github.com/Medenchi/Mfriends.git
cd Mfriends
sudo bash deploy/scripts/install-vps.sh "$PWD"
sudo nano /opt/mfriends/.env
```

В `/opt/mfriends/.env` обязательно задай:

- `SECRET_KEY` — длинный случайный секрет
- `DATABASE_PATH=/opt/mfriends/data/mfriends.sqlite3`
- `UPLOAD_DIR=/opt/mfriends/uploads`
- SMTP credentials для `mail@denchy.cyou`
- опционально переменные внешней moderation API
- опционально TURN credentials от TURN-провайдера

## Инициализация базы

```bash
sudo -u mfriends /opt/mfriends/venv/bin/python -m backend.app.db.init_db
```

## Запуск backend

```bash
sudo systemctl enable --now mfriends-api
sudo systemctl status mfriends-api
```

## SSL

Когда wildcard DNS уже смотрит на VPS:

```bash
sudo certbot --nginx   -d denchy.cyou   -d '*.denchy.cyou'   --manual --preferred-challenges dns
sudo systemctl reload nginx
```

Если wildcard-сертификат через DNS-01 неудобен, можно выпустить отдельные HTTP-сертификаты:

```bash
sudo certbot --nginx   -d mfriends.denchy.cyou   -d api.denchy.cyou   -d ws.denchy.cyou   -d cdn.denchy.cyou   -d dev.denchy.cyou
```

## WebSocket

`ws.denchy.cyou/ws` проксируется в тот же FastAPI-процесс. В Nginx включены `Upgrade`/`Connection` headers и длинные read/send timeouts.

## WebRTC

По умолчанию используется STUN:

```js
stun:stun.l.google.com:19302
```

Для стабильного продакшена добавь TURN credentials от Coturn, Twilio, Metered или Cloudflare Calls. Не передавай видео через FastAPI VPS — медиа должно идти P2P.

## Полезные команды

```bash
sudo journalctl -u mfriends-api -f
sudo nginx -t
curl -fsS https://api.denchy.cyou/api/health
```

## Структура на сервере

```text
/opt/mfriends
├── app/backend
├── frontend
├── data/mfriends.sqlite3
├── uploads
├── logs
└── scripts
```
