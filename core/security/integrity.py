"""
Deterministic hashing and HMAC signing helpers for snapshot/audit integrity.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any, Iterable, Optional


def canonical_json(payload: Any) -> str:
    """Serialize payload deterministically for hashing/signing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def sha256_hex(payload: Any) -> str:
    """Compute SHA-256 over deterministic JSON representation."""
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def hmac_sha256_hex(payload: Any, secret: str) -> str:
    """Compute HMAC-SHA256 hex digest for payload."""
    secret_bytes = str(secret).encode("utf-8")
    payload_bytes = canonical_json(payload).encode("utf-8")
    return hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()


def verify_hmac_sha256(payload: Any, secret: str, signature: Optional[str]) -> bool:
    """Constant-time verification for HMAC-SHA256 signatures."""
    if not signature:
        return False
    expected = hmac_sha256_hex(payload, secret)
    return hmac.compare_digest(expected, str(signature).strip().lower())


def resolve_hmac_secret(primary_env: str, fallback_envs: Iterable[str] = ()) -> Optional[str]:
    """
    Resolve an HMAC secret from environment variables.

    Returns `None` if no configured value is present.
    """
    candidates = [primary_env, *fallback_envs]
    for env_key in candidates:
        value = os.environ.get(str(env_key), "")
        if value and value.strip():
            return value.strip()
    return None

