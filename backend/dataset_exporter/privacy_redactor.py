"""Privacy, Secret Redactor, and Input Sanitizer for dataset exporting.

Scrubs API keys, bearer tokens, credentials, PII patterns, prompt injection markers,
and path traversal inputs prior to dataset export.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_SECRET_KEY_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{32,}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
    re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|auth[_-]?token)\b\s*[:=]\s*['\"]?([^\s,;'\"}]+)['\"]?"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"),
]

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?prior\s+(?:instructions|prompts)", re.IGNORECASE),
    re.compile(r"<\|(?:system|developer|assistant|user)\|>", re.IGNORECASE),
]

_PATH_TRAVERSAL_PATTERN = re.compile(r"(?:\.\.[\\/]|[\\/]\.\.)")


class PrivacyRedactor:
    """Scrubs sensitive strings, sanitizes paths, and handles malformed data structures."""

    @classmethod
    def redact_text(cls, text: str) -> str:
        """Redact known secrets, PII patterns, and control markers from a raw string."""
        if not text or not isinstance(text, str):
            return text if isinstance(text, str) else ""

        scrubbed = text

        for pattern in _SECRET_KEY_PATTERNS:
            scrubbed = pattern.sub("[REDACTED_SECRET]", scrubbed)

        for pattern in _INJECTION_PATTERNS:
            scrubbed = pattern.sub("[REDACTED_INJECTION_PATTERN]", scrubbed)

        return scrubbed

    @classmethod
    def redact_data(cls, data: Any) -> Any:
        """Recursively redact strings within dicts, lists, and primitives with null safety."""
        if data is None:
            return None
        if isinstance(data, str):
            return cls.redact_text(data)
        if isinstance(data, dict):
            return {str(key): cls.redact_data(val) for key, val in data.items()}
        if isinstance(data, list):
            return [cls.redact_data(item) for item in data]
        if isinstance(data, (tuple, set)):
            return [cls.redact_data(item) for item in data]
        return data

    @classmethod
    def validate_safe_path(cls, path_str: str | Path, base_dir: str | Path = "./datasets") -> Path:
        """Resolve an output path and require it to remain below ``base_dir``."""
        if not path_str:
            raise ValueError("Output path cannot be empty.")

        raw_path = Path(path_str).expanduser()
        base_obj = Path(base_dir).expanduser().resolve()
        if _PATH_TRAVERSAL_PATTERN.search(str(path_str)):
            raise SecurityError("Output path contains a traversal segment.")

        path_obj = raw_path.resolve() if raw_path.is_absolute() else (base_obj / raw_path).resolve()
        try:
            relative_path = path_obj.relative_to(base_obj)
        except ValueError as exc:
            raise SecurityError("Output path is outside the approved dataset directory.") from exc

        if not relative_path.parts:
            raise ValueError("Output path must identify a file below the dataset directory.")

        return path_obj


class SecurityError(Exception):
    """Raised when a security policy or validation rule is violated."""
