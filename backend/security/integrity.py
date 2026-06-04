"""
Backwards-compatible re-export shim for integrity helpers.

The implementation moved to ``core.security.integrity`` so that core domain
modules (``core/simulation/trace_system.py``, ``core/system/frost_service.py``)
no longer import from ``backend/``, preserving the documented
``backend -> core`` dependency direction.

Existing imports from ``backend.security.integrity`` continue to work
unchanged.
"""

from __future__ import annotations

from core.security.integrity import (
    canonical_json,
    hmac_sha256_hex,
    resolve_hmac_secret,
    sha256_hex,
    verify_hmac_sha256,
)

__all__ = [
    "canonical_json",
    "hmac_sha256_hex",
    "resolve_hmac_secret",
    "sha256_hex",
    "verify_hmac_sha256",
]
