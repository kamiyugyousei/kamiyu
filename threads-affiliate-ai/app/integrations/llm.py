"""LLM wrapper (OpenAI) with a deterministic template fallback.

If OPENAI_API_KEY is unset, `complete()` returns "" and callers use their own
rule-based generation so the system remains fully functional offline.
"""
from __future__ import annotations

from typing import Optional

from app.config import settings


def complete(prompt: str, system: Optional[str] = None, temperature: float = 0.8) -> str:
    """Return an LLM completion, or "" when no key is configured / on error."""
    if not settings.llm_enabled:
        return ""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=temperature,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:  # pragma: no cover - network dependent
        return ""
