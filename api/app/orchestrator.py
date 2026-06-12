from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

from .config import settings
from .models import (
    AuditAgentRequest, AuditRepositoryRequest, VerifyClaimsRequest,
    JobResult, JobStatus, WorkerResults, A2ACall
)
from .scoring import compute_scorecard
from .proof_pack import persist_proof_pack
from .a2a_client import call_cap_agent


class ExecutionLogger:
    def __init__(self):
        self._lines: List[str] = []

    def log(self, event: str, data: Dict[str, Any] = None) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **(data or {}),
        }
        self._lines.append(json.dumps(entry))

    def lines(self) -> List[str]:
        return self._lines.copy()


async def _import_workers():
    from .workers.repo_reproducer import reproduce_repository
    from .workers.claim_verifier import verify_claims
    from .workers.cap_inspector import inspect_cap_integration
    from .workers.security_scanner import scan_security
    from .workers.readme_rewriter import suggest_readme_fixes
    from .workers.demo_coach import generate_demo_script
    return reproduce_repository, verify_claims, inspect_cap_integration, scan_security, suggest_readme_fixes, generate_demo_script


async def run_audit_repository(job: JobResult, req: AuditRepositoryRequest) -> JobResult:
    logger = ExecutionLogger()
    logger.log("job_start", {"job_id": job.job_id, "capability": "audit_repository"})
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)

    (reproduce_repository, verify_claims_fn, inspect_cap_integration,
     scan_security, suggest_readme_fixes, generate_demo_script) = await _import_workers()

    worker_results = WorkerResults()

    # Step 1: Repository analysis
    logger.log("worker_start", {"worker": "repo_reproducer"})
    try:
        worker_results.repo = await asyncio.wait_for(
            reproduce_repository(req.github_url, req.branch),
            timeout=settings.max_job_seconds / 2
        )
        logger.log("worker_done", {"worker": "repo_reproducer", "score": worker_results.repo.score})
    except asyncio.TimeoutError:
        logger.log("worker_timeout", {"worker": "repo_reproducer"})
    except Exception as e:
        logger.log("worker_error", {"worker": "repo_reproducer", "error": str(e)})

    # Step 2: Security scan
    if req.run_security_scan and worker_results.repo:
        logger.log("worker_start", {"worker": "security_scanner"})
        try:
            worker_results.security = await asyncio.wait_for(
                scan_security(req.github_url),
                timeout=60
            )
            logger.log("worker_done", {"worker": "security_scanner", "risk": worker_results.security.risk_level})
        except Exception as e:
            logger.log("worker_error", {"worker": "security_scanner", "error": str(e)})

    # Step 3: CAP inspection
    logger.log("worker_start", {"worker": "cap_inspector"})
    try:
        worker_results.cap = await asyncio.wait_for(
            inspect_cap_integration(req.github_url),
            timeout=60
        )
        logger.log("worker_done", {"worker": "cap_inspector", "score": worker_results.cap.score})
    except Exception as e:
        logger.log("worker_error", {"worker": "cap_inspector", "error": str(e)})

    # Step 4: README rewrite suggestions (LLM)
    logger.log("worker_start", {"worker": "readme_rewriter"})
    try:
        worker_results.readme_suggestions = await asyncio.wait_for(
            suggest_readme_fixes(req.github_url, worker_results.repo),
            timeout=60
        )
        logger.log("worker_done", {"worker": "readme_rewriter"})
    except Exception as e:
        logger.log("worker_error", {"worker": "readme_rewriter", "error": str(e)})

    # Step 5: Demo coach (LLM)
    logger.log("worker_start", {"worker": "demo_coach"})
    try:
        worker_results.demo_script = await asyncio.wait_for(
            generate_demo_script(req.github_url, worker_results),
            timeout=60
        )
        logger.log("worker_done", {"worker": "demo_coach"})
    except Exception as e:
        logger.log("worker_error", {"worker": "demo_coach", "error": str(e)})

    # Step 6: A2A calls (source verifier)
    a2a_calls: List[A2ACall] = []
    logger.log("a2a_start", {"agent": "source-verifier-mock"})
    try:
        a2a_call = await call_cap_agent(
            "source-verifier-mock",
            "verify_sources",
            {"github_url": req.github_url},
            timeout=30,
        )
        a2a_calls.append(a2a_call)
        logger.log("a2a_done", {"agent": "source-verifier-mock", "status": a2a_call.status})
    except Exception as e:
        logger.log("a2a_error", {"agent": "source-verifier-mock", "error": str(e)})

    job.a2a_calls = a2a_calls
    job.worker_results = worker_results

    # Compute scorecard
    input_data = req.model_dump()
    job.scorecard = compute_scorecard(worker_results, input_data, len(a2a_calls))
    logger.log("scorecard_computed", {"overall_score": job.scorecard.overall_score})

    # Build proof pack
    job.completed_at = datetime.now(timezone.utc)
    job.status = JobStatus.DONE
    persist_proof_pack(job, logger.lines())
    logger.log("proof_pack_built", {"result_hash": job.result_hash})

    return job


