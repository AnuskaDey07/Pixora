# Cloudflare Tunnel — Setup

Cloudflare Tunnel creates an outbound encrypted connection from your
machine to Cloudflare's edge. Public HTTPS requests hit Cloudflare,
travel down the tunnel, and arrive at `http://localhost:80`.

No router config, no static IP, no port forwarding.

Two flavors:

- **Quick tunnel** — random URL, no account needed, changes on restart.
- **Named tunnel** — persistent URL, requires a domain + Cloudflare account.

---

## Install cloudflared (WSL2 / Ubuntu)

    curl -L --output /tmp/cloudflared.deb \
      https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

    sudo dpkg -i /tmp/cloudflared.deb
    sudo apt-get install -f   # in case dpkg reports missing deps

    cloudflared --version

---

## Quick tunnel

Make sure Pixora is running (`make up` or `make prod-up`), then:

    cloudflared tunnel --url http://localhost:80

Copy the printed `*.trycloudflare.com` URL. It serves Pixora over HTTPS.

**Limitations**

- URL changes on every restart.
- Thumbnails and job results use presigned MinIO URLs pointing at
  `localhost:9000`, which only work when the browser is on the same
  machine as the stack. From another device, images fail to load.
  This is expected — quick tunnels are for testing, not for demos
  from other networks.

Stop with `Ctrl+C`.

---

## Named tunnel (persistent URL)

Requires:

- A domain (any registrar)
- A free Cloudflare account
- Domain's nameservers pointed at Cloudflare

### 1. Point the domain at Cloudflare

Change nameservers at your registrar to the two Cloudflare provided.
Wait for propagation (usually minutes). Verify in Cloudflare's
dashboard that the zone shows as **Active**.

### 2. Create the tunnel

Cloudflare Zero Trust dashboard → Networks → Tunnels → Create a tunnel.

- Name: `pixora-local`
- Type: Cloudflared
- Copy the token shown.

### 3. Public hostname

Add a public hostname mapping:

- Subdomain: `pixora`
- Domain: `yourdomain.com`
- Service: `http://localhost:80`

### 4. Install as a service on the host

    sudo cloudflared service install <TUNNEL_TOKEN>
    sudo systemctl status cloudflared

### 5. Tell the app its public URL

Edit `.env`:

    MINIO_PUBLIC_ENDPOINT=pixora.yourdomain.com

Restart:

    make prod-down && make prod-up

Now `https://pixora.yourdomain.com` serves Pixora with:
- Automatic TLS
- DDoS protection
- A stable URL that survives reboots
- Working thumbnails for any browser worldwide
