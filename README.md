# CAPScore Agent

[![CI](https://github.com/CROO-Network/capscore-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/CROO-Network/capscore-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CROO Hackathon 2026](https://img.shields.io/badge/CROO-Hackathon%202026-6e40c9)](https://dorahacks.io/hackathon/croo-hackathon)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178c6.svg)](https://www.typescriptlang.org/)

> **Verifiable due diligence for the agent economy.** CAPScore audits any AI agent, GitHub repo, or CROO Agent Store listing and returns a verifiable proof pack: reproducibility score, CAP integration score, source-backed claims verification, security risks, README fixes, and a demo-day improvement plan.

**[Demo Video](#) · [Agent Store Listing](#) · [DoraHacks BUIDL](#)**

---

## 1. What is CAPScore?

CAPScore is an AI-powered auditing agent built for the CROO Agent Economy. It accepts structured audit orders via the **Commerce Agent Protocol (CAP)** and produces a tamper-evident **proof pack** — a ZIP file containing a scorecard, evidence log, SHA-256 hash chain, and AI attestation.

Three capabilities are available on the CROO Agent Store:

| Capability | Description | Price |
|---|---|---|
| `audit_repository` | Deep audit of any GitHub repo: reproducibility, CAP integration, security, readme quality | 0.05 CROO |
| `audit_agent_listing` | Full audit of an Agent Store submission against CROO judging criteria | 0.08 CROO |
| `verify_claims` | Verifies specific claims against provided evidence URLs | 0.02 CROO |

Any agent can call CAPScore programmatically via the CROO SDK — no API keys required, just a CAP order.

---

## 2. Why It Matters for CROO/CAP

The agent economy has a **trust gap**: any developer can submit an agent to the CROO Agent Store and make bold claims about functionality, reliability, and integration quality. Buyers — whether human or AI — have no independent way to verify those claims before purchasing.

CAPScore closes this gap. By accepting a CAP order, running a multi-worker audit pipeline, and returning a cryptographically-hashed proof pack, CAPScore gives the ecosystem a **verifiable due-diligence layer**. Judges evaluating hackathon submissions, buyers assessing agents in production, and developers wanting honest feedback can all use CAPScore as a neutral third party.

This is not just a useful tool — it is **infrastructure for the agent economy itself**: a composable verification primitive that any other agent can call in a single line of code.

---

## 3. Demo

> **Live demo:** [https://capscore.croo.network](https://capscore.croo.network) *(placeholder — update before submission)*

**Demo video:** [YouTube / Loom link](#) *(5-minute walkthrough — link before submission)*

**Screenshot:**

```
┌─────────────────────────────────────────────────────┐
│  CAPScore Agent                     [CROO Hackathon] │
│  Verifiable Due Diligence for the Agent Economy      │
├──────────────────────────────────────────────────────┤
│  [Audit Repository] [Audit Agent] [Verify Claims]    │
│                                                      │
│  GitHub URL: https://github.com/team/my-agent        │
│  Run Tests: ☑   Security Scan: ☑                    │
│                                                      │
│  [Submit Audit]                                      │
│                                                      │
│  ● Overall Score: 84/100                             │
│  ████████████████████░░░  Technical Execution  85    │
│  █████████████████░░░░░░  A2A Composability   85    │
│  ████████████████░░░░░░░  Innovation          80    │
│  █████████████████░░░░░░  Adoption Readiness  83    │
│  ████████████████░░░░░░░  Presentation        80    │
└──────────────────────────────────────────────────────┘
```

---

## 4. Agent Store Listing

CAPScore is registered on the CROO Agent Store with three capabilities:

### `audit_repository`
- **Input:** `github_url` (required), `branch`, `run_tests`, `run_security_scan`
- **Output:** Full scorecard + proof pack ZIP
- **Price:** 0.05 CROO per audit
- **SLA:** 5 minutes max / 99% uptime

### `audit_agent_listing`
- **Input:** `agent_listing_url` (required), `github_url`, `demo_url`, `claimed_tracks`, `depth`
- **Output:** Hackathon-aligned scorecard + proof pack ZIP
- **Price:** 0.08 CROO per audit
- **SLA:** 8 minutes max

### `verify_claims`
- **Input:** `claims` (required list), `evidence_urls`, `strictness`
- **Output:** Per-claim verification table + proof pack ZIP
- **Price:** 0.02 CROO per verification
- **SLA:** 2 minutes max

---

## 5. Quickstart

```bash
# 1. Clone
git clone https://github.com/CROO-Network/capscore-agent.git
cd capscore-agent

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your keys
#    Required: CROO_SDK_KEY, ANTHROPIC_API_KEY
#    Optional: CAPSCORE_PUBLIC_BASE_URL (for shareable proof URLs)
nano .env

# 4. Start the full stack
docker compose up --build

# 5. Test
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0","jobs_in_memory":0}
```

Open the frontend at [http://localhost:8080](http://localhost:8080).

---

## 6. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `CROO_SDK_KEY` | Yes | — | CROO SDK API key for registering capabilities |
| `CROO_API_URL` | No | `https://api.croo.network` | CROO API base URL |
| `CROO_WS_URL` | No | `wss://api.croo.network/ws` | CROO WebSocket URL for order streaming |
| `CAPSCORE_AGENT_ID` | No | — | Your registered agent ID on CROO |
| `WALLET_PRIVATE_KEY` | No | — | Wallet key for CROO payment receipts |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key for AI workers |
| `CAPSCORE_API_URL` | No | `http://localhost:8000` | Internal API URL (used by cap-provider) |
| `CAPSCORE_PUBLIC_BASE_URL` | No | `http://localhost:8000` | Public URL for proof pack download links |
| `MAX_JOB_SECONDS` | No | `300` | Job timeout in seconds |
| `MAX_REPO_MB` | No | `250` | Max repository size in MB |
| `ALLOW_NETWORK_REPRO` | No | `false` | Allow network access during repo reproduction |
| `LOG_LEVEL` | No | `info` | Logging level (`debug`, `info`, `warning`, `error`) |

---

## 7. Run Locally with Docker Compose

```bash
docker compose up --build
```

Services started:
- **`api`** — FastAPI backend on port 8000
- **`cap-provider`** — TypeScript CAP provider connecting to CROO network
- **`frontend`** — Static nginx frontend on port 8080

Proof packs are persisted to `./runs/{job_id}/` on the host.

### Without Docker

```bash
# API
cd api
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# CAP Provider (separate terminal)
cd cap-provider
npm install
npm run dev
```

---

## 8. Run Tests

```bash
# Python tests (from api/)
cd api
pip install -e ".[dev]"
pytest ../tests/ -v

# Type checking
mypy app/ --ignore-missing-imports

# TypeScript type check
cd cap-provider
npm run typecheck
```

### Test Coverage

| Module | Tests |
|---|---|
| `test_scoring.py` | 12 tests — scoring engine, weighted formula, edge cases |
| `test_proof_pack.py` | 16 tests — ZIP structure, hash determinism, attestation |
| `test_schemas.py` | 20 tests — CAP schemas + API integration |

---

## 9. Example CAP Orders

### Audit a Repository

```bash
curl -s -X POST http://localhost:8000/jobs/audit-repository \
  -H "Content-Type: application/json" \
  -d '{
    "github_url": "https://github.com/CROO-Network/capscore-agent",
    "run_tests": true,
    "run_security_scan": true
  }' | jq .job_id
```

### Audit an Agent Listing

```bash
curl -s -X POST http://localhost:8000/jobs/audit-agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_listing_url": "https://agent.croo.network/my-agent",
    "github_url": "https://github.com/my-team/my-agent",
    "claimed_tracks": ["Data & Verification Agents"],
    "depth": "standard"
  }' | jq .job_id
```

### Verify Claims

```bash
curl -s -X POST http://localhost:8000/jobs/verify-claims \
  -H "Content-Type: application/json" \
  -d '{
    "claims": [
      "This agent provides a working CAP provider.",
      "Docker Compose starts the stack with one command."
    ],
    "evidence_urls": ["https://github.com/my-team/my-agent"],
    "strictness": "standard"
  }' | jq .job_id
```

### Poll for Result

```bash
JOB_ID="capscore_20260612_100000_abc12345"

# Poll until done
while true; do
  STATUS=$(curl -s http://localhost:8000/jobs/$JOB_ID | jq -r .status)
  echo "Status: $STATUS"
  [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ] && break
  sleep 2
done

# Get result
curl -s http://localhost:8000/jobs/$JOB_ID | jq .scorecard.overall_score

# Download proof pack
curl -O http://localhost:8000/jobs/$JOB_ID/proof-pack.zip
```

### Via CROO SDK (A2A)

```typescript
import { CROOClient } from "@croo/agent-sdk";

const client = new CROOClient({ apiKey: process.env.CROO_SDK_KEY });

const result = await client.placeOrder({
  agentId: "capscore-agent",
  capability: "audit_repository",
  input: {
    github_url: "https://github.com/my-team/my-agent",
    run_tests: true,
  },
});

console.log("Score:", result.scorecard.overall_score);
console.log("Proof hash:", result.result_hash);
```

---

## 10. Example Result

```
# CAPScore Report — Job capscore_20260612_100000_abc12345

Overall Score: 84/100

## Scorecard

| Dimension            | Weight | Score  |
|----------------------|--------|--------|
| Technical Execution  | 30%    | 85/100 |
| A2A Composability    | 25%    | 85/100 |
| Innovation           | 20%    | 80/100 |
| Adoption Readiness   | 15%    | 83/100 |
| Presentation Ready   | 10%    | 80/100 |

## Critical Issues
1. No Agent Store listing URL provided
2. Failure behavior not documented

## Top Fixes
1. Register on agent.croo.network
2. Add failure_modes to CAP schema

Result hash: sha256:e3b0c44...
```

See [examples/sample_result.md](examples/sample_result.md) for the full report.

---

## 11. Proof Pack Format

Every completed job produces a `proof-pack-{job_id}.zip`:

```
proof-pack-capscore_20260612_100000_abc12345.zip
├── manifest.json          # Job metadata, file inventory, A2A call log, limits
├── result.json            # Full scorecard in canonical JSON (sorted keys)
├── result.md              # Human-readable Markdown report
├── result_hash.sha256     # sha256:<hex> of canonical result.json
├── execution_log.jsonl    # Timestamped worker events (one JSON per line)
├── attestation.json       # CAPScore Agent statement + execution log hash
└── evidence/
    └── sources.json       # Repo file inventory, security findings, raw worker data
```

### Verify a Proof Pack

```bash
unzip proof-pack-capscore_20260612_100000_abc12345.zip
EXPECTED=$(cat result_hash.sha256)
COMPUTED="sha256:$(python3 -c "
import json, hashlib
data = json.load(open('result.json'))
canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',',':'))
print(hashlib.sha256(canonical.encode()).hexdigest())
")"
[ "$EXPECTED" = "$COMPUTED" ] && echo "VERIFIED OK" || echo "HASH MISMATCH"
```

---

## 12. A2A Composability

CAPScore itself calls three sub-agents during an audit, demonstrating genuine A2A composability:

```
Buyer Agent
    │
    │  CAP Order: audit_repository
    ▼
CAPScore Agent (this repo)
    │
    ├──► source-verifier-mock    (verify GitHub source exists)
    │         └── result_hash: sha256:abc...
    │
    ├──► security-scanner-mock  (scan for secrets / CVEs)
    │         └── result_hash: sha256:def...
    │
    └──► readme-rewriter-mock   (AI README improvement suggestions)
              └── result_hash: sha256:ghi...
    │
    ▼
Proof Pack (ZIP with SHA-256 hash chain)
    │
    ▼
Buyer Agent receives: scorecard + result_hash + proof_pack_url
```

Every A2A call is logged in `manifest.json` with its own `result_hash`, creating an **auditable chain of provenance**.

### Calling CAPScore from Another Agent

```typescript
// Any CROO agent can call CAPScore in one line:
const audit = await crooClient.placeOrder({
  agentId: "capscore-agent",
  capability: "verify_claims",
  input: { claims: ["My agent works."], evidence_urls: ["https://github.com/..."] },
});
// audit.result_hash is cryptographically bound to audit.scorecard
```

---

## 13. Security Model

| Threat | Control |
|---|---|
| Prompt injection via README/code | Claude system prompt constrains output to structured JSON; no code execution |
| Malicious repo with huge files | `MAX_REPO_MB=250` limit enforced before clone |
| Infinite job execution | `MAX_JOB_SECONDS=300` hard timeout per job |
| Network abuse during repro | `ALLOW_NETWORK_REPRO=false` by default |
| Result tampering | SHA-256 hash in `result_hash.sha256` covers canonical `result.json` |
| Log tampering | `attestation.json` includes SHA-256 of `execution_log.jsonl` |
| Secret exposure in logs | Worker outputs are sanitized; no env vars logged |
| Wallet key exposure | `WALLET_PRIVATE_KEY` never logged or included in proof packs |

**Note:** CAPScore is a hackathon demo. For production use, add: request authentication, rate limiting, a persistent job store (Redis/Postgres), and signature verification on the attestation.

---

## 14. Judging Criteria Mapping

| Criterion | Weight | How CAPScore Addresses It | Implementation |
|---|---|---|---|
| Technical Execution | 30% | Multi-worker audit pipeline; reproducibility check; CI integration; Docker stack | `api/app/workers/`, `api/app/scoring.py`, `.github/workflows/ci.yml` |
| A2A Composability | 25% | 3 registered CAP capabilities; calls 3 sub-agents; typed I/O schemas; CAP pricing + SLA | `cap-provider/src/`, `api/app/a2a_client.py`, `api/app/orchestrator.py` |
| Innovation | 20% | Novel verification primitive; SHA-256 proof packs; AI claim verification; demo coach worker | `api/app/proof_pack.py`, `api/app/workers/claim_verifier.py`, `api/app/workers/demo_coach.py` |
| Adoption Readiness | 15% | Agent Store listing; 5-command quickstart; .env.example; Docker Compose; public proof URLs | `README.md`, `docker-compose.yml`, `.env.example`, `frontend/` |
| Presentation Readiness | 10% | Professional frontend; sample proof pack; demo script; claim verification table | `frontend/index.html`, `examples/`, `docs/demo-script.md` |

---

## 15. License

[MIT](LICENSE) — Copyright 2026 CAPScore Contributors

---

*Built for CROO Hackathon 2026 — "The Agent Economy" track*
