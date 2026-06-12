from __future__ import annotations
import asyncio
import re
import tempfile
import os
import shutil
from pathlib import Path
from typing import Optional
import subprocess

from ..models import CAPInspectionResult


CAP_INDICATORS = {
    "schema_present": [
        r"capability.*schema", r"input.*schema", r"output.*schema",
        r'"type".*"object"', r"z\.object\(", r"BaseModel",
    ],
    "pricing_defined": [
        r"price", r"pricing", r"cost", r"\$\d", r"usd", r"croo_price",
    ],
    "sla_defined": [
        r"sla", r"timeout", r"max.*second", r"delivery.*time", r"sla_seconds",
    ],
    "proof_delivery": [
        r"proof", r"deliver.*order", r"deliverOrder", r"result_hash",
        r"proof.pack", r"attestation",
    ],
    "output_machine_readable": [
        r"json\.dumps", r"model_dump", r"\.json\(\)", r"application/json",
        r"response_model", r"BaseModel",
    ],
    "callable_by_agents": [
        r"agent.*client", r"AgentClient", r"croo.*sdk", r"@croo",
        r"cap.*order", r"acceptNegotiation",
    ],
    "typed_inputs": [
        r"pydantic", r"zod", r"ajv", r"schema", r"BaseModel",
    ],
    "a2a_dependency": [
        r"call.*agent", r"sub.agent", r"a2a", r"agent.*to.*agent",
        r"hire.*agent", r"call_cap_agent",
    ],
    "failure_documented": [
        r"timeout", r"retry", r"fallback", r"graceful", r"error.*handling",
    ],
    "wallet_setup": [
        r"wallet", r"private.key", r"WALLET", r"croo.*key", r"sdk.key",
    ],
}


async def inspect_cap_integration(github_url: str) -> CAPInspectionResult:
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix="capscore_cap_")
        repo_path = Path(tmpdir) / "repo"

        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth", "1", github_url, str(repo_path),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if not repo_path.exists():
            return CAPInspectionResult(
                checks={k: False for k in CAP_INDICATORS},
                score=0.0,
                issues=[f"Could not clone repository for CAP inspection: {stderr.decode()[:100]}"],
            )

        # Read all text files
        all_text = ""
        for ext in ["*.ts", "*.js", "*.py", "*.json", "*.md", "*.yaml", "*.yml"]:
            for f in repo_path.rglob(ext):
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    all_text += content + "\n"
                except Exception:
                    pass

        all_text_lower = all_text.lower()

        checks: dict[str, bool] = {}
        for check_name, patterns in CAP_INDICATORS.items():
            checks[check_name] = any(
                re.search(p, all_text_lower, re.IGNORECASE) for p in patterns
            )

        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        score = round((passed / total) * 100, 1)

        issues = []
        if not checks.get("schema_present"):
            issues.append("No capability schema found — add input/output JSON schemas")
        if not checks.get("pricing_defined"):
            issues.append("No pricing definition found — add explicit price for CAP listing")
        if not checks.get("proof_delivery"):
            issues.append("No proof-of-delivery code found — add result hash and delivery proof")
        if not checks.get("callable_by_agents"):
            issues.append("CROO SDK usage not detected — ensure the agent is callable via CAP")
        if not checks.get("output_machine_readable"):
            issues.append("Output may not be machine-readable — ensure JSON structured responses")

        return CAPInspectionResult(checks=checks, score=score, issues=issues)

    except asyncio.TimeoutError:
        return CAPInspectionResult(
            checks={k: False for k in CAP_INDICATORS},
            score=0.0,
            issues=["CAP inspection timed out"],
        )
    except Exception as e:
        return CAPInspectionResult(
            checks={k: False for k in CAP_INDICATORS},
            score=0.0,
            issues=[f"CAP inspection error: {str(e)}"],
        )
    finally:
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)
