"""
Shared error normalization for external/API-facing responses.
"""

from __future__ import annotations

from typing import Iterable, Optional


DEFAULT_SAFE_FRAGMENTS = (
    "not allowed",
    "messages required",
    "model required",
    "no active providers found",
    "no provider configured",
    "permission denied",
    "invalid api key",
    "authentication required",
)


def normalize_public_error_message(
    raw_error: Optional[str],
    fallback: str,
    safe_fragments: Iterable[str] = DEFAULT_SAFE_FRAGMENTS,
) -> str:
    """Expose safe/intentional failures while suppressing raw provider internals."""
    if not raw_error:
        return fallback

    lowered = str(raw_error).strip().lower()
    for fragment in safe_fragments:
        if fragment in lowered:
            return str(raw_error)

    return fallback
