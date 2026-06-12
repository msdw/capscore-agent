#!/usr/bin/env bash
# CAPScore production deploy — brings up the stack behind a Cloudflare Tunnel.
#
# Prerequisites on the host:
#   - Docker + Docker Compose
#   - .env present (copy from .env.example, fill in keys)
#   - TUNNEL_TOKEN set in the environment or .env (Cloudflare Zero Trust tunnel
#     run token, with public hostname croo.maaihub.com -> http://frontend:80)
#
# Usage:
#   TUNNEL_TOKEN=eyJ... ./deploy/deploy.sh
#
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "ERROR: .env not found. Copy .env.example to .env and fill in keys." >&2
  exit 1
fi

# Load TUNNEL_TOKEN from .env if not already in the environment.
if [ -z "${TUNNEL_TOKEN:-}" ] && grep -q '^TUNNEL_TOKEN=' .env; then
  export TUNNEL_TOKEN="$(grep '^TUNNEL_TOKEN=' .env | head -1 | cut -d= -f2-)"
fi

if [ -z "${TUNNEL_TOKEN:-}" ]; then
  echo "ERROR: TUNNEL_TOKEN is not set (env or .env)." >&2
  echo "Create a tunnel in Cloudflare Zero Trust > Networks > Tunnels," >&2
  echo "set public hostname croo.maaihub.com -> HTTP -> frontend:80, copy the token." >&2
  exit 1
fi

echo "[deploy] Building images..."
docker compose -f docker-compose.prod.yml build api frontend

echo "[deploy] Starting api + frontend + cloudflared..."
# cap-provider is started only when real CROO_SDK_KEY is configured.
if grep -q '^CROO_SDK_KEY=croo_sk_[A-Za-z0-9]' .env && ! grep -q '^CROO_SDK_KEY=croo_sk_your_key_here' .env; then
  docker compose -f docker-compose.prod.yml up -d --build
  echo "[deploy] Live CROO provider enabled."
else
  docker compose -f docker-compose.prod.yml up -d api frontend cloudflared
  echo "[deploy] CROO provider NOT started (placeholder CROO_SDK_KEY). API + frontend live."
fi

echo "[deploy] Waiting for API health..."
for i in $(seq 1 20); do
  if docker compose -f docker-compose.prod.yml exec -T api curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "[deploy] API healthy."; break
  fi
  sleep 3
done

echo "[deploy] Done. Verify: https://croo.maaihub.com/health"
