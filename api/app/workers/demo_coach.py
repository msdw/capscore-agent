from __future__ import annotations
from typing import Optional

from ..models import WorkerResults
from ..config import settings


DEFAULT_DEMO_SCRIPT = """# CAPScore Demo Script — 5 Minutes

## 0:00–0:30 — Hook
"CROO turns agents into paid services. But once agents can hire other agents, trust becomes the bottleneck. CAPScore solves this by auditing agents and producing verifiable proof packs before buyers depend on them."

## 0:30–1:20 — Show Agent Store Listing
- Open CROO Agent Store
- Show CAPScore listed with 3 capabilities: audit_agent_listing, audit_repository, verify_claims
- Show prices ($0.50 / $2.00 / $1.00) and SLA (2 min / 5 min / 3 min)
- Show input schema for audit_repository

## 1:20–2:20 — Place a Real CAP Order
- Submit a GitHub repo URL (use another hackathon team's repo)
- Show CAP order accepted in logs: "NegotiationCreated → acceptNegotiation → job_start"
- Show job running in API logs

## 2:20–3:20 — Show A2A Composition
- Show CAP provider logs: "a2a_start source-verifier-mock"
- Show A2A trace in proof pack manifest: "a2a_calls": [{"provider_agent": "source-verifier-mock", "status": "cleared"}]
- Emphasize: CAPScore both SERVES other agents and HIRES other agents

## 3:20–4:20 — Show Proof Pack
- Download proof-pack-{job_id}.zip
- Show result.md: overall score, dimension breakdown, critical fixes, claims table
- Show result_hash.sha256: deterministic verification
- Show attestation.json

## 4:20–5:00 — Close
- Show CAP orders count (target: 10+)
- Show before/after improvement on one team's submission
- "CAPScore is not only a hackathon submission — it is a missing trust layer for the agent economy."
"""


async def generate_demo_script(github_url: str, worker_results: WorkerResults) -> str:
    if not settings.anthropic_api_key:
        return DEFAULT_DEMO_SCRIPT

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        context_parts = []
        if worker_results.repo:
            context_parts.append(f"Repository score: {worker_results.repo.score:.0f}/100")
            if worker_results.repo.issues:
                context_parts.append(f"Issues: {'; '.join(worker_results.repo.issues[:3])}")
        if worker_results.cap:
            context_parts.append(f"CAP integration score: {worker_results.cap.score:.0f}/100")
        context = "\n".join(context_parts) if context_parts else "No analysis results available."

        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            temperature=0,
            messages=[{"role": "user", "content": f"""Write a 5-minute demo script for CAPScore Agent (a CROO AI agent that audits other agents). The script should fit the CROO hackathon judging criteria: Technical Execution (30%), A2A Composability (25%), Innovation (20%), Adoption (15%), Presentation (10%).

Analysis context for the target agent:
{context}
GitHub URL: {github_url}

Write a concise, punchy demo script with timestamps (0:00, 0:30, 1:20, 2:20, 3:20, 4:20) showing: Agent Store listing -> CAP order -> A2A calls -> proof pack -> adoption metrics.

Keep it under 400 words."""}],
        )
        return message.content[0].text
    except Exception:
        return DEFAULT_DEMO_SCRIPT
