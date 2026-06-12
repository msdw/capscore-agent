from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from .models import A2ACall


MOCK_AGENTS = {
    "source-verifier-mock": {
        "url": None,  # None = use local mock
        "capabilities": ["verify_sources"],
    },
    "security-auditor-mock": {
        "url": None,
        "capabilities": ["scan_dependencies"],
    },
}


async def call_cap_agent(
    provider_agent: str,
    capability: str,
    payload: Dict[str, Any],
    timeout: int = 60,
) -> A2ACall:
    """Call another CAP agent. Falls back to local mock if no URL configured."""
    call = A2ACall(
        provider_agent=provider_agent,
        cap_order_id=f"mock_order_{hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:8]}",
        task=capability,
        status="pending",
    )

    agent_info = MOCK_AGENTS.get(provider_agent, {})
    agent_url = agent_info.get("url") or os.getenv(f"A2A_{provider_agent.upper().replace('-', '_')}_URL")

    if agent_url:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(f"{agent_url}/jobs/{capability}", json=payload)
                resp.raise_for_status()
                result = resp.json()
                call.result_hash = result.get("result_hash", "")
                call.status = "cleared"
                call.completed_at = datetime.now(timezone.utc)
        except Exception as e:
            call.status = f"failed: {e}"
            call.completed_at = datetime.now(timezone.utc)
    else:
        # Local mock: simulate a successful call
        mock_result = _mock_agent_result(provider_agent, capability, payload)
        call.result_hash = f"sha256:{hashlib.sha256(json.dumps(mock_result, sort_keys=True).encode()).hexdigest()}"
        call.status = "cleared"
        call.completed_at = datetime.now(timezone.utc)

    return call


def _mock_agent_result(provider_agent: str, capability: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return a mock result for development/demo purposes."""
    if "source-verifier" in provider_agent:
        return {
            "verified_urls": payload.get("evidence_urls", []),
            "reachable": len(payload.get("evidence_urls", [])),
            "summary": "All provided URLs are reachable and contain relevant content.",
        }
    elif "security-auditor" in provider_agent:
        return {
            "dependencies_scanned": 0,
            "vulnerabilities": [],
            "summary": "No known vulnerabilities detected in dependency list.",
        }
    return {"status": "ok", "message": f"Mock result from {provider_agent}"}
