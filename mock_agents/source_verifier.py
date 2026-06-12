"""
Mock source-verifier agent for A2A testing.
Exposes a CAP-compatible FastAPI endpoint.
Run with: uvicorn mock_agents.source_verifier:app --port 8001
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Source Verifier Mock Agent", version="0.1.0")


class VerifySourcesRequest(BaseModel):
    evidence_urls: Optional[List[str]] = None
    github_url: Optional[str] = None
    listing_url: Optional[str] = None


class VerifySourcesResult(BaseModel):
    job_id: str
    status: str
    verified_urls: List[str]
    reachable_count: int
    summary: str
    result_hash: str
    completed_at: str


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "source-verifier-mock", "version": "0.1.0"}


@app.post("/jobs/verify_sources", response_model=VerifySourcesResult)
async def verify_sources(req: VerifySourcesRequest):
    urls = req.evidence_urls or []
    if req.github_url:
        urls.append(req.github_url)
    if req.listing_url:
        urls.append(req.listing_url)

    job_id = f"sv_mock_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    result = {
        "job_id": job_id,
        "verified_urls": urls,
        "reachable_count": len(urls),
        "summary": f"Mock verification: {len(urls)} URL(s) checked. All appear reachable.",
    }
    result_hash = f"sha256:{hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()}"

    return VerifySourcesResult(
        job_id=job_id,
        status="done",
        verified_urls=urls,
        reachable_count=len(urls),
        summary=result["summary"],
        result_hash=result_hash,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
