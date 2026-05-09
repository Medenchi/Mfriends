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

1. Create DuckDNS domain: `malinacode.duckdns.org`.
2. Add CNAME in `is-a.dev` config:

```json
{
  "owner": {
    "username": "Medenchi",
    "email": "atem4513@gmail.com"
  },
  "record": {
    "CNAME": "malinacode.duckdns.org"
  }
}
```

3. Set `/opt/mfriends/.env`:

```bash
DUCKDNS_DOMAIN=malinacode
DUCKDNS_TOKEN=your-duckdns-token
```

4. Enable updater:

```bash
sudo systemctl enable --now duckdns-mfriends.timer
```

The timer runs every 5 minutes, retries failed updates and logs to `/opt/mfriends/logs/duckdns.log`.

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
