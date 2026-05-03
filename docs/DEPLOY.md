# Production deployment

The split:

| Piece | Where | URL |
|---|---|---|
| Frontend (Next.js) | Vercel | `https://spieon.agicitizens.com` |
| Backend (FastAPI + Postgres) | Your VPS, behind nginx | `https://api-spieon.agicitizens.com` |
| Bundle storage, narration WS, agent wallet | VPS (same compose stack) | — |

Langfuse and the rest of the dev observability stack are intentionally not part
of the production deploy ([docker-compose.prod.yml](../docker-compose.prod.yml)
ships postgres + backend only).

## 1. DNS

In your DNS provider for `agicitizens.com`:

```
spieon.agicitizens.com        CNAME  cname.vercel-dns.com.
api-spieon.agicitizens.com    A      <your VPS IPv4>
api-spieon.agicitizens.com    AAAA   <your VPS IPv6, if any>
```

Vercel will give you the exact CNAME target when you add the custom domain to
the project — use whatever it says, the value above is only an example.

## 2. VPS one-time setup

Assumes Ubuntu 22.04+ with a non-root sudo user. Adapt apt commands for your
distro.

```bash
# 2.1 Docker + compose plugin
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER" && newgrp docker

# 2.2 nginx + certbot
sudo apt-get update
sudo apt-get install -y nginx python3-certbot-nginx

# 2.3 Repo
sudo mkdir -p /opt/spieon && sudo chown "$USER" /opt/spieon
git clone <this-repo-url> /opt/spieon
cd /opt/spieon
```

## 3. Production env file

Copy [.env.example](../.env.example) to `/opt/spieon/.env` and fill in:

```
APP_ENV=production
CORS_ORIGINS=https://spieon.agicitizens.com

POSTGRES_USER=spieon
POSTGRES_PASSWORD=<strong random password — NOT the dev default>
POSTGRES_DB=spieon

DATABASE_URL=postgresql+asyncpg://spieon:<password>@postgres:5432/spieon
DATABASE_URL_SYNC=postgresql+psycopg://spieon:<password>@postgres:5432/spieon

OPENROUTER_API_KEY=sk-or-v1-…
AGENT_PRIVATE_KEY=<64-hex, NO 0x prefix — fund the address with Base Sepolia ETH>
AGENT_ADDRESS=0x…
EAS_SCHEMA_UID=0x…              # already registered, copy from .env on dev box
KEEPERHUB_API_KEY=kh_…
KEEPERHUB_PAYOUT_WORKFLOW_ID=wf_…
ENS_NAME=spieon-agent.eth
```

`chmod 600 /opt/spieon/.env`. This file holds the agent private key — don't
back it up to anywhere unencrypted.

## 4. Bring up the stack

```bash
cd /opt/spieon
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head

# Optional: seed the demo scans + attestations the DEMO.md video relies on.
# Skip if you only want real scans.
docker compose -f docker-compose.prod.yml exec backend uv run python scripts/seed_demo.py

# Sanity check — backend should be reachable from the host's loopback only.
curl -s http://127.0.0.1:8000/health
# expect: {"status":"ok","db":true}

# From outside the VPS this should NOT respond (firewall + loopback bind):
#   curl http://<vps-ip>:8000/health
```

## 5. nginx + TLS

The vhost references `/etc/letsencrypt/live/api-spieon.agicitizens.com/...` for
its cert paths, so it can't be enabled until the cert exists. Bootstrap order:

```bash
# 5.1 Install nginx if you haven't already, but don't enable our vhost yet.
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 5.2 Stop nginx so port 80 is free for certbot --standalone.
sudo systemctl stop nginx

# 5.3 Get the cert. Replace the email with yours for renewal notices.
sudo certbot certonly --standalone \
    -d api-spieon.agicitizens.com \
    --non-interactive --agree-tos -m you@example.com

# Verify the cert landed:
sudo ls /etc/letsencrypt/live/api-spieon.agicitizens.com/
# expect: cert.pem  chain.pem  fullchain.pem  privkey.pem

# 5.4 Now install the vhost and start nginx.
sudo cp /opt/spieon/deploy/nginx/api-spieon.agicitizens.com.conf \
        /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/api-spieon.agicitizens.com.conf \
            /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl start nginx
```

