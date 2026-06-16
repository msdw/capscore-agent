# CAPScore Agent

## Verifiable Due Diligence for the Agent Economy

> A paid, callable CROO/CAP agent that audits any AI agent, GitHub repository, or CROO Agent Store listing — and returns a verifiable **proof pack**: a judging-aligned scorecard, source-backed claim checks, a security review, README fixes, and an on-chain result hash.

![CAPScore Agent](https://raw.githubusercontent.com/msdw/capscore-agent/main/docs/assets/hero.png)

**🌐 Live app:** https://capscore-agent.onrender.com  ·  **💻 Code (MIT):** https://github.com/msdw/capscore-agent  ·  **🛡️ Agent Store:** _listing link_  ·  **🎥 Demo video:** _link_

---

## 🎥 Demo

[![Watch the CAPScore demo](https://raw.githubusercontent.com/msdw/capscore-agent/main/docs/assets/dashboard.png)](https://capscore-agent.onrender.com)

*▶ Click the image to open the live app, or watch the 5-minute walkthrough: **_<paste YouTube/Loom link>_**.*
*The screenshot above is the live deployment — note the “Recent Audits” panel: CAPScore audited **its own repository** and scored **86/100** (dogfooding).*

---

## The problem

CROO turns AI agents into paid, composable services. But the moment agents can *hire other agents*, **trust becomes the bottleneck**. Before a buyer (human or agent) depends on an agent, they need to answer:

- Does this agent actually work? Is the README reproducible?
- Is the CAP integration real, or just a chatbot with a price tag?
- Are the agent’s claims backed by evidence?
- Did it deliver verifiable proof before settlement?
- Is it safe for another agent to depend on?

Today there is no trusted, automated way to answer these. **CAPScore turns those questions into a paid CAP service.**

---

## What CAPScore does

Submit a **GitHub repo**, an **Agent Store listing**, or a **list of claims**, and CAPScore returns a structured **Verification Proof Pack**:

1. **Judging-aligned scorecard** — Technical Execution, A2A Composability, Innovation, Adoption Readiness, Presentation, with a transparent weighted overall score.
2. **README reproducibility report** — does the setup actually work? (`.env.example`, Docker, tests, CI…)
3. **CAP-integration inspection** — schema, pricing/SLA, proof-of-delivery, machine-readable output, A2A readiness.
4. **Claim-by-claim verification table** — each claim labeled *supported / weak / unsupported / misleading* with evidence and a suggested rewrite.
5. **Security review** — static scan for leaked secrets, dangerous commands, unpinned dependencies (never executes untrusted code).
6. **Improvement plan** — the top fixes before demo day, README rewrites, a demo script.
7. **Verifiable proof bundle** — `manifest.json`, `result.json`, deterministic `result_hash.sha256`, `execution_log.jsonl`, `attestation.json`, and an `evidence/` folder, all zipped.

Three paid capabilities are offered on the CROO Agent Store:

| Capability | What it does | Price | SLA |
|---|---|---:|---|
| `audit_repository` | Deep repo audit: reproducibility, CAP, security, README | $2.00 USDC | 5 min |
| `audit_agent_listing` | Audit an Agent Store submission vs. judging criteria | $1.00 USDC | 2 min |
| `verify_claims` | Verify claims against provided evidence URLs | $0.50 USDC | 3 min |

---

## How it works

![Architecture](https://raw.githubusercontent.com/msdw/capscore-agent/main/docs/assets/architecture.png)

A buyer places a CAP order and pays in USDC. The **CAP provider** (Node, `@croo-network/sdk`) accepts the negotiation, and on payment runs the **FastAPI analysis engine**, which orchestrates specialized workers, computes the weighted scorecard, and builds a deterministic proof pack. The result is delivered through CAP; the protocol records the deliverable’s keccak256 hash **on-chain**, and CAPVault settles USDC to the agent’s wallet.

**CAP lifecycle:** `connectWebSocket()` → `NegotiationCreated` → `acceptNegotiation()` → `OrderPaid` → run analysis → `deliverOrder({ deliverableType: Text, deliverableText })` → `OrderCompleted`.

---

## A2A composability — both directions

CAPScore is composable as a **provider** *and* as a **buyer**:

- **As a provider**, any agent can call CAPScore to vet a repo, a data source, or a listing before depending on it. Inputs are typed; output is structured JSON (reusable by other agents), not just prose.
- **As a buyer**, CAPScore *hires* a sub-agent during analysis (a source verifier) and records every A2A call in the proof pack:

```json
"a2a_calls": [
  { "provider_agent": "source-verifier", "task": "verify_sources",
    "result_hash": "sha256:…", "status": "cleared" }
]
```

If a sub-agent or LLM is unavailable, CAPScore **degrades gracefully** (Anthropic → OpenAI → deterministic rule-based heuristics), so audits never hard-fail.

---

## Why the proof matters

CAPScore is **deterministic**: the same input produces the same `result_hash`. We verified this across local runs and the live Render deployment — identical SHA-256 every time. Every factual line in the report points to evidence or is explicitly marked as inference, and “not found” is never reported as “false.” The result is a tamper-evident artifact a buyer can independently re-hash and trust.

---

## Scoring model (transparent)

```
Overall = 0.30·Technical Execution
        + 0.25·A2A Composability
        + 0.20·Innovation
        + 0.15·Adoption Readiness
        + 0.10·Presentation
```

Each dimension is a checklist of deterministic rules plus LLM judgment for synthesis — mirroring the hackathon’s own criteria, so a CAPScore report doubles as a pre-submission self-check for any team.

---

## What’s already built and live

- ✅ **Deployed and callable:** https://capscore-agent.onrender.com (FastAPI serves both the dashboard and the REST API in one container).
- ✅ **Open source, MIT:** https://github.com/msdw/capscore-agent
- ✅ **CAP provider** aligned with the real `@croo-network/sdk` v0.2.x lifecycle.
- ✅ **Proof packs** with deterministic hashing, manifest, attestation, execution log, evidence.
- ✅ **A2A** sub-agent call traced in every proof pack.
- ✅ **54 passing tests**; Docker; reproducible setup.
- ✅ **Dogfooding:** CAPScore audits its own repository and scores **86/100**.

---

## Why this can win

| Criterion | How CAPScore answers it |
|---|---|
| **Technical Execution** | Real CAP provider, deterministic proof pack with on-chain hash, Docker, 54 tests, live deployment |
| **A2A Composability** | Callable by agents *and* calls a sub-agent; A2A trace in every proof pack |
| **Innovation** | A reputation/verification layer for the agent economy — value grows as more agents join; output is machine-readable and reusable |
| **Adoption** | Immediately useful to every other hackathon team; low-friction input; clear USDC pricing; shareable score + proof hash |
| **Presentation** | A 30-second-clear story: submit → score → proof → settle → fix |

CAPScore isn’t “another chatbot.” It’s **commerce-native infrastructure for the CROO ecosystem itself** — every paid agent needs proof, and every buyer needs a reason to trust before settlement.

---

## Try it yourself

```bash
curl -X POST https://capscore-agent.onrender.com/jobs/audit-repository \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/msdw/capscore-agent"}'
# → poll GET /jobs/{job_id}, then download /jobs/{job_id}/proof-pack.zip
```

Or open the dashboard and submit a repo: **https://capscore-agent.onrender.com**

---

## Tech stack

**Python / FastAPI** analysis engine · **TypeScript / Node** CAP provider on `@croo-network/sdk` · **Anthropic + OpenAI** (with heuristic fallback) · **Docker** · deployed on **Render** · tracks: **Data & Verification Agents** + **Developer Tooling Agents**.

**Team:** Mathurin Aché ([@msdw](https://github.com/msdw)) · **License:** MIT
