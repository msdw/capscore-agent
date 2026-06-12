import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import AuditRepositoryRequest, VerifyClaimsRequest, AuditAgentRequest


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def sample_audit_repo_request():
    return AuditRepositoryRequest(
        github_url="https://github.com/CROO-Network/capscore-agent",
        run_tests=False,
        run_security_scan=False,
    )


@pytest.fixture
def sample_verify_claims_request():
    return VerifyClaimsRequest(
        claims=["This agent provides a working CAP provider.", "The README is clear."],
        evidence_urls=["https://github.com/CROO-Network/capscore-agent"],
        strictness="standard",
    )


@pytest.fixture
def sample_audit_agent_request():
    return AuditAgentRequest(
        agent_listing_url="https://agent.croo.network/capscore",
        github_url="https://github.com/CROO-Network/capscore-agent",
        claimed_tracks=["Data & Verification Agents"],
        depth="quick",
    )
