# VPS setup for 512 MB RAM

## Recommended server

- Ubuntu 22.04 or 24.04
- 512 MB RAM minimum
- 1 vCPU
- 8 GB disk
- swap enabled

## Swap

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## DNS architecture

Create a wildcard DNS record:

```text
*.denchy.cyou A <VPS-IP>
denchy.cyou A <VPS-IP>
```

Subdomains are routed by Nginx virtual hosts:

- `mfriends.denchy.cyou` frontend
- `api.denchy.cyou` FastAPI
- `ws.denchy.cyou` WebSockets/WebRTC signaling
- `cdn.denchy.cyou` uploads/static
- `mail.denchy.cyou` email services
- `dev.denchy.cyou` protected development environment

## Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Low-RAM choices

- one Uvicorn worker
- SQLite WAL mode
- static frontend served by Nginx
- WebRTC media stays peer-to-peer
- no local AI models
- upload limit defaults to 5 MB
- no React/Next.js/Kubernetes/microservices

## Email

Configure your mail provider or local mail stack so `mail@denchy.cyou` can send SMTP mail. Store SMTP credentials in `/opt/mfriends/.env` only.

## Dev host

`dev.denchy.cyou` is protected with Nginx basic auth. Create the password file before enabling the config:

```bash
sudo apt-get install -y apache2-utils
sudo htpasswd -c /etc/nginx/.mfriends-dev.htpasswd devin
```
