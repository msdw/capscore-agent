from __future__ import annotations
import asyncio
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import subprocess

from ..models import ReproResult, CheckResult
from ..config import settings


STACK_INDICATORS = {
    "python": ["requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"],
    "node": ["package.json", "yarn.lock", "pnpm-lock.yaml"],
    "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    "go": ["go.mod", "go.sum"],
    "rust": ["Cargo.toml", "Cargo.lock"],
}

KEY_FILES = [
    "README.md", "README.rst", ".env.example", ".env.sample",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    ".github/workflows/", "tests/", "test/", "spec/",
    "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md",
]


def _detect_stack(repo_path: Path) -> str:
    for stack, indicators in STACK_INDICATORS.items():
        if any((repo_path / f).exists() for f in indicators):
            return stack
    return "unknown"


def _check_files(repo_path: Path) -> dict[str, bool]:
    result = {}
    for f in KEY_FILES:
        p = repo_path / f
        result[f] = p.exists()
    return result


def _parse_readme_commands(readme_path: Path) -> list[str]:
    if not readme_path.exists():
        return []
    text = readme_path.read_text(encoding="utf-8", errors="ignore")
    # Extract code blocks
    commands = re.findall(r"```(?:bash|sh|shell|zsh)?\n(.*?)```", text, re.DOTALL)
    lines = []
    for block in commands:
        for line in block.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines[:20]  # limit


def _score_from_files(files_present: dict[str, bool]) -> float:
    weights = {
        "README.md": 20,
        ".env.example": 15,
        "docker-compose.yml": 15,
        "Dockerfile": 10,
        "tests/": 15,
        ".github/workflows/": 10,
        "LICENSE": 5,
        ".env.sample": 5,
    }
    total_weight = sum(weights.values())
    score = sum(w for k, w in weights.items() if files_present.get(k, False))
    return round((score / total_weight) * 100, 1)


async def reproduce_repository(github_url: str, branch: str = "main") -> ReproResult:
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix="capscore_repo_")
        repo_path = Path(tmpdir) / "repo"

        # Clone (shallow, no history needed)
        clone_result = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "git", "clone", "--depth", "1", "--branch", branch,
                github_url, str(repo_path),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            ),
            timeout=60,
        )
        stdout, stderr = await clone_result.communicate()

        if clone_result.returncode != 0:
            # Try without branch spec (might be main/master ambiguity)
            clone_result2 = await asyncio.create_subprocess_exec(
                "git", "clone", "--depth", "1",
                github_url, str(repo_path),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            stdout2, stderr2 = await clone_result2.communicate()
            if clone_result2.returncode != 0:
                return ReproResult(
                    stack_detected="unknown",
                    reproducible=False,
                    score=0.0,
                    issues=[f"Could not clone repository: {stderr.decode()[:200]}"],
                    suggestions=["Ensure the repository is public and the URL is correct"],
                )

        # Analyze
        stack = _detect_stack(repo_path)
        files_present = _check_files(repo_path)
        score = _score_from_files(files_present)
        reproducible = score >= 40

        issues = []
        suggestions = []

        if not files_present.get("README.md"):
            issues.append("README.md is missing")
            suggestions.append("Add a README.md with installation and usage instructions")
        if not files_present.get(".env.example"):
            issues.append(".env.example is missing — buyers cannot configure without seeing required variables")
            suggestions.append("Add .env.example with all required environment variables (no real values)")
        if not files_present.get("docker-compose.yml"):
            issues.append("docker-compose.yml is missing — setup reproducibility cannot be verified")
            suggestions.append("Add docker-compose.yml so the project can be started with a single command")
        if not files_present.get("tests/") and not files_present.get("test/"):
            issues.append("No tests/ directory found")
            suggestions.append("Add tests/ directory with at least one test")
        if not files_present.get(".github/workflows/"):
            issues.append("No CI workflow found")
            suggestions.append("Add .github/workflows/ci.yml to run tests automatically")
        if not files_present.get("LICENSE"):
            issues.append("No LICENSE file found")
            suggestions.append("Add an MIT or Apache 2.0 LICENSE file")

        checks = [
            CheckResult(name=k, passed=v, note=f"{'Found' if v else 'Missing'}: {k}")
            for k, v in files_present.items()
        ]

        return ReproResult(
            stack_detected=stack,
            files_present=files_present,
            reproducible=reproducible,
            score=score,
            issues=issues,
            suggestions=suggestions,
            checks=checks,
        )
    except asyncio.TimeoutError:
        return ReproResult(
            reproducible=False,
            score=0.0,
            issues=["Repository clone timed out (>60s)"],
            suggestions=["Ensure the repository is accessible and not too large"],
        )
    except Exception as e:
        return ReproResult(
            reproducible=False,
            score=0.0,
            issues=[f"Error during repository analysis: {str(e)}"],
            suggestions=["Check that the GitHub URL is valid and the repository is public"],
        )
    finally:
        if tmpdir and os.path.exists(tmpdir):
            shutil.rmtree(tmpdir, ignore_errors=True)
