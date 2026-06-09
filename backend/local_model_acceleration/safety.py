"""
Prompt safety filter for the Local Model Acceleration cache.

Determines whether a prompt/response pair is safe to cache.  A response
should NOT be cached if:

  1. The prompt is too long (risk of stale context matching).
  2. The task type is inherently dynamic (live queries, emotional support,
     security decisions) — same question tomorrow ≠ same correct answer.
  3. The prompt contains keywords indicating sensitive credentials, PII, or
     personal financial data — caching these would be a privacy risk.
  4. The caller's metadata explicitly requests cache bypass.

Semantic cache is a Phase 2 concern; ``semantic_cache_allowed()`` always
returns False in Phase 1.
"""
from __future__ import annotations

# Task types that produce non-deterministic or sensitive responses
_UNSAFE_TASK_TYPES: frozenset[str] = frozenset(
    {
        "emotional_chat",
        "emotional_support",
        "medical_advice",
        "legal_advice",
        "financial_advice",
        "live_web",
        "live_search",
        "current_events",
        "security_decision",
        "authentication",
        "credential_handling",
        "realtime",
    }
)

# Substrings that suggest sensitive credential / PII content in the prompt
_SENSITIVE_KEYWORDS: frozenset[str] = frozenset(
    {
        "password",
        "api_key",
        "api key",
        "secret",
        " token",
        "private_key",
        "private key",
        "bearer ",
        "authorization:",
        "ssn",
        "social security",
        "credit card",
        "card number",
        "cvv",
        "passport number",
        "tax id",
    }
)


def should_cache_prompt(
    prompt: str,
    task_type: str,
    metadata: dict | None = None,
    *,
    max_prompt_chars: int = 24_000,
) -> tuple[bool, str | None]:
    """
    Decide whether a prompt is safe and appropriate to cache.

    Returns ``(cacheable, skip_reason)`` where *skip_reason* is ``None``
    when cacheable and a short string explaining the skip otherwise.
    """
    # 1. Prompt length gate
    if len(prompt) > max_prompt_chars:
        return False, "prompt_too_long"

    # 2. Task type gate
    if task_type.lower() in _UNSAFE_TASK_TYPES:
        return False, f"task_type:{task_type}"

    # 3. Sensitive keyword scan (case-insensitive, substring)
    prompt_lower = prompt.lower()
    for kw in _SENSITIVE_KEYWORDS:
        if kw in prompt_lower:
            return False, f"sensitive_keyword:{kw.strip()}"

    # 4. Caller-supplied metadata overrides
    if metadata:
        if metadata.get("no_cache") or metadata.get("cache_policy") == "off":
            return False, "meta:no_cache"
        if metadata.get("contains_sensitive_data"):
            return False, "meta:sensitive_data"

    return True, None


def semantic_cache_allowed() -> bool:
    """
    Return True if semantic (embedding-based) cache lookup is permitted.

    Always False in Phase 1 — the DSQP persona and RAG context mean that
    the same surface query can legitimately produce different correct answers
    on different requests.  A 0.92 cosine threshold is not safe enough to
    avoid false positive cache hits in this architecture.

    Phase 2 will add a per-query similarity gate that compares the RAG
    context hashes before allowing a semantic cache hit.
    """
    return False
