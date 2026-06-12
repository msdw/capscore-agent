import pytest
from app.scoring import compute_scorecard, score_technical_execution, score_a2a_composability
from app.models import WorkerResults, ReproResult, CAPInspectionResult, SecurityScanResult


def _full_worker_results() -> WorkerResults:
    """Helper: creates a WorkerResults with all checks passing."""
    return WorkerResults(
        repo=ReproResult(
            files_present={
                "README.md": True,
                ".env.example": True,
                "docker-compose.yml": True,
                "tests/": True,
                ".github/workflows/": True,
                "Dockerfile": True,
                "LICENSE": True,
            },
            reproducible=True,
            score=85.0,
            issues=[],
            suggestions=[],
        ),
        cap=CAPInspectionResult(
            checks={
                "schema_present": True,
                "pricing_defined": True,
                "proof_delivery": True,
                "output_machine_readable": True,
                "callable_by_agents": True,
                "typed_inputs": True,
                "a2a_dependency": True,
                "failure_documented": True,
                "sla_defined": True,
                "wallet_setup": True,
            },
            score=90.0,
            issues=[],
        ),
    )


def test_scoring_deterministic():
    """Same input always produces same score."""
    wr = _full_worker_results()
    input_data = {"github_url": "https://github.com/test/repo"}
    result1 = compute_scorecard(wr, input_data, a2a_calls_count=2)
    result2 = compute_scorecard(wr, input_data, a2a_calls_count=2)
    assert result1.overall_score == result2.overall_score


def test_score_range():
    """Score is always between 0 and 100."""
    wr = WorkerResults()
    result = compute_scorecard(wr, {}, 0)
    assert 0 <= result.overall_score <= 100


def test_score_range_full_pass():
    """High-quality repo scores between 0 and 100."""
    wr = _full_worker_results()
    result = compute_scorecard(wr, {"github_url": "https://github.com/test/repo"}, a2a_calls_count=3)
    assert 0 <= result.overall_score <= 100


def test_weighted_formula():
    """Overall score follows the hackathon weighting."""
    wr = WorkerResults()
    result = compute_scorecard(wr, {}, 0)
    # Verify the formula: overall = 0.30*tech + 0.25*a2a + 0.20*innov + 0.15*adopt + 0.10*pres
    expected = round(
        0.30 * result.technical_execution.score
        + 0.25 * result.a2a_composability.score
        + 0.20 * result.innovation.score
        + 0.15 * result.adoption_readiness.score
        + 0.10 * result.presentation_readiness.score,
        1,
    )
    assert result.overall_score == expected


def test_weighted_formula_with_data():
    """Weighted formula holds for a non-trivial input."""
    wr = _full_worker_results()
    input_data = {"github_url": "https://github.com/test/repo", "agent_listing_url": "https://agent.croo.network/x"}
    result = compute_scorecard(wr, input_data, a2a_calls_count=2)
    expected = round(
        0.30 * result.technical_execution.score
        + 0.25 * result.a2a_composability.score
        + 0.20 * result.innovation.score
        + 0.15 * result.adoption_readiness.score
        + 0.10 * result.presentation_readiness.score,
        1,
    )
    assert result.overall_score == expected


def test_full_cap_integration_scores_high():
    """A project with full CAP integration should score well on A2A."""
    wr = WorkerResults(
        cap=CAPInspectionResult(
            checks={
                "schema_present": True,
                "pricing_defined": True,
                "proof_delivery": True,
                "output_machine_readable": True,
                "callable_by_agents": True,
                "typed_inputs": True,
                "a2a_dependency": True,
                "failure_documented": True,
                "sla_defined": True,
                "wallet_setup": True,
            },
            score=100.0,
            issues=[],
        )
    )
    result = compute_scorecard(wr, {"github_url": "https://github.com/test/repo"}, a2a_calls_count=3)
    assert result.a2a_composability.score > 70


def test_empty_input_graceful():
    """Empty input produces a valid scorecard without crashing."""
    result = compute_scorecard(WorkerResults(), {}, 0)
    assert isinstance(result.overall_score, float)
    assert isinstance(result.critical_issues, list)
    assert isinstance(result.top_fixes, list)


def test_critical_issues_capped():
    """critical_issues list is at most 5 items."""
    wr = WorkerResults(
        repo=ReproResult(
            issues=["issue1", "issue2", "issue3", "issue4", "issue5", "issue6"],
            suggestions=["fix1", "fix2", "fix3", "fix4", "fix5", "fix6"],
        ),
        cap=CAPInspectionResult(
            issues=["cap_issue1", "cap_issue2", "cap_issue3"],
            score=0.0,
        ),
    )
    result = compute_scorecard(wr, {}, 0)
    assert len(result.critical_issues) <= 5
    assert len(result.top_fixes) <= 5


def test_security_risk_adds_critical_issue():
    """High security risk level appears in critical_issues."""
    wr = WorkerResults(
        security=SecurityScanResult(
            findings=[],
            dangerous_patterns=["eval("],
            risk_level="high",
            score=20.0,
        )
    )
    result = compute_scorecard(wr, {}, 0)
    assert any("high" in issue.lower() or "security" in issue.lower() for issue in result.critical_issues)


def test_score_technical_execution_no_data():
    """score_technical_execution handles None inputs gracefully."""
    dim = score_technical_execution(None, None, None, {})
    assert 0 <= dim.score <= 100
    assert isinstance(dim.checks, list)


def test_score_a2a_no_cap():
    """score_a2a_composability falls back gracefully when no CAP result."""
    dim = score_a2a_composability(None, {"github_url": "https://github.com/test/repo"}, a2a_calls_count=1)
    assert 0 <= dim.score <= 100


def test_a2a_calls_count_boosts_score():
    """Making A2A calls results in a higher a2a_composability score than 0 calls."""
    wr_with = WorkerResults()
    wr_without = WorkerResults()
    result_with = compute_scorecard(wr_with, {}, a2a_calls_count=2)
    result_without = compute_scorecard(wr_without, {}, a2a_calls_count=0)
    assert result_with.a2a_composability.score >= result_without.a2a_composability.score
