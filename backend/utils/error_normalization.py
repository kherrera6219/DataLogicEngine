"""
Shared error normalization for external/API-facing responses.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Optional


DEFAULT_SAFE_FRAGMENTS = {
    "not allowed": "Operation not allowed",
    "messages required": "Messages required",
    "model required": "Model required",
    "no active providers found": "No active providers found",
    "no provider configured": "No provider configured",
    "permission denied": "Permission denied",
    "invalid api key": "Invalid API key",
    "authentication required": "Authentication required",
}


def normalize_public_error_message(
    raw_error: Optional[str],
    fallback: str,
    safe_fragments: Iterable[str] | Mapping[str, str] = DEFAULT_SAFE_FRAGMENTS,
) -> str:
    """Return only canonical public messages, never raw exception text."""
    if not raw_error:
        return fallback

    lowered = str(raw_error).strip().lower()
    canonical_messages = (
        safe_fragments.items()
        if isinstance(safe_fragments, Mapping)
        else (
            (
                fragment,
                DEFAULT_SAFE_FRAGMENTS.get(str(fragment).lower(), str(fragment)),
            )
            for fragment in safe_fragments
        )
    )
    for fragment, public_message in canonical_messages:
        if str(fragment).lower() in lowered:
            return str(public_message)

    return fallback
