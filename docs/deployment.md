# Pixora — Deployment Guide

Two supported deployment paths:

- **Path A** — Local machine + Cloudflare Tunnel (recommended for demos)
- **Path B** — VPS (Hetzner, DigitalOcean, Linode)

Both use the same Docker Compose stack. TLS is handled by Cloudflare in
Path A and by Caddy in Path B.

---

## Prerequisites

- Linux host (WSL2, Ubuntu VM, or VPS) with Docker + Docker Compose v2
- git, make, curl
- ~4 GB RAM, 20 GB disk, 2 vCPU minimum
- Optional: Cloudflare account (for Path A), domain (for Path A+ / B)

---

## Path A — Local + Cloudflare quick tunnel

Fastest path to a public HTTPS URL.

### 1. Clone and configure

    git clone git@github.com:AnuskaDey07/Pixora.git
    cd Pixora

    make gen-secrets > .env.prod
    cp .env.prod .env

### 2. Start in production mode

    make prod-up

Wait until healthy:

    docker compose ps

### 3. Apply migrations

    docker compose exec api flask db upgrade

### 4. Create an admin user

    docker compose exec api python scripts/create_admin.py you@example.com --create --password 'strong-password'

### 5. Install cloudflared

    curl -L --output /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    sudo dpkg -i /tmp/cloudflared.deb
    cloudflared --version

### 6. Start the quick tunnel

    cloudflared tunnel --url http://localhost:80

Copy the printed `*.trycloudflare.com` URL and open it. That URL serves
Pixora over HTTPS.

The URL changes on every restart of cloudflared. For a persistent URL,
see Path A+ below.

---

## Path A+ — Named tunnel (persistent URL)

Requires a domain pointed at Cloudflare. Steps are in
[cloudflare-tunnel.md](cloudflare-tunnel.md).

Once set up, edit `.env`:

    MINIO_PUBLIC_ENDPOINT=pixora.yourdomain.com

Then restart:

    make prod-down && make prod-up

---

## Path B — VPS deployment

### 1. Prepare the host

    sudo apt update && sudo apt upgrade -y
    sudo apt install -y docker.io docker-compose-v2 git make curl

    sudo usermod -aG docker $USER
    # log out and back in for group changes

### 2. Clone and configure

    sudo mkdir -p /opt/pixora && sudo chown $USER /opt/pixora
    git clone git@github.com:AnuskaDey07/Pixora.git /opt/pixora
    cd /opt/pixora

    make gen-secrets > .env.prod
    cp .env.prod .env

Edit `.env`, set `MINIO_PUBLIC_ENDPOINT` to your public domain.

### 3. Firewall

    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw enable

### 4. Start the stack

    make prod-up
    docker compose exec api flask db upgrade
    docker compose exec api python scripts/create_admin.py you@example.com --create --password 'strong-password'

### 5. TLS with Caddy

    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    sudo apt update && sudo apt install -y caddy

Create `/etc/caddy/Caddyfile`:

    pixora.example.com {
        reverse_proxy localhost:80
    }

Reload:

    sudo systemctl reload caddy

Caddy provisions a Let's Encrypt certificate automatically.

### 6. Auto-start on boot

In root's crontab (`sudo crontab -e`):

    @reboot cd /opt/pixora && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

---

## Backups

Create:

    ./scripts/backup.sh /var/backups/pixora

Restore:

    ./scripts/restore.sh /var/backups/pixora/pixora-backup-YYYYMMDD-HHMMSS.tar.gz

Daily backups in root's crontab:

    0 3 * * * cd /opt/pixora && ./scripts/backup.sh /var/backups/pixora >> /var/log/pixora-backup.log 2>&1

---

## Commands

    make prod-up              # start (production mode)
    make prod-down            # stop
    docker compose ps         # status
    docker compose logs -f    # tail logs
    docker compose exec api flask db upgrade
    curl http://localhost/api/health

---

## Troubleshooting

**Thumbnails broken over a tunnel** — `MINIO_PUBLIC_ENDPOINT` must be
reachable from the browser. Set it to your public domain.

**502 from the tunnel** — API not yet healthy. Wait 20 seconds, refresh.

**Data disappeared** — you ran `make reset`. Restore from backup.

**Celery jobs stuck in pending** — check `docker compose logs worker-light`
and `docker compose logs worker-ml`.

**MinIO console 404 in prod** — by design. In production, ports 9000
and 9001 are not exposed. Use dev mode to access the console.
