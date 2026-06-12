from __future__ import annotations
import asyncio
import re
import tempfile
import os
import shutil
from pathlib import Path
from typing import List
import subprocess

from ..models import SecurityScanResult, SecurityFinding


SECRET_PATTERNS = [
    (r'sk-[A-Za-z0-9]{32,}', "OpenAI API key", "critical"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID", "critical"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub Personal Access Token", "critical"),
    (r'croo_sk_[A-Za-z0-9]{20,}', "CROO SDK Key", "critical"),
    (r'sk-ant-api\d{2}-[A-Za-z0-9\-_]{93,}', "Anthropic API key", "critical"),
    (r'(?i)password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password", "high"),
    (r'(?i)secret\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded secret", "high"),
    (r'(?i)api_key\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded API key", "high"),
    (r'(?i)private_key\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded private key", "critical"),
    (r'0x[a-fA-F0-9]{64}', "Possible private key hex", "high"),
]

DANGEROUS_PATTERNS = [
    (r'curl\s+.*\|\s*(?:bash|sh)', "curl pipe to shell"),
    (r'eval\(.*input', "eval() on user input"),
    (r'exec\(.*request', "exec() on request data"),
    (r'os\.system\(.*input', "os.system() on user input"),
    (r'subprocess\..*shell\s*=\s*True', "subprocess with shell=True"),
    (r'__import__.*input', "__import__() on user input"),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
SKIP_EXTENSIONS = {".pyc", ".jpg", ".png", ".gif", ".ico", ".woff", ".ttf", ".mp4"}


def _should_skip(path: Path) -> bool:
    return (
        any(part in SKIP_DIRS for part in path.parts) or
        path.suffix.lower() in SKIP_EXTENSIONS or
        path.stat().st_size > 1_000_000  # skip files > 1MB
    )


async def scan_security(github_url: str) -> SecurityScanResult:
    tmpdir = None
    findings: List[SecurityFinding] = []
    dangerous_patterns_found: List[str] = []
    unpinned_deps: List[str] = []

    try:
        tmpdir = tempfile.mkdtemp(prefix="capscore_sec_")
        repo_path = Path(tmpdir) / "repo"

        proc = await asyncio.create_subprocess_exec(
            "git", "clone", "--depth", "1", github_url, str(repo_path),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if not repo_path.exists():
            return SecurityScanResult(
                risk_level="low",
                score=100.0,
                findings=[],
                dangerous_patterns=["Could not clone for security scan"],
            )

        # Scan files
        for file_path in repo_path.rglob("*"):
            if not file_path.is_file() or _should_skip(file_path):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                relative = str(file_path.relative_to(repo_path))

                # Skip .env files (expected to have secrets) but flag committed .env
                is_env_file = file_path.name in {".env", ".env.local", ".env.production"}
                if is_env_file and not file_path.name.endswith(".example"):
                    findings.append(SecurityFinding(
                        file=relative, line=0,
                        pattern=".env file committed",
                        severity="critical",
                        description=f"Committed .env file found: {relative}. Remove from git history.",
                    ))

                for pattern, description, severity in SECRET_PATTERNS:
                    for i, line in enumerate(content.split("\n"), 1):
                        if re.search(pattern, line):
                            # Skip if it's clearly a placeholder
                            if any(p in line.lower() for p in ["your_key", "xxx", "placeholder", "example", "changeme", "<"]):
                                continue
                            findings.append(SecurityFinding(
                                file=relative, line=i,
                                pattern=description,
                                severity=severity,
                                description=f"Possible {description} found at {relative}:{i}",
                            ))

                for pattern, description in DANGEROUS_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        dangerous_patterns_found.append(f"{description} in {relative}")

            except Exception:
                pass

        # Check for unpinned dependencies
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            for line in req_file.read_text().split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and ">=" not in line and "==" not in line and "~=" not in line:
                    if line and not line.startswith("-"):
                        unpinned_deps.append(line)

        # Determine risk level
        has_critical = any(f.severity == "critical" for f in findings)
        has_high = any(f.severity == "high" for f in findings)

        if has_critical or len(dangerous_patterns_found) > 2:
            risk_level = "critical"
        elif has_high or dangerous_patterns_found:
            risk_level = "high"
        elif findings:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Score: higher = safer
        deductions = len([f for f in findings if f.severity == "critical"]) * 30
        deductions += len([f for f in findings if f.severity == "high"]) * 15
        deductions += len(dangerous_patterns_found) * 10
        deductions += min(len(unpinned_deps) * 2, 20)
        score = max(0.0, 100.0 - deductions)

        return SecurityScanResult(
            findings=findings[:20],  # cap at 20 findings
            dangerous_patterns=dangerous_patterns_found[:10],
            unpinned_deps=unpinned_deps[:10],
            risk_level=risk_level,
            score=round(score, 1),
        )

    except asyncio.TimeoutError:
        return SecurityScanResult(risk_level="low", score=70.0, findings=[], dangerous_patterns=["Scan timed out"])
    except Exception as e:
        return SecurityScanResult(risk_level="low", score=70.0, findings=[], dangerous_patterns=[f"Scan error: {str(e)}"])
    finally:
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)
