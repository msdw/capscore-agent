from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
import uuid


# ── Enums ──────────────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


# ── Request Models ─────────────────────────────────────────────────────────────

class AuditAgentRequest(BaseModel):
    agent_listing_url: str
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    claimed_tracks: Optional[List[str]] = None
    depth: Literal["quick", "standard", "deep"] = "standard"


class AuditRepositoryRequest(BaseModel):
    github_url: str
    branch: str = "main"
    run_tests: bool = True
    run_security_scan: bool = True
    expected_start_command: Optional[str] = None


class VerifyClaimsRequest(BaseModel):
    claims: List[str] = Field(min_length=1)
    evidence_urls: Optional[List[str]] = None
    strictness: Literal["lenient", "standard", "strict"] = "standard"


# ── Worker Result Models ───────────────────────────────────────────────────────

class CheckResult(BaseModel):
    name: str
    passed: bool
    note: str = ""


class ReproResult(BaseModel):
    stack_detected: str = "unknown"
    files_present: Dict[str, bool] = Field(default_factory=dict)
    reproducible: bool = False
    score: float = 0.0
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    test_output: Optional[str] = None
    checks: List[CheckResult] = Field(default_factory=list)


class ClaimVerification(BaseModel):
    claim: str
    status: Literal["supported", "weak", "unsupported", "misleading"]
    evidence: str = ""
    confidence: float = 0.0
    suggested_rewrite: str = ""


class ClaimReport(BaseModel):
    verifications: List[ClaimVerification] = Field(default_factory=list)
    score: float = 50.0


class CAPInspectionResult(BaseModel):
    checks: Dict[str, bool] = Field(default_factory=dict)
    score: float = 0.0
    issues: List[str] = Field(default_factory=list)


class SecurityFinding(BaseModel):
    file: str
    line: int = 0
    pattern: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str


class SecurityScanResult(BaseModel):
    findings: List[SecurityFinding] = Field(default_factory=list)
    dangerous_patterns: List[str] = Field(default_factory=list)
    unpinned_deps: List[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    score: float = 100.0


class WorkerResults(BaseModel):
    repo: Optional[ReproResult] = None
    claims: Optional[ClaimReport] = None
    cap: Optional[CAPInspectionResult] = None
    security: Optional[SecurityScanResult] = None
    readme_suggestions: Optional[List[str]] = None
    demo_script: Optional[str] = None


# ── Scorecard Models ───────────────────────────────────────────────────────────

class ScoreDimension(BaseModel):
    score: float = 0.0
    checks: List[CheckResult] = Field(default_factory=list)
    notes: str = ""


class ScorecardResult(BaseModel):
    overall_score: float = 0.0
    technical_execution: ScoreDimension = Field(default_factory=ScoreDimension)
    a2a_composability: ScoreDimension = Field(default_factory=ScoreDimension)
    innovation: ScoreDimension = Field(default_factory=ScoreDimension)
    adoption_readiness: ScoreDimension = Field(default_factory=ScoreDimension)
    presentation_readiness: ScoreDimension = Field(default_factory=ScoreDimension)
    critical_issues: List[str] = Field(default_factory=list)
    top_fixes: List[str] = Field(default_factory=list)


# ── A2A Models ─────────────────────────────────────────────────────────────────

class A2ACall(BaseModel):
    provider_agent: str
    cap_order_id: str
    task: str
    result_hash: str = ""
    status: str = "pending"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


# ── Job Models ─────────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    job_id: str = Field(default_factory=lambda: f"capscore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}")
    capability: str
    input_data: Dict[str, Any]


class JobResult(BaseModel):
    job_id: str
    status: JobStatus = JobStatus.PENDING
    capability: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scorecard: Optional[ScorecardResult] = None
    worker_results: Optional[WorkerResults] = None
    proof_pack_url: Optional[str] = None
    result_hash: Optional[str] = None
    a2a_calls: List[A2ACall] = Field(default_factory=list)
    error: Optional[str] = None
