from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from .config import settings
from .models import (
    AuditAgentRequest, AuditRepositoryRequest, VerifyClaimsRequest,
    JobResult, JobStatus, WorkerResults, ScorecardResult
)
from .orchestrator import run_audit_repository, run_audit_agent, run_verify_claims

app = FastAPI(
    title="CAPScore API",
    description="Verifiable due diligence for AI agents — CROO Hackathon 2026",
    version="0.1.0",
)

# In-memory job store (for demo; production would use Redis/DB)
_jobs: Dict[str, JobResult] = {}


def _new_job(capability: str, input_data: Dict[str, Any]) -> JobResult:
    from .models import JobCreate
    create = JobCreate(capability=capability, input_data=input_data)
    job = JobResult(
        job_id=create.job_id,
        capability=capability,
        status=JobStatus.PENDING,
    )
    _jobs[job.job_id] = job
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    return job


def _get_job(job_id: str) -> JobResult:
    job = _jobs.get(job_id)
    if not job:
        # Try to reload from disk
        job_file = settings.runs_dir / job_id / "result.json"
        if job_file.exists():
            data = json.loads(job_file.read_text())
            job = JobResult(job_id=job_id, capability="unknown", status=JobStatus.DONE)
            job.scorecard = ScorecardResult(**data) if data else None
            result_hash_file = settings.runs_dir / job_id / "result_hash.sha256"
            job.result_hash = result_hash_file.read_text() if result_hash_file.exists() else None
            _jobs[job_id] = job
        else:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0", "jobs_in_memory": len(_jobs)}


@app.post("/jobs/audit-agent", response_model=JobResult)
async def audit_agent(req: AuditAgentRequest, background_tasks: BackgroundTasks):
    job = _new_job("audit_agent_listing", req.model_dump())

    async def run():
        try:
            await run_audit_agent(job, req)
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)

    background_tasks.add_task(run)
    return job


@app.post("/jobs/audit-repository", response_model=JobResult)
async def audit_repository(req: AuditRepositoryRequest, background_tasks: BackgroundTasks):
    job = _new_job("audit_repository", req.model_dump())

    async def run():
        try:
            await run_audit_repository(job, req)
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)

    background_tasks.add_task(run)
    return job


@app.post("/jobs/verify-claims", response_model=JobResult)
async def verify_claims(req: VerifyClaimsRequest, background_tasks: BackgroundTasks):
    job = _new_job("verify_claims", req.model_dump())

    async def run():
        try:
            await run_verify_claims(job, req)
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)

    background_tasks.add_task(run)
    return job


@app.get("/jobs/{job_id}", response_model=JobResult)
async def get_job(job_id: str):
    return _get_job(job_id)


@app.get("/jobs/{job_id}/result.md", response_class=PlainTextResponse)
async def get_result_md(job_id: str):
    result_file = settings.runs_dir / job_id / "result.md"
    if result_file.exists():
        return result_file.read_text(encoding="utf-8")
    job = _get_job(job_id)
    if job.status != JobStatus.DONE:
        raise HTTPException(status_code=202, detail=f"Job {job_id} not done yet (status: {job.status})")
    raise HTTPException(status_code=404, detail="result.md not found")


@app.get("/jobs/{job_id}/proof-pack.zip")
async def get_proof_pack(job_id: str):
    zip_path = settings.runs_dir / job_id / f"proof-pack-{job_id}.zip"
    if not zip_path.exists():
        job = _get_job(job_id)
        if job.status != JobStatus.DONE:
            raise HTTPException(status_code=202, detail=f"Job {job_id} not done yet")
        raise HTTPException(status_code=404, detail="Proof pack not found")
    return FileResponse(zip_path, media_type="application/zip", filename=f"proof-pack-{job_id}.zip")


@app.get("/jobs")
async def list_jobs():
    return [
        {"job_id": j.job_id, "status": j.status, "capability": j.capability,
         "overall_score": j.scorecard.overall_score if j.scorecard else None,
         "created_at": j.created_at.isoformat()}
        for j in sorted(_jobs.values(), key=lambda x: x.created_at, reverse=True)
    ]


# ── Static dashboard (single-container deploy) ───────────────────────────────────
# Serve the frontend from FastAPI so the whole app runs as ONE container on any
# free host. API routes above are registered first and take precedence; this
# catch-all mount handles "/" and static assets. The frontend already calls the
# API same-origin, so no separate proxy/nginx is needed.
def _resolve_frontend_dir() -> Path | None:
    candidates = [
        settings.frontend_dir,
        Path(__file__).resolve().parent.parent.parent / "frontend",
    ]
    for c in candidates:
        if c.is_dir() and (c / "index.html").exists():
            return c
    return None


_frontend = _resolve_frontend_dir()
if _frontend is not None:
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_frontend), html=True), name="frontend")