async def run_audit_agent(job: JobResult, req: AuditAgentRequest) -> JobResult:
    logger = ExecutionLogger()
    logger.log("job_start", {"job_id": job.job_id, "capability": "audit_agent_listing"})
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)

    (_, verify_claims_fn, inspect_cap_integration,
     _, suggest_readme_fixes, generate_demo_script) = await _import_workers()

    worker_results = WorkerResults()

    if req.github_url:
        logger.log("worker_start", {"worker": "cap_inspector"})
        try:
            worker_results.cap = await asyncio.wait_for(
                inspect_cap_integration(req.github_url),
                timeout=60
            )
            logger.log("worker_done", {"worker": "cap_inspector", "score": worker_results.cap.score})
        except Exception as e:
            logger.log("worker_error", {"worker": "cap_inspector", "error": str(e)})

    # Verify any claims from listing
    if req.claimed_tracks:
        logger.log("worker_start", {"worker": "claim_verifier"})
        try:
            evidence_urls = [req.agent_listing_url]
            if req.github_url:
                evidence_urls.append(req.github_url)
            worker_results.claims = await asyncio.wait_for(
                verify_claims_fn(req.claimed_tracks, evidence_urls, "standard"),
                timeout=90
            )
            logger.log("worker_done", {"worker": "claim_verifier"})
        except Exception as e:
            logger.log("worker_error", {"worker": "claim_verifier", "error": str(e)})

    # A2A call
    a2a_calls: List[A2ACall] = []
    try:
        a2a_call = await call_cap_agent(
            "source-verifier-mock", "verify_sources",
            {"listing_url": req.agent_listing_url}, timeout=30
        )
        a2a_calls.append(a2a_call)
    except Exception:
        pass

    job.a2a_calls = a2a_calls
    job.worker_results = worker_results
    job.scorecard = compute_scorecard(worker_results, req.model_dump(), len(a2a_calls))
    job.completed_at = datetime.now(timezone.utc)
    job.status = JobStatus.DONE
    persist_proof_pack(job, logger.lines())
    return job


async def run_verify_claims(job: JobResult, req: VerifyClaimsRequest) -> JobResult:
    logger = ExecutionLogger()
    logger.log("job_start", {"job_id": job.job_id, "capability": "verify_claims"})
    job.status = JobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)

    (_, verify_claims_fn, _, _, _, _) = await _import_workers()

    worker_results = WorkerResults()

    logger.log("worker_start", {"worker": "claim_verifier"})
    try:
        worker_results.claims = await asyncio.wait_for(
            verify_claims_fn(req.claims, req.evidence_urls or [], req.strictness),
            timeout=90
        )
        logger.log("worker_done", {"worker": "claim_verifier", "claims_count": len(req.claims)})
    except Exception as e:
        logger.log("worker_error", {"worker": "claim_verifier", "error": str(e)})

    a2a_calls: List[A2ACall] = []
    if req.evidence_urls:
        try:
            a2a_call = await call_cap_agent(
                "source-verifier-mock", "verify_sources",
                {"evidence_urls": req.evidence_urls}, timeout=30
            )
            a2a_calls.append(a2a_call)
        except Exception:
            pass

    job.a2a_calls = a2a_calls
    job.worker_results = worker_results
    job.scorecard = compute_scorecard(worker_results, req.model_dump(), len(a2a_calls))
    job.completed_at = datetime.now(timezone.utc)
    job.status = JobStatus.DONE
    persist_proof_pack(job, logger.lines())
    return job
