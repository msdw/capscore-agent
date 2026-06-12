from __future__ import annotations
from typing import Any, Dict, Optional
from .models import (
    CheckResult, ScoreDimension, ScorecardResult,
    WorkerResults, ReproResult, ClaimReport,
    CAPInspectionResult, SecurityScanResult
)


def _check(name: str, passed: bool, note: str = "") -> CheckResult:
    return CheckResult(name=name, passed=passed, note=note)


def score_technical_execution(
    repo: Optional[ReproResult],
    cap: Optional[CAPInspectionResult],
    security: Optional[SecurityScanResult],
    input_data: Dict[str, Any],
) -> ScoreDimension:
    checks: list[CheckResult] = []

    # CAP provider checks
    github_url = input_data.get("github_url", "")
    agent_url = input_data.get("agent_listing_url", "")

    checks.append(_check("github_url_provided", bool(github_url or agent_url), "Input URL provided"))

    if repo:
        checks.append(_check("readme_exists", repo.files_present.get("README.md", False), "README.md present"))
        checks.append(_check("env_example_exists", repo.files_present.get(".env.example", False), ".env.example present"))
        checks.append(_check("docker_compose_exists", repo.files_present.get("docker-compose.yml", False), "docker-compose.yml present"))
        checks.append(_check("dockerfile_exists", repo.files_present.get("Dockerfile", False), "Dockerfile present"))
        checks.append(_check("tests_exist", repo.files_present.get("tests/", False), "tests/ directory present"))
        checks.append(_check("ci_exists", repo.files_present.get(".github/workflows/", False), "CI workflow present"))
        checks.append(_check("reproducible", repo.reproducible, f"Repo setup reproducible (score={repo.score:.0f})"))

    if cap:
        checks.append(_check("cap_schema_present", cap.checks.get("schema_present", False), "CAP capability schema present"))
        checks.append(_check("cap_pricing_defined", cap.checks.get("pricing_defined", False), "CAP pricing defined"))
        checks.append(_check("cap_proof_delivery", cap.checks.get("proof_delivery", False), "Proof-of-delivery fields present"))
        checks.append(_check("cap_output_machine_readable", cap.checks.get("output_machine_readable", False), "Output is machine-readable JSON"))

    if security:
        checks.append(_check("no_critical_secrets", security.risk_level != "critical", f"Security risk level: {security.risk_level}"))

    passed = sum(1 for c in checks if c.passed)
    total = max(len(checks), 1)
    score = (passed / total) * 100

    issues = []
    if repo and not repo.reproducible:
        issues.append("Repository setup is not reproducible")
    if cap and not cap.checks.get("proof_delivery", False):
        issues.append("Missing proof-of-delivery fields in CAP integration")
    if security and security.risk_level in ("high", "critical"):
        issues.append(f"Security risk level is {security.risk_level}")

    return ScoreDimension(
        score=round(score, 1),
        checks=checks,
        notes=f"{passed}/{total} checks passed. " + "; ".join(issues) if issues else f"{passed}/{total} checks passed.",
    )


def score_a2a_composability(
    cap: Optional[CAPInspectionResult],
    input_data: Dict[str, Any],
    a2a_calls_count: int = 0,
) -> ScoreDimension:
    checks: list[CheckResult] = []

    if cap:
        checks.append(_check("callable_by_agents", cap.checks.get("callable_by_agents", False), "Service can be called by another agent"))
        checks.append(_check("typed_inputs", cap.checks.get("typed_inputs", False), "Inputs are typed/minimal"))
        checks.append(_check("structured_output", cap.checks.get("output_machine_readable", False), "Outputs are structured JSON"))
        checks.append(_check("pricing_explicit", cap.checks.get("pricing_defined", False), "Pricing and SLA explicit"))
        checks.append(_check("a2a_dependency_documented", cap.checks.get("a2a_dependency", False), "A2A dependency documented"))
    else:
        # If no cap inspector ran, give partial credit for having A2A calls
        checks.append(_check("has_github_url", bool(input_data.get("github_url")), "GitHub URL provided (proxy for composability)"))

    checks.append(_check("makes_a2a_calls", a2a_calls_count > 0, f"Makes A2A calls to other agents ({a2a_calls_count} calls)"))
    checks.append(_check("failure_behavior_documented", cap.checks.get("failure_documented", False) if cap else False, "Failure/timeout behavior documented"))

    passed = sum(1 for c in checks if c.passed)
    total = max(len(checks), 1)
    return ScoreDimension(
        score=round((passed / total) * 100, 1),
        checks=checks,
        notes=f"{passed}/{total} A2A composability checks passed.",
    )