Auto-renewal runs from the `certbot.timer` systemd unit installed with the
package. `sudo systemctl status certbot.timer` to confirm. Renewal uses the
nginx hook (since the vhost listens on :80 with the acme-challenge passthrough),
so nginx does NOT need to be stopped at renewal time — only the initial cert
acquisition above used `--standalone`.

### Recovery — if you already installed the vhost before getting the cert

If you hit `unknown directive "http2"` or `cannot load certificate` errors when
reloading nginx, you installed the vhost too early. Recover with:

```bash
sudo rm -f /etc/nginx/sites-enabled/api-spieon.agicitizens.com.conf
sudo systemctl stop nginx
sudo certbot certonly --standalone -d api-spieon.agicitizens.com \
    --non-interactive --agree-tos -m you@example.com
cd /opt/spieon && git pull   # pick up any vhost fixes
sudo cp deploy/nginx/api-spieon.agicitizens.com.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/api-spieon.agicitizens.com.conf \
            /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl start nginx
```

Verify from your laptop:

```bash
curl -s https://api-spieon.agicitizens.com/health
# expect: {"status":"ok","db":true}

# WebSocket smoke (use a known scan id from the seeded data, or any UUID — a
# missing one closes with code 4404, which is still a successful upgrade).
curl -i -N \
     -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: $(openssl rand -base64 16)" \
     https://api-spieon.agicitizens.com/ws/scans/00000000-0000-0000-0000-000000000000
# expect: HTTP/1.1 101 Switching Protocols
```

## 6. Vercel (frontend)

1. Import `frontend/` from the Git repo into a new Vercel project. Framework
   preset auto-detects as **Next.js**. Root directory: `frontend`. Build
   command + output: leave defaults.
2. **Environment Variables → Production + Preview**:
   ```
   NEXT_PUBLIC_API_URL = https://api-spieon.agicitizens.com
   NEXT_PUBLIC_WS_URL  = wss://api-spieon.agicitizens.com
   ```
3. **Domains**: add `spieon.agicitizens.com`, follow Vercel's CNAME instructions.
4. Trigger a deploy. The home page server-renders against the backend at
   request time, so a 5xx during build means the API URL is wrong or the
   backend isn't reachable — fix the env var and redeploy.

## 7. Update ENS scan-endpoint record

The agent identity points at the public scan endpoint via the
`org.spieon.scan-endpoint` text record. Re-publish it now that the URL changed:

```bash
docker compose -f docker-compose.prod.yml exec backend \
    uv run python scripts/ens_setup.py \
    --base-url https://api-spieon.agicitizens.com
```

Costs ~0.001 ETH on Sepolia; the agent wallet pays. Confirm:

```bash
curl -s https://api-spieon.agicitizens.com/.well-known/agent.json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ens']['textRecords'])"
# expect: dict including org.spieon.scan-endpoint = https://api-spieon.agicitizens.com
```

## 8. Routine ops

```bash
# Logs
docker compose -f docker-compose.prod.yml logs -f --tail=200 backend

# Restart after pulling new code
cd /opt/spieon && git pull
docker compose -f docker-compose.prod.yml up -d --build backend
docker compose -f docker-compose.prod.yml exec backend uv run alembic upgrade head

# DB shell
docker compose -f docker-compose.prod.yml exec postgres \
    psql -U spieon -d spieon

# Backup the agent's persistent state (Postgres + bundle volume)
docker compose -f docker-compose.prod.yml exec postgres \
    pg_dump -U spieon spieon | gzip > "spieon-$(date +%F).sql.gz"
docker run --rm -v spieon_bundles:/data -v "$PWD":/out alpine \
    tar czf "/out/bundles-$(date +%F).tar.gz" -C /data .
```

## 9. Things this deploy does NOT do

- **Rate limiting / WAF.** Add at the nginx layer (or Cloudflare in front) if
  the public API attracts traffic.
- **Multi-region.** Single-VPS deploy. The Vercel frontend is global but every
  API call still funnels back to one box.
- **Secret rotation.** The agent key + KeeperHub key live in `.env` — rotate by
  hand, restart the backend container.
- **Observability.** Langfuse is dropped; if you want tracing later, point
  `LANGFUSE_HOST` + keys at Langfuse Cloud — no code changes needed.
- **Outbound webhook ingress for KeeperHub.** KH is outbound-only from our side
  (we POST to `/workflow/{id}/execute`); no callback path needs to be opened.
