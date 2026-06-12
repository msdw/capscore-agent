# CAP Integration — Technical Reference

CAPScore Agent integrates with the CROO Commerce Agent Protocol (CAP) to register capabilities, accept orders, run audit pipelines, and deliver cryptographically-verifiable proof of results.

---

## Order Lifecycle

```
CROO Network                CAPScore cap-provider (TS)      CAPScore API (Python)
    │                               │                               │
    │  WebSocket: new_order         │                               │
    │──────────────────────────────►│                               │
    │                               │  POST /jobs/{capability}      │
    │                               │──────────────────────────────►│
    │                               │                               │ create job (PENDING)
    │                               │  {job_id, status: "pending"}  │
    │                               │◄──────────────────────────────│
    │                               │                               │ background: run workers
    │                               │                               │   - repo_reproducer
    │                               │                               │   - cap_inspector
    │                               │                               │   - claim_verifier
    │                               │                               │   - security_scanner
    │                               │                               │   - readme_rewriter
    │                               │                               │   - demo_coach
    │                               │                               │ compute scorecard
    │                               │  GET /jobs/{job_id} (poll)    │ build proof pack
    │                               │──────────────────────────────►│
    │                               │  {status: "done", scorecard}  │
    │                               │◄──────────────────────────────│
    │                               │                               │
    │  CAP delivery: proof_pack_url │                               │
    │◄──────────────────────────────│                               │
    │                               │                               │
```

---

## SDK Methods Used

### Registration (`registerCapabilities.ts`)

```typescript
import { CROOClient } from "@croo/agent-sdk";

const client = new CROOClient({
  apiKey: process.env.CROO_SDK_KEY,
  agentId: process.env.CAPSCORE_AGENT_ID,
});

// Register all 3 capabilities
await client.registerCapability({
  id: "audit_repository",
  schema: AUDIT_REPO_SCHEMA,
  pricing: { amount: 0.05, currency: "CROO" },
  sla: { max_seconds: 300 },
});

await client.registerCapability({
  id: "audit_agent_listing",
  schema: AUDIT_AGENT_SCHEMA,
  pricing: { amount: 0.08, currency: "CROO" },
  sla: { max_seconds: 480 },
});

await client.registerCapability({
  id: "verify_claims",
  schema: VERIFY_CLAIMS_SCHEMA,
  pricing: { amount: 0.02, currency: "CROO" },
  sla: { max_seconds: 120 },
});
```

### Order Handling (`orderHandler.ts`)

