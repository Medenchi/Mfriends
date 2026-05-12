# Настройка VPS на 512 MB RAM

## Рекомендуемый сервер

- Ubuntu 22.04 или 24.04
- минимум 512 MB RAM
- 1 vCPU
- 8 GB disk
- включённый swap

## Swap

На маленьком VPS обязательно добавь swap:

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## DNS

Создай wildcard DNS-запись:

```text
*.denchy.cyou A <VPS-IP>
denchy.cyou A <VPS-IP>
```

Nginx будет роутить поддомены так:

- `mfriends.denchy.cyou` → frontend
- `api.denchy.cyou` → FastAPI
- `ws.denchy.cyou` → WebSockets/WebRTC signaling
- `cdn.denchy.cyou` → uploads/static
- `mail.denchy.cyou` → email services
- `dev.denchy.cyou` → закрытая dev-среда

## Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Почему это нормально для 512 MB RAM

- один Uvicorn worker
- SQLite в WAL mode
- frontend отдаёт Nginx как статику
- WebRTC media идёт P2P, не через VPS
- локальные AI-модели не запускаются
- лимит uploads по умолчанию 5 MB
- без React/Next.js/Kubernetes/microservices

## Email

Нужно настроить SMTP так, чтобы `mail@denchy.cyou` мог отправлять письма. SMTP-логин/пароль храни только в `/opt/mfriends/.env`.

## Dev host

`dev.denchy.cyou` закрывается через Nginx basic auth. Перед включением конфига создай пароль:

```bash
sudo apt-get install -y apache2-utils
sudo htpasswd -c /etc/nginx/.mfriends-dev.htpasswd devin
```
