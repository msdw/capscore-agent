# DoraHacks BUIDL Submission — CAPScore Agent

Ready-to-paste content for the CROO AI Agent Hackathon submission.
**Deadline: 2026-07-12 11:00 (CEST).** Submit on DoraHacks; register on Kaggle too.

- DoraHacks: https://dorahacks.io/hackathon/croo-hackathon
- Kaggle: https://www.kaggle.com/competitions/croo-ai-agent-hackathon-10-k-usd-prize-pool

---

## Name
CAPScore Agent

## Tagline (one line)
Verifiable due diligence for the agent economy — audit any AI agent, GitHub repo, or CROO Agent Store listing and get a judging-aligned scorecard plus a verifiable proof pack.

## Tracks (max 2)
1. **Data & Verification Agents** (primary)
2. **Developer Tooling Agents** (secondary)

## Links
- **GitHub (open source, MIT):** https://github.com/msdw/capscore-agent
- **Live app / demo:** https://capscore-agent.onrender.com
- **CROO Agent Store listing:** _<paste agent.croo.network URL after registering>_
- **Demo video (≤5 min):** _<paste link after recording>_

## Description

As agents become paid, composable services on CROO, buyers face a trust bottleneck:
*Does this agent actually work? Is the CAP integration real? Are its claims backed by
evidence? Is it safe to depend on?* **CAPScore Agent** turns these questions into a paid
CAP service.

Submit a GitHub repo, an Agent Store listing, or a set of claims, and CAPScore returns a
**Verification Proof Pack**:
- A **judging-aligned scorecard** (Technical Execution, A2A Composability, Innovation,
  Adoption Readiness, Presentation) with a transparent weighted overall score.
- A **README reproducibility** check, **CAP-integration** inspection, **security scan**
  (secrets/dangerous patterns), and a **claim-by-claim verification table** with evidence
  and suggested rewrites.
- A **verifiable proof bundle**: `manifest.json`, `result.json`, deterministic
  `result_hash.sha256`, `execution_log.jsonl`, `attestation.json`, and an `evidence/` folder.

CAPScore is **A2A-composable in both directions**: it is callable by other agents via CAP,
and it *hires* a sub-agent (source verifier) during analysis, recording the A2A call in the
proof pack. It runs deterministically (same input → same hash) and degrades gracefully when
an LLM or sub-agent is unavailable (Anthropic → OpenAI → rule-based heuristics).

## How it uses CAP / SDK methods
- Node provider on `@croo-network/sdk` v0.2.x: `connectWebSocket()` → `EventType.NegotiationCreated`
  → `acceptNegotiation()` → on `EventType.OrderPaid` runs the analysis → `deliverOrder(orderId,
  { deliverableType: DeliverableType.Text, deliverableText })`. The protocol records the
  deliverable's keccak256 hash on-chain; settlement clears USDC to the agent's AA wallet.
- 3 paid services (configured in the dashboard): **Audit Repository** ($2), **Audit Agent
  Listing** ($1), **Verify Claims** ($0.50).

## Architecture (one container + provider)
- **FastAPI** analysis engine serves both the dashboard (`/`) and the REST API
  (`/health`, `/jobs/...`) — single container, deployed on Render.
- **Workers**: repo reproducer, CAP inspector, security scanner, claim verifier (LLM),
  README rewriter (LLM), demo coach (LLM), scorecard, proof-pack builder.
- **CAP provider** (Node) bridges CROO orders to the analysis API and delivers results.

## Why it can win (maps to judging signals)
- **Technical execution**: real CAP provider, deterministic proof pack with on-chain hash,
  Docker, 54 passing tests, live deployment.
- **A2A composability**: callable by agents *and* calls a sub-agent; A2A trace in proof pack.
- **Innovation**: a reputation/verification layer for the agent economy — value grows as
  more agents join; output is machine-readable and reusable by other agents.
- **Adoption**: immediately useful to every other hackathon team; low-friction input;
  clear pricing; shareable score + proof hash.
- **Presentation**: 30-second-clear demo (submit → score → proof → settle → fix).

## Mandatory deliverables checklist
- [x] Open-source public repo, MIT license — https://github.com/msdw/capscore-agent
- [x] Live, callable analysis API + dashboard — https://capscore-agent.onrender.com
- [x] README with setup, SDK methods used, integration notes
- [ ] Listed on CROO Agent Store (see `docs/CROO_ONBOARDING.md`)
- [ ] CAP integration settling on-chain in USDC (deploy `cap-provider` with real `CROO_SDK_KEY`)
- [ ] Demo video ≤5 min (script in `docs/demo-script.md`)
- [ ] BUIDL filed on DoraHacks with all fields complete

## Team
- Mathurin Aché (GitHub: msdw)

## License
MIT
