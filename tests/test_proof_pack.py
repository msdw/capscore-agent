import json
import zipfile
import io
import pytest
from datetime import datetime, timezone
from app.proof_pack import build_proof_pack, _sha256, _canonical_json, render_result_md
from app.models import JobResult, JobStatus, ScorecardResult, ScoreDimension, WorkerResults


def _make_job(score: float = 75.0) -> JobResult:
    sc = ScorecardResult(
        overall_score=score,
        technical_execution=ScoreDimension(score=80.0, notes="Test"),
        a2a_composability=ScoreDimension(score=70.0, notes="Test"),
        innovation=ScoreDimension(score=75.0, notes="Test"),
        adoption_readiness=ScoreDimension(score=65.0, notes="Test"),
        presentation_readiness=ScoreDimension(score=70.0, notes="Test"),
        critical_issues=["Missing .env.example"],
        top_fixes=["Add .env.example"],
    )
    return JobResult(
        job_id="test_job_001",
        capability="audit_repository",
        status=JobStatus.DONE,
        created_at=datetime(2026, 6, 12, 10, 0, 0, tzinfo=timezone.utc),
        completed_at=datetime(2026, 6, 12, 10, 4, 0, tzinfo=timezone.utc),
        scorecard=sc,
        result_hash="sha256:placeholder",
    )


def test_proof_pack_deterministic():
    """Same input produces same SHA-256 hash."""
    job = _make_job(75.0)
    log_lines = ['{"ts": "2026-06-12T10:00:00Z", "event": "job_start"}']
    zip1 = build_proof_pack(job, log_lines)
    zip2 = build_proof_pack(job, log_lines)
    # Extract and compare result.json hashes
    with zipfile.ZipFile(io.BytesIO(zip1)) as z1, zipfile.ZipFile(io.BytesIO(zip2)) as z2:
        hash1 = z1.read("result_hash.sha256").decode()
        hash2 = z2.read("result_hash.sha256").decode()
    assert hash1 == hash2


def test_proof_pack_contains_required_files():
    """ZIP must contain all required proof files."""
    job = _make_job()
    zip_bytes = build_proof_pack(job, [])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = set(zf.namelist())
    required = {
        "manifest.json",
        "result.json",
        "result.md",
        "result_hash.sha256",
        "execution_log.jsonl",
        "attestation.json",
        "evidence/sources.json",
    }
    assert required.issubset(names), f"Missing files: {required - names}"


def test_result_hash_format():
    """Result hash must start with 'sha256:'."""
    job = _make_job()
    zip_bytes = build_proof_pack(job, [])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        hash_content = zf.read("result_hash.sha256").decode()
    assert hash_content.startswith("sha256:")


def test_result_hash_is_hex():
    """The hex part of the SHA-256 hash is a valid 64-char hex string."""
    job = _make_job()
    zip_bytes = build_proof_pack(job, [])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        hash_content = zf.read("result_hash.sha256").decode()
    hex_part = hash_content.removeprefix("sha256:")
    assert len(hex_part) == 64
    assert all(c in "0123456789abcdef" for c in hex_part)


def test_manifest_valid_json():
    """manifest.json must be valid JSON."""
    job = _make_job()
    zip_bytes = build_proof_pack(job, [])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    assert "job_id" in manifest
    assert "result_hash" in manifest
    assert "proof_files" in manifest


def test_manifest_job_id_matches():
    """manifest.json job_id matches the job."""
    job = _make_job()
    zip_bytes = build_proof_pack(job, [])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
    assert manifest["job_id"] == "test_job_001"


def test_attestation_valid_json():
    """attestation.json must be valid JSON with required fields."""
    job = _make_job()
    zip_bytes = build_proof_pack(job, [])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        attestation = json.loads(zf.read("attestation.json"))
    assert "statement" in attestation
    assert "result_hash" in attestation
    assert "provider_agent" in attestation


def test_attestation_hash_matches_manifest():
    """attestation.json result_hash matches manifest.json result_hash."""
    job = _make_job()
    zip_bytes = build_proof_pack(job, [])
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        attestation = json.loads(zf.read("attestation.json"))
    assert manifest["result_hash"] == attestation["result_hash"]


def test_canonical_json_deterministic():
    """_canonical_json produces identical output for same input."""
    obj = {"b": 2, "a": 1, "c": {"z": 26, "x": 24}}
    assert _canonical_json(obj) == _canonical_json(obj)
    assert _canonical_json(obj) == _canonical_json({"a": 1, "b": 2, "c": {"x": 24, "z": 26}})


def test_canonical_json_sorted_keys():
    """_canonical_json sorts keys alphabetically."""
    obj = {"z": 1, "a": 2, "m": 3}
    result = _canonical_json(obj)
    parsed = json.loads(result)
    assert list(parsed.keys()) == ["a", "m", "z"]


def test_sha256_returns_hex():
    """_sha256 returns a 64-char lowercase hex string."""
    result = _sha256("hello world")
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_sha256_known_value():
    """_sha256 returns the correct SHA-256 for 'hello world'."""
    import hashlib
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert _sha256("hello world") == expected


def test_result_md_contains_score():
    """result.md must contain the overall score."""
    job = _make_job(84.0)
    md = render_result_md(job)
    assert "84" in md
    assert "CAPScore" in md


def test_result_md_contains_dimensions():
    """result.md must contain all 5 scoring dimensions."""
    job = _make_job(75.0)
    md = render_result_md(job)
    assert "Technical Execution" in md
    assert "A2A Composability" in md
    assert "Innovation" in md
    assert "Adoption Readiness" in md
    assert "Presentation Readiness" in md


def test_result_md_contains_critical_issues():
    """result.md includes Critical Issues section when issues exist."""
    job = _make_job(75.0)
    md = render_result_md(job)
    assert "Critical Issues" in md
    assert "Missing .env.example" in md


def test_result_md_no_scorecard():
    """render_result_md handles a job with no scorecard gracefully."""
    job = JobResult(
        job_id="no_scorecard_job",
        capability="audit_repository",
        status=JobStatus.DONE,
        created_at=datetime(2026, 6, 12, 10, 0, 0, tzinfo=timezone.utc),
    )
    md = render_result_md(job)
    assert "CAPScore" in md
    assert "no_scorecard_job" in md


def test_proof_pack_different_scores_different_hashes():
    """Two jobs with different scores produce different hashes."""
    job1 = _make_job(75.0)
    job2 = _make_job(90.0)
    zip1 = build_proof_pack(job1, [])
    zip2 = build_proof_pack(job2, [])
    with zipfile.ZipFile(io.BytesIO(zip1)) as z1, zipfile.ZipFile(io.BytesIO(zip2)) as z2:
        hash1 = z1.read("result_hash.sha256").decode()
        hash2 = z2.read("result_hash.sha256").decode()
    assert hash1 != hash2


def test_execution_log_written():
    """execution_log.jsonl contains the provided log lines."""
    job = _make_job()
    log_lines = [
        '{"ts": "2026-06-12T10:00:00Z", "event": "job_start"}',
        '{"ts": "2026-06-12T10:01:00Z", "event": "worker_done", "worker": "repo"}',
    ]
    zip_bytes = build_proof_pack(job, log_lines)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        log_content = zf.read("execution_log.jsonl").decode()
    for line in log_lines:
        assert line in log_content
