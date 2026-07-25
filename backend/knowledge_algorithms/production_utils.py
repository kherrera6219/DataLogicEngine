"""Small deterministic utilities shared by production Knowledge Algorithms."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]{1,}", re.IGNORECASE)


def load_config(module_file: str, filename: str) -> dict[str, Any]:
    path = Path(module_file).resolve().with_name("config") / filename
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def stable_identifier(prefix: str, payload: Any, *, length: int = 16) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def normalized_tokens(value: Any) -> set[str]:
    return {
        match.group(0).lower()
        for match in TOKEN_RE.finditer(str(value or ""))
        if len(match.group(0)) > 1
    }


def overlap_ratio(expected: set[str], actual: set[str]) -> float:
    if not expected:
        return 1.0
    return round(len(expected & actual) / len(expected), 6)
