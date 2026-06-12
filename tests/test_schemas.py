import json
import pytest


# The 3 capability input schemas (mirrors schemas.ts)
AUDIT_AGENT_SCHEMA = {
    "type": "object",
    "required": ["agent_listing_url"],
    "properties": {
        "agent_listing_url": {"type": "string"},
        "github_url": {"type": "string"},
        "demo_url": {"type": "string"},
        "claimed_tracks": {"type": "array", "items": {"type": "string"}},
        "depth": {"type": "string", "enum": ["quick", "standard", "deep"]},
    },
}

AUDIT_REPO_SCHEMA = {
    "type": "object",
    "required": ["github_url"],
    "properties": {
        "github_url": {"type": "string"},
        "branch": {"type": "string"},
        "run_tests": {"type": "boolean"},
        "run_security_scan": {"type": "boolean"},
        "expected_start_command": {"type": "string"},
    },
}

VERIFY_CLAIMS_SCHEMA = {
    "type": "object",
    "required": ["claims"],
    "properties": {
        "claims": {"type": "array", "items": {"type": "string"}},
        "evidence_urls": {"type": "array", "items": {"type": "string"}},
        "strictness": {"type": "string", "enum": ["lenient", "standard", "strict"]},
    },
}


# ── Schema structure tests ─────────────────────────────────────────────────────

def test_schemas_are_valid_json():
    """All schemas should serialize/deserialize as valid JSON."""
    for schema in [AUDIT_AGENT_SCHEMA, AUDIT_REPO_SCHEMA, VERIFY_CLAIMS_SCHEMA]:
        serialized = json.dumps(schema)
        deserialized = json.loads(serialized)
        assert deserialized["type"] == "object"
        assert "properties" in deserialized


def test_all_schemas_have_required_field():
    """All schemas declare at least one required field."""
    for schema in [AUDIT_AGENT_SCHEMA, AUDIT_REPO_SCHEMA, VERIFY_CLAIMS_SCHEMA]:
        assert "required" in schema
        assert len(schema["required"]) >= 1


def test_audit_agent_requires_listing_url():
    """audit_agent_listing requires agent_listing_url."""
    assert "agent_listing_url" in AUDIT_AGENT_SCHEMA["required"]


def test_audit_repo_requires_github_url():
    """audit_repository requires github_url."""
    assert "github_url" in AUDIT_REPO_SCHEMA["required"]


def test_verify_claims_requires_claims():
    """verify_claims requires claims array."""
    assert "claims" in VERIFY_CLAIMS_SCHEMA["required"]


def test_depth_enum_values():
    """depth field in audit_agent_listing has correct enum values."""
    depth_prop = AUDIT_AGENT_SCHEMA["properties"]["depth"]
    assert set(depth_prop["enum"]) == {"quick", "standard", "deep"}


def test_strictness_enum_values():
    """strictness field in verify_claims has correct enum values."""
    strictness_prop = VERIFY_CLAIMS_SCHEMA["properties"]["strictness"]
    assert set(strictness_prop["enum"]) == {"lenient", "standard", "strict"}


def test_audit_agent_optional_fields():
    """audit_agent_listing optional fields are present in schema."""
    props = AUDIT_AGENT_SCHEMA["properties"]
    for field in ["github_url", "demo_url", "claimed_tracks", "depth"]:
        assert field in props, f"Optional field '{field}' missing from schema"


def test_audit_repo_optional_fields():
    """audit_repository optional fields are present in schema."""
    props = AUDIT_REPO_SCHEMA["properties"]
    for field in ["branch", "run_tests", "run_security_scan", "expected_start_command"]:
        assert field in props, f"Optional field '{field}' missing from schema"


def test_verify_claims_evidence_urls_is_array():
    """evidence_urls in verify_claims must be declared as array."""
    prop = VERIFY_CLAIMS_SCHEMA["properties"]["evidence_urls"]
    assert prop["type"] == "array"


