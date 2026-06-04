"""
Core security utilities.

Pure, dependency-free integrity helpers (deterministic hashing and HMAC
signing) used by the core domain layer. Lives in ``core/`` so domain modules
do not need to import from ``backend/`` (preserving the documented
``backend -> core`` dependency direction).
"""

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
