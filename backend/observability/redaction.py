"""Dependency-light redaction primitives for local observability artifacts."""

from __future__ import annotations

import re
from typing import Any

PII_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b(?:\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "ip_address": re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"),
}
SECRET_PATTERNS = (
    (re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]{8,}"), r"\1[REDACTED_SECRET]"),
    (
        re.compile(
            r"(?i)\b((?:api[_-]?key|token|secret|password|authorization|cookie|private[_-]?key)"
            r"\s*[:=]\s*)[^\s,;]+"
        ),
        r"\1[REDACTED_SECRET]",
    ),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"), "[REDACTED_SECRET]"),
    (re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"), "[REDACTED_SECRET]"),
    (re.compile(r"\bukg_[A-Za-z0-9_-]{16,}\b"), "[REDACTED_SECRET]"),
)
SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(password|secret|token|api[_-]?key|authorization|cookie|private[_-]?key)"
)


def is_sensitive_key(key: object) -> bool:
    return bool(SENSITIVE_KEY_PATTERN.search(str(key)))


def redact_text(value: str) -> str:
    """Redact common PII and secret forms without logging or external state."""
    if not isinstance(value, str):
        return value
    redacted = value
    for pii_type, pattern in PII_PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{pii_type.upper()}]", redacted)
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_value(value: Any) -> Any:
    """Recursively redact strings and values held under secret-named keys."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {
            key: "[REDACTED_SECRET]" if is_sensitive_key(key) else redact_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact_value(item) for item in value]
    return value