def test_claimed_tracks_items_are_strings():
    """claimed_tracks items must be typed as string."""
    prop = AUDIT_AGENT_SCHEMA["properties"]["claimed_tracks"]
    assert prop["items"]["type"] == "string"


def test_claims_items_are_strings():
    """claims items must be typed as string."""
    prop = VERIFY_CLAIMS_SCHEMA["properties"]["claims"]
    assert prop["items"]["type"] == "string"


# ── API integration tests ──────────────────────────────────────────────────────

def test_api_health_endpoint(api_client):
    """Health endpoint returns 200."""
    resp = api_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_api_health_has_version(api_client):
    """Health endpoint returns version field."""
    resp = api_client.get("/health")
    data = resp.json()
    assert "version" in data


def test_api_audit_repo_creates_job(api_client):
    """POST /jobs/audit-repository creates a job and returns job_id."""
    resp = api_client.post("/jobs/audit-repository", json={
        "github_url": "https://github.com/CROO-Network/capscore-agent",
        "run_tests": False,
        "run_security_scan": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["capability"] == "audit_repository"
    assert data["status"] in ("pending", "running", "done")


def test_api_audit_repo_job_id_format(api_client):
    """job_id follows the capscore_YYYYMMDD_HHMMSS_hex8 pattern."""
    import re
    resp = api_client.post("/jobs/audit-repository", json={
        "github_url": "https://github.com/CROO-Network/capscore-agent",
        "run_tests": False,
        "run_security_scan": False,
    })
    data = resp.json()
    assert re.match(r"capscore_\d{8}_\d{6}_[0-9a-f]{8}", data["job_id"])


def test_api_verify_claims_creates_job(api_client):
    """POST /jobs/verify-claims creates a job."""
    resp = api_client.post("/jobs/verify-claims", json={
        "claims": ["This agent works.", "The README is clear."],
        "strictness": "standard",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data


def test_api_audit_agent_creates_job(api_client):
    """POST /jobs/audit-agent creates a job."""
    resp = api_client.post("/jobs/audit-agent", json={
        "agent_listing_url": "https://agent.croo.network/capscore",
        "depth": "quick",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["capability"] == "audit_agent_listing"


def test_api_get_job_after_create(api_client):
    """GET /jobs/{job_id} returns job after creation."""
    create_resp = api_client.post("/jobs/audit-repository", json={
        "github_url": "https://github.com/CROO-Network/capscore-agent",
        "run_tests": False,
        "run_security_scan": False,
    })
    job_id = create_resp.json()["job_id"]
    get_resp = api_client.get(f"/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["job_id"] == job_id


def test_api_get_nonexistent_job(api_client):
    """GET /jobs/nonexistent returns 404."""
    resp = api_client.get("/jobs/nonexistent_job_xyz")
    assert resp.status_code == 404


def test_api_list_jobs_returns_array(api_client):
    """GET /jobs returns an array."""
    resp = api_client.get("/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_api_list_jobs_includes_created_job(api_client):
    """GET /jobs includes a newly created job."""
    create_resp = api_client.post("/jobs/verify-claims", json={
        "claims": ["Test claim for listing."],
    })
    job_id = create_resp.json()["job_id"]
    list_resp = api_client.get("/jobs")
    job_ids = [j["job_id"] for j in list_resp.json()]
    assert job_id in job_ids


def test_api_verify_claims_missing_required_field(api_client):
    """POST /jobs/verify-claims without claims returns 422."""
    resp = api_client.post("/jobs/verify-claims", json={
        "strictness": "standard",
    })
    assert resp.status_code == 422


def test_api_audit_repo_missing_github_url(api_client):
    """POST /jobs/audit-repository without github_url returns 422."""
    resp = api_client.post("/jobs/audit-repository", json={
        "run_tests": False,
    })
    assert resp.status_code == 422