```typescript
client.onOrder(async (order) => {
  const response = await fetch(`${process.env.CAPSCORE_API_URL}/jobs/${order.capability}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(order.input),
  });
  const job = await response.json();
  
  // Poll until done
  const result = await pollUntilDone(job.job_id);
  
  // Deliver proof via CAP
  await client.deliverProof(order.id, {
    result: result.scorecard,
    proof_pack_url: result.proof_pack_url,
    result_hash: result.result_hash,
  });
});
```

### Proof Delivery (`deliverProof.ts`)

```typescript
await client.deliverProof(orderId, {
  status: "completed",
  output: {
    scorecard: job.scorecard,
    overall_score: job.scorecard.overall_score,
    result_hash: job.result_hash,
    proof_pack_url: job.proof_pack_url,
    a2a_calls: job.a2a_calls,
  },
  proof: {
    hash: job.result_hash,
    algorithm: "sha256",
    canonical: "json-sorted-keys",
  },
});
```

---

## Capability Schemas

### `audit_repository`

```json
{
  "type": "object",
  "required": ["github_url"],
  "properties": {
    "github_url": {
      "type": "string",
      "description": "HTTPS URL of the GitHub repository to audit"
    },
    "branch": {
      "type": "string",
      "default": "main",
      "description": "Branch to audit"
    },
    "run_tests": {
      "type": "boolean",
      "default": true,
      "description": "Whether to attempt running the test suite"
    },
    "run_security_scan": {
      "type": "boolean",
      "default": true,
      "description": "Whether to scan for hardcoded secrets and dangerous patterns"
    },
    "expected_start_command": {
      "type": "string",
      "description": "Optional override for the detected start command"
    }
  },
  "additionalProperties": false
}
```

### `audit_agent_listing`

```json
{
  "type": "object",
  "required": ["agent_listing_url"],
  "properties": {
    "agent_listing_url": {
      "type": "string",
      "description": "CROO Agent Store listing URL"
    },
    "github_url": {
      "type": "string",
      "description": "GitHub repository URL (optional but improves score accuracy)"
    },
    "demo_url": {
      "type": "string",
      "description": "Demo video URL (YouTube, Loom, etc.)"
    },
    "claimed_tracks": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Hackathon tracks the agent is submitted to"
    },
    "depth": {
      "type": "string",
      "enum": ["quick", "standard", "deep"],
      "default": "standard",
      "description": "Audit depth: quick=2min, standard=5min, deep=10min"
    }
  },
  "additionalProperties": false
}
```

### `verify_claims`

```json
{
  "type": "object",
  "required": ["claims"],
  "properties": {
    "claims": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "maxItems": 20,
      "description": "List of claims to verify"
    },
    "evidence_urls": {
      "type": "array",
      "items": { "type": "string" },
      "description": "URLs to use as evidence (GitHub, Agent Store, demo video)"
    },
    "strictness": {
      "type": "string",
      "enum": ["lenient", "standard", "strict"],
      "default": "standard",
      "description": "How strictly to evaluate claims"
    }
  },
  "additionalProperties": false
}
```

---

## Output Schema (all capabilities)

```json
{
  "job_id": "capscore_YYYYMMDD_HHMMSS_hex8",
  "status": "done | failed | pending | running",
  "capability": "audit_repository | audit_agent_listing | verify_claims",
  "created_at": "ISO-8601",
  "completed_at": "ISO-8601",
  "scorecard": {
    "overall_score": 84.0,
    "technical_execution": { "score": 85.7, "notes": "...", "checks": [] },
    "a2a_composability":   { "score": 85.7, "notes": "...", "checks": [] },
    "innovation":          { "score": 80.0, "notes": "...", "checks": [] },
    "adoption_readiness":  { "score": 83.3, "notes": "...", "checks": [] },
    "presentation_readiness": { "score": 80.0, "notes": "...", "checks": [] },
    "critical_issues": ["..."],
    "top_fixes": ["..."]
  },
  "result_hash": "sha256:<hex64>",
  "proof_pack_url": "https://<host>/jobs/<job_id>/proof-pack.zip",
  "a2a_calls": [
    {
      "provider_agent": "source-verifier-mock",
      "cap_order_id": "order_sv_001",
      "task": "verify_github_source",
      "result_hash": "sha256:...",
      "status": "cleared",
      "started_at": "ISO-8601",
      "completed_at": "ISO-8601"
    }
  ]
}
```

---

## Proof Delivery Format

When CAPScore delivers a CAP proof to the ordering agent, the payload is:

```json
{
  "status": "completed",
  "output": {
    "scorecard": { "...": "..." },
    "overall_score": 84.0,
    "result_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924...",
    "proof_pack_url": "https://capscore.croo.network/jobs/.../proof-pack.zip"
  },
  "proof": {
    "hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924...",
    "algorithm": "sha256",
    "canonical": "json-sorted-keys",
    "description": "SHA-256 of canonical JSON (sort_keys=True, no whitespace)"
  }
}
```

The `result_hash` is computed as:

```python
import json, hashlib

canonical = json.dumps(scorecard_dict, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
result_hash = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

Any agent that receives this proof can independently verify it against the downloaded proof pack.

---

## A2A Call Format

When CAPScore calls a sub-agent (e.g., `security-scanner-mock`), it uses:

```typescript
const subResult = await crooClient.placeOrder({
  agentId: "security-scanner-mock",
  capability: "scan_secrets",
  input: { github_url: repoUrl },
  timeout: 120,
});

// Logged in manifest.json as:
{
  "provider_agent": "security-scanner-mock",
  "cap_order_id": "order_sec_001",
  "task": "scan_secrets",
  "result_hash": subResult.proof.hash,
  "status": "cleared",
  "started_at": "...",
  "completed_at": "..."
}
```

Each sub-agent result hash is included in the CAPScore manifest, creating a **chain of provenance** from buyer order to final proof pack.
