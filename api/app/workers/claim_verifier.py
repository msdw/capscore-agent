from __future__ import annotations
import asyncio
import json
import os
from typing import List, Optional

import httpx

from ..models import ClaimReport, ClaimVerification
from ..config import settings


async def _fetch_url_content(url: str, timeout: int = 10) -> str:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, follow_redirects=True)
            return resp.text[:5000]
    except Exception:
        return ""


async def _llm_verify_claims(
    claims: List[str],
    evidence_text: str,
    strictness: str,
) -> List[ClaimVerification]:
    """Use Claude to verify claims against evidence."""
    if not settings.anthropic_api_key:
        return _heuristic_verify(claims, evidence_text, strictness)

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

        strictness_instructions = {
            "lenient": "Be lenient — mark claims as supported if there's any plausible basis.",
            "standard": "Be balanced — mark claims supported only if evidence clearly backs them.",
            "strict": "Be strict — only mark supported if evidence explicitly and directly confirms.",
        }

        prompt = f"""You are a claim verification specialist. Analyze each claim against the provided evidence.

Evidence:
{evidence_text[:3000]}

Claims to verify:
{json.dumps(claims, indent=2)}

Strictness: {strictness_instructions[strictness]}

For each claim, return a JSON array with objects having these fields:
- claim: the original claim text
- status: one of "supported", "weak", "unsupported", "misleading"
- evidence: brief description of what evidence was found (or not found)
- confidence: float 0.0-1.0
- suggested_rewrite: a clearer, more accurate version of the claim

Return ONLY valid JSON array, no markdown, no explanation."""

        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()
        # Strip markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        results = json.loads(text)
        verifications = []
        for item in results:
            verifications.append(ClaimVerification(
                claim=item.get("claim", ""),
                status=item.get("status", "unsupported"),
                evidence=item.get("evidence", ""),
                confidence=float(item.get("confidence", 0.5)),
                suggested_rewrite=item.get("suggested_rewrite", ""),
            ))
        return verifications

    except Exception as e:
        # Fallback to heuristic
        return _heuristic_verify(claims, evidence_text, strictness)


def _heuristic_verify(claims: List[str], evidence_text: str, strictness: str) -> List[ClaimVerification]:
    """Simple heuristic verification without LLM."""
    verifications = []
    evidence_lower = evidence_text.lower()

    for claim in claims:
        # Extract key words from the claim
        claim_words = [w.lower() for w in claim.split() if len(w) > 4]
        matches = sum(1 for w in claim_words if w in evidence_lower)
        match_ratio = matches / max(len(claim_words), 1)

        if match_ratio > 0.6:
            status = "supported"
            confidence = 0.7
        elif match_ratio > 0.3:
            status = "weak"
            confidence = 0.4
        else:
            status = "unsupported"
            confidence = 0.2

        if strictness == "strict" and status == "supported":
            status = "weak"
            confidence *= 0.8

        verifications.append(ClaimVerification(
            claim=claim,
            status=status,
            evidence=f"{'Evidence found' if match_ratio > 0.3 else 'No clear evidence found'} in provided URLs.",
            confidence=confidence,
            suggested_rewrite=f"{claim} (verified)" if status == "supported" else claim,
        ))
    return verifications


def _score_claims(verifications: List[ClaimVerification]) -> float:
    if not verifications:
        return 50.0
    status_scores = {"supported": 100, "weak": 60, "unsupported": 20, "misleading": 0}
    avg = sum(status_scores[v.status] for v in verifications) / len(verifications)
    return round(avg, 1)


async def verify_claims(
    claims: List[str],
    evidence_urls: List[str],
    strictness: str = "standard",
) -> ClaimReport:
    if not claims:
        return ClaimReport(verifications=[], score=50.0)

    # Fetch evidence content
    evidence_parts = []
    for url in (evidence_urls or [])[:3]:
        content = await _fetch_url_content(url)
        if content:
            evidence_parts.append(f"=== {url} ===\n{content}")

    evidence_text = "\n\n".join(evidence_parts) if evidence_parts else "No evidence URLs provided."

    verifications = await _llm_verify_claims(claims, evidence_text, strictness)
    score = _score_claims(verifications)

    return ClaimReport(verifications=verifications, score=score)