def score_innovation(
    cap: Optional[CAPInspectionResult],
    claims: Optional[ClaimReport],
    input_data: Dict[str, Any],
) -> ScoreDimension:
    checks: list[CheckResult] = []

    checks.append(_check("cap_integrated", cap is not None and cap.score > 50, "CAP integration is real (not superficial)"))
    checks.append(_check("unique_use_case", True, "Use case is distinct from generic API marketplace"))  # default true for CAPScore context
    checks.append(_check("evidence_provided", bool(input_data.get("agent_listing_url") or input_data.get("github_url")), "Evidence URLs provided"))

    if claims:
        supported = sum(1 for v in claims.verifications if v.status == "supported")
        checks.append(_check("claims_backed_by_evidence", supported > 0, f"{supported} claims backed by evidence"))

    checks.append(_check("machine_readable_output", cap.checks.get("output_machine_readable", False) if cap else False, "Output reusable by other agents"))

    passed = sum(1 for c in checks if c.passed)
    total = max(len(checks), 1)
    return ScoreDimension(
        score=round((passed / total) * 100, 1),
        checks=checks,
        notes=f"{passed}/{total} innovation checks passed.",
    )


def score_adoption_readiness(
    repo: Optional[ReproResult],
    cap: Optional[CAPInspectionResult],
    input_data: Dict[str, Any],
) -> ScoreDimension:
    checks: list[CheckResult] = []

    checks.append(_check("listing_url_present", bool(input_data.get("agent_listing_url")), "Agent Store listing URL present"))
    checks.append(_check("github_url_present", bool(input_data.get("github_url")), "GitHub URL present"))

    if repo:
        checks.append(_check("quickstart_exists", repo.files_present.get("README.md", False), "README with quickstart present"))
        checks.append(_check("env_documented", repo.files_present.get(".env.example", False), ".env.example with documented variables"))

    if cap:
        checks.append(_check("clear_pricing", cap.checks.get("pricing_defined", False), "Clear pricing for buyers"))
        checks.append(_check("sla_defined", cap.checks.get("sla_defined", False), "SLA defined"))

    passed = sum(1 for c in checks if c.passed)
    total = max(len(checks), 1)
    return ScoreDimension(
        score=round((passed / total) * 100, 1),
        checks=checks,
        notes=f"{passed}/{total} adoption readiness checks passed.",
    )


def score_presentation_readiness(
    repo: Optional[ReproResult],
    claims: Optional[ClaimReport],
    input_data: Dict[str, Any],
) -> ScoreDimension:
    checks: list[CheckResult] = []

    checks.append(_check("readme_present", repo.files_present.get("README.md", False) if repo else bool(input_data.get("github_url")), "README present"))
    checks.append(_check("demo_url_provided", bool(input_data.get("demo_url")), "Demo video URL provided"))
    checks.append(_check("claims_present", len(input_data.get("claims", [])) > 0 or bool(input_data.get("agent_listing_url")), "Claims or listing provided"))

    if claims:
        unsupported = sum(1 for v in claims.verifications if v.status == "unsupported")
        misleading = sum(1 for v in claims.verifications if v.status == "misleading")
        checks.append(_check("no_misleading_claims", misleading == 0, f"{misleading} misleading claims found"))
        checks.append(_check("few_unsupported_claims", unsupported <= 1, f"{unsupported} unsupported claims"))

    passed = sum(1 for c in checks if c.passed)
    total = max(len(checks), 1)
    return ScoreDimension(
        score=round((passed / total) * 100, 1),
        checks=checks,
        notes=f"{passed}/{total} presentation readiness checks passed.",
    )


def compute_scorecard(
    worker_results: WorkerResults,
    input_data: Dict[str, Any],
    a2a_calls_count: int = 0,
) -> ScorecardResult:
    tech = score_technical_execution(
        worker_results.repo, worker_results.cap, worker_results.security, input_data
    )
    a2a = score_a2a_composability(worker_results.cap, input_data, a2a_calls_count)
    innov = score_innovation(worker_results.cap, worker_results.claims, input_data)
    adopt = score_adoption_readiness(worker_results.repo, worker_results.cap, input_data)
    pres = score_presentation_readiness(worker_results.repo, worker_results.claims, input_data)

    overall = round(
        0.30 * tech.score +
        0.25 * a2a.score +
        0.20 * innov.score +
        0.15 * adopt.score +
        0.10 * pres.score,
        1
    )

    # Collect critical issues and top fixes
    critical_issues: list[str] = []
    top_fixes: list[str] = []

    if worker_results.repo:
        critical_issues.extend(worker_results.repo.issues[:3])
        top_fixes.extend(worker_results.repo.suggestions[:3])
    if worker_results.cap:
        critical_issues.extend(worker_results.cap.issues[:2])
    if worker_results.security and worker_results.security.risk_level in ("high", "critical"):
        critical_issues.append(f"Security risk level: {worker_results.security.risk_level}")

    # Deduplicate
    critical_issues = list(dict.fromkeys(critical_issues))[:5]
    top_fixes = list(dict.fromkeys(top_fixes))[:5]

    return ScorecardResult(
        overall_score=overall,
        technical_execution=tech,
        a2a_composability=a2a,
        innovation=innov,
        adoption_readiness=adopt,
        presentation_readiness=pres,
        critical_issues=critical_issues,
        top_fixes=top_fixes,
    )
