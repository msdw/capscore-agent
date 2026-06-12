# Deploying CAPScore

## Recommended: free single-container hosts

The whole app runs as **one container** — FastAPI serves both the dashboard and
the REST API (`frontend` is same-origin, no nginx needed). The root `Dockerfile`
is all any free Docker host needs; it reads `$PORT` automatically.

The optional Node `cap-provider` (live CROO WebSocket listener) is **not** part of
the single container and is only needed once real CROO credentials exist.

| Host | Free? | URL | Notes |
|---|---|---|---|
| **Render** | Yes (free web service) | `*.onrender.com` | Easiest. `render.yaml` included. Cold start ~50s after idle. |
| **Hugging Face Spaces** | Yes (no card) | `*.hf.space` | Docker Space. Use `deploy/huggingface-space-README.md`. Great for AI demos. |
| **Google Cloud Run** | Yes (free tier) | `*.run.app` | Scales to zero, fast. Needs gcloud + a billing-enabled project. |
| **Koyeb** | Yes (free instance) | `*.koyeb.app` | Docker-native. |

### Render (quickest)

1. Push this repo to GitHub (also required for the hackathon submission).
2. Render → **New → Blueprint** → pick the repo (it reads `render.yaml`).
3. Set secrets `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY`.
4. Deploy → live at `https://capscore-agent.onrender.com`.
5. Set `CAPSCORE_PUBLIC_BASE_URL` to that URL and redeploy.

### Local single-container test

```bash
docker build -t capscore .
docker run --rm -p 8000:8000 --env-file .env capscore
# open http://localhost:8000
```

---

## Self-hosting behind a custom domain (Cloudflare Tunnel)

> Original notes for serving under a custom domain via a Cloudflare Tunnel.

The stack runs three containers (`api`, `frontend`, `cloudflared`) and is fronted
by a **Cloudflare Tunnel**, so no inbound ports need to be opened on the host.
`nginx` (the `frontend` container) serves the dashboard and reverse-proxies the
`/health` and `/jobs` API surface to the `api` container, so the whole app is
served same-origin under `https://croo.maaihub.com`.

```
Internet ──TLS──> Cloudflare ──tunnel──> cloudflared ──> frontend (nginx :80)
                                                            ├─ /            -> static dashboard
                                                            └─ /health,/jobs -> api (:8000)
```

## Prerequisites

- Docker + Docker Compose on the host.
- `.env` filled in (copy from `.env.example`). For the analysis layer you need
  at least `ANTHROPIC_API_KEY` **or** `OPENAI_API_KEY` (the LLM helper falls back
  Anthropic → OpenAI → deterministic heuristics).
- A Cloudflare Tunnel **run token** in `TUNNEL_TOKEN`.

## One-time Cloudflare setup (dashboard, ~3 min)

The API token in this project can read DNS but **cannot create tunnels**, so the
tunnel is created once in the dashboard:

1. Cloudflare **Zero Trust → Networks → Tunnels → Create a tunnel**.
2. Type: **Cloudflared**. Name it e.g. `croo-capscore`. Save.
3. Under **Public Hostnames**, add:
   - Subdomain `croo`, Domain `maaihub.com`
   - Service: **HTTP** → `frontend:80`
4. Copy the **tunnel token** (the long `eyJ...` string from the "install connector"
   command) into `.env` as `TUNNEL_TOKEN=...`.

Cloudflare automatically creates the `croo.maaihub.com` CNAME to the tunnel.
(The existing `*.maaihub.com` wildcard no longer matters once this explicit
record exists.)

## Deploy

```bash
cd capscore-agent
cp .env.example .env   # then fill in keys + TUNNEL_TOKEN
./deploy/deploy.sh
```

Verify:

```bash
curl https://croo.maaihub.com/health
# {"status":"ok","version":"0.1.0",...}
```

Open `https://croo.maaihub.com` for the dashboard.

## Enabling the live CROO CAP provider (later)

Until real CROO credentials exist, the `cap-provider` container is **not** started
(the API, analysis engine, proof packs, and dashboard all work without it). Once
you create the agent on cap.croo.network:

1. Set `CROO_SDK_KEY`, `CAPSCORE_AGENT_ID`, `WALLET_PRIVATE_KEY` in `.env`.
2. `docker compose -f docker-compose.prod.yml up -d --build cap-provider`

## Alternative: deploy on the existing maaihub box over SSH

If you prefer the existing origin server (the host behind `*.maaihub.com`):

```bash
# on your machine
rsync -az --exclude .venv --exclude node_modules --exclude runs \
  capscore-agent/ user@maaihub-host:/opt/capscore-agent/
ssh user@maaihub-host 'cd /opt/capscore-agent && ./deploy/deploy.sh'
```

The Cloudflare Tunnel approach is recommended either way — it avoids opening
ports and works identically on any Docker host.
