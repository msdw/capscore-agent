"""
Worker: README Rewriter
Uses Claude (or heuristics) to suggest targeted improvements to a project's README
based on the repository analysis results.
"""
from __future__ import annotations
import asyncio
import json
from typing import List, Optional

import httpx

from ..config import settings
from ..models import ReproResult


async def _fetch_readme(github_url: str, timeout: int = 10) -> str:
    """Fetch raw README content from GitHub."""
    # Normalize URL: https://github.com/owner/repo -> raw content URL
    url = github_url.rstrip("/")
    owner_repo = url.replace("https://github.com/", "")
    for branch in ("main", "master"):
        raw_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/README.md"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(raw_url)
                if resp.status_code == 200:
                    return resp.text[:4000]
        except Exception:
            pass
    return ""


async def _llm_suggest_readme_fixes(
    readme_content: str,
    repo_result: Optional[ReproResult],
    github_url: str,
) -> List[str]:
    """Use Claude to generate targeted README improvement suggestions."""
    if not settings.anthropic_api_key:
        return _heuristic_readme_suggestions(readme_content, repo_result)

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        issues_summary = ""
        if repo_result:
            missing = [k for k, v in repo_result.files_present.items() if not v]
            issues_summary = f"\nRepository issues detected: {', '.join(repo_result.issues[:5])}\nMissing files: {', '.join(missing[:5])}"

        readme_excerpt = readme_content[:2000] if readme_content else "(No README found)"

        prompt = f"""You are a technical writer helping an AI agent developer improve their README for the CROO Agent Store.

Repository: {github_url}{issues_summary}

Current README (truncated):
{readme_excerpt}

Generate exactly 5 concrete, actionable suggestions to improve this README for:
1. Agent marketplace buyers who need to quickly understand what the agent does and how to use it
2. CROO hackathon judges evaluating technical execution and adoption readiness
3. Other AI agents that may want to call this agent via CAP protocol

Format as a JSON array of strings, each suggestion being 1-2 sentences. Focus on:
- Missing quickstart/installation instructions
- Unclear or missing input/output examples
- Missing pricing or SLA information for CAP buyers
- Missing environment variable documentation
- Poor explanation of the agent's unique value proposition

Return ONLY a valid JSON array of 5 strings, no markdown, no explanation."""

        message = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        suggestions = json.loads(text)
        return [str(s) for s in suggestions[:5]]

    except Exception:
        return _heuristic_readme_suggestions(readme_content, repo_result)


def _heuristic_readme_suggestions(
    readme_content: str,
    repo_result: Optional[ReproResult],
) -> List[str]:
    """Generate README suggestions without LLM."""
    suggestions = []
    content_lower = readme_content.lower() if readme_content else ""

    if not readme_content:
        return [
            "Add a README.md — this is the first thing judges and buyers will read.",
            "Include a one-sentence description of what the agent does and what problem it solves.",
            "Add a 'Quick Start' section with copy-paste installation commands.",
            "Document all required environment variables with descriptions (no real values).",
            "Add an example input and output to show what the agent produces.",
        ]

    if "quick start" not in content_lower and "quickstart" not in content_lower and "getting started" not in content_lower:
        suggestions.append(
            "Add a 'Quick Start' section with step-by-step commands so buyers can get running in under 5 minutes."
        )

    if "example" not in content_lower and "sample" not in content_lower:
        suggestions.append(
            "Include a concrete input/output example so buyers understand exactly what to send and what they'll receive."
        )

    if "price" not in content_lower and "cost" not in content_lower and "croo" not in content_lower:
        suggestions.append(
            "Add a 'Pricing' section documenting the cost per call and any SLA guarantees for CAP marketplace buyers."
        )

    if ".env" not in content_lower and "environment" not in content_lower:
        suggestions.append(
            "Add an 'Environment Variables' section listing all required variables — ideally referencing .env.example."
        )

    if repo_result and not repo_result.files_present.get("docker-compose.yml", False):
        suggestions.append(
            "Add docker-compose.yml and document Docker-based setup in the README for reproducible one-command startup."
        )

    if len(suggestions) < 5:
        suggestions.append(
            "Add a badge section (CI status, version, license) at the top to signal project maturity to evaluators."
        )

    if len(suggestions) < 5:
        suggestions.append(
            "Add a 'How It Works' section with a short architecture diagram or flowchart showing the agent's decision flow."
        )

    return suggestions[:5]


async def suggest_readme_fixes(
    github_url: str,
    repo_result: Optional[ReproResult] = None,
) -> List[str]:
    """
    Analyse the project README and return up to 5 targeted improvement suggestions.
    Uses Claude if ANTHROPIC_API_KEY is set, otherwise falls back to heuristics.
    """
    readme_content = await _fetch_readme(github_url)
    suggestions = await _llm_suggest_readme_fixes(readme_content, repo_result, github_url)
    return suggestions
