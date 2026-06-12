"""
Shared LLM helper with provider fallback.

Order of attempts:
  1. Anthropic (settings.anthropic_model) if ANTHROPIC_API_KEY is set.
  2. OpenAI (settings.openai_model) if OPENAI_API_KEY is set.
  3. Caller's heuristic fallback (returns None here; callers handle None).

This keeps the analysis workers provider-agnostic: they call `complete()`
and fall back to deterministic heuristics only when it returns None.
"""
from __future__ import annotations

from typing import Optional

from .config import settings


async def complete(prompt: str, max_tokens: int = 1000, temperature: float = 0.0) -> Optional[str]:
    """Return model text, or None if no provider is available/working."""
    text = await _try_anthropic(prompt, max_tokens, temperature)
    if text is not None:
        return text
    text = await _try_openai(prompt, max_tokens, temperature)
    if text is not None:
        return text
    return None


async def _try_anthropic(prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
    if not settings.anthropic_api_key:
        return None
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        message = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception:
        # Includes low-credit / auth / rate-limit errors -> fall through.
        return None


async def _try_openai(prompt: str, max_tokens: int, temperature: float) -> Optional[str]:
    if not settings.openai_api_key:
        return None
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            max_completion_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences from a model reply."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if t.count("```") >= 2 else t.lstrip("`")
        if t.startswith("json"):
            t = t[4:]
    return t.strip()
