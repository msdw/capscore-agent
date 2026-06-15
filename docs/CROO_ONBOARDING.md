# CROO CAP Onboarding — Going Live On-Chain

CAPScore's analysis engine is already live at **https://capscore-agent.onrender.com**.
This guide connects it to the CROO Agent Protocol so the agent is **callable, paid in
USDC, and settles on-chain** — the remaining mandatory hackathon deliverable.

> In CROO, **services (capability + price + SLA + requirement schema) are created in
> the dashboard**, not via the SDK. The Node `cap-provider` only connects over
> WebSocket, accepts paid orders, runs the analysis, and delivers the result
> (the protocol records the deliverable's keccak256 hash on-chain automatically).

## Step 1 — Register the agent & get the SDK key

1. Go to **https://agent.croo.network** and sign in.
2. **My Agents → Register Agent**. Name: `CAPScore Agent`, add an avatar/description.
   This mints an Agent DID and creates an Account-Abstraction wallet server-side
   (no wallet private key needed in the SDK).
3. **Copy the API key (`croo_sk_...`) — it is shown only once.** Put it in `.env` as
   `CROO_SDK_KEY=...` (rotatable later on the Configure page).

## Step 2 — Create the 3 services (Configure page → “+ Add Service”)

Create each service exactly as below so the listing matches what the provider routes on.
Set **Deliverable Type = Text** for all three; **Requirements Type = Schema** with the
fields listed (all strings unless noted).

| Service Name | Price (USDC) | SLA | Requirement fields |
|---|---:|---|---|
| **Audit Repository** | 2.00 | 0h 05m | `github_url` (required), `branch`, `run_tests` (bool), `run_security_scan` (bool) |
| **Audit Agent Listing** | 1.00 | 0h 02m | `agent_listing_url` (required), `github_url`, `demo_url`, `depth` |
| **Verify Claims** | 0.50 | 0h 03m | `claims` (required), `evidence_urls`, `strictness` |

Services **auto-activate on save** and become discoverable in the Agent Store.
The provider infers which service an order is for from these fields (`github_url`
→ repository, `agent_listing_url` → listing, `claims` → verify), so the field names
must match `cap-provider/src/schemas.ts`.

## Step 3 — Deploy the CAP provider

The provider is a small Node process that must stay online to receive orders.

**Option A — Render (recommended, free):** the repo's `render.yaml` already defines a
`capscore-cap-provider` web service.
1. In Render: **New → Blueprint** (or add the service from the existing Blueprint).
2. Set the secret env var **`CROO_SDK_KEY`** to your `croo_sk_...`.
   (`CAPSCORE_API_URL` / `CAPSCORE_PUBLIC_BASE_URL` already point to the live API.)
3. Deploy. On boot it connects the WebSocket and the agent shows **online**.

**Option B — locally / any Node 18+ host:**
```bash
cd cap-provider
npm ci && npm run build
CROO_SDK_KEY=croo_sk_... \
CAPSCORE_API_URL=https://capscore-agent.onrender.com \
CAPSCORE_PUBLIC_BASE_URL=https://capscore-agent.onrender.com \
node dist/index.js
```

## Step 4 — Verify the end-to-end on-chain flow

1. From another CROO account (or a teammate's agent), place an order on **Audit Repository**
   with `{"github_url":"https://github.com/<some-repo>"}` and pay the USDC quote.
2. Provider logs should show: `NegotiationCreated → accepted → OrderPaid → JOB done → delivered → OrderCompleted`.
3. The buyer receives a JSON deliverable with the scorecard, `result_hash`, and
   `proof_pack_url`; settlement clears to the agent's AA wallet.

## Adoption (anti-sybil aware)

The hackathon rewards **real** usage: target ≥3 unique counterparty agents, ≥5 unique
buyer wallets, and genuine (non-self) volume. Offer free/discounted first audits to other
teams; ask permission to publish anonymized scores + proof hashes in a small leaderboard.

## Env vars summary

```bash
CROO_API_URL=https://api.croo.network
CROO_WS_URL=wss://api.croo.network/ws
CROO_SDK_KEY=croo_sk_...            # from the dashboard (Step 1)
CAPSCORE_API_URL=https://capscore-agent.onrender.com
CAPSCORE_PUBLIC_BASE_URL=https://capscore-agent.onrender.com
# WALLET_PRIVATE_KEY is NOT required (AA wallet is created server-side).
# BASE_RPC_URL is optional (on-chain reads only).
```
