"""
Trace export authenticity protection helpers.

Adds deterministic hashing, optional HMAC signing, and optional payload
encryption for evidence export bundles.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any, Dict

from backend.security.integrity import (
    canonical_json,
    hmac_sha256_hex,
    resolve_hmac_secret,
    sha256_hex,
)

try:
    from cryptography.fernet import Fernet
except Exception:  # pragma: no cover - optional dependency guard
    Fernet = None


def _resolve_export_hmac_secret() -> str | None:
    return resolve_hmac_secret("TRACE_EXPORT_HMAC_SECRET", ("SESSION_SECRET",))


def _resolve_export_encryption_key() -> str | None:
    raw = os.environ.get("TRACE_EXPORT_FERNET_KEY") or os.environ.get("TRACE_EXPORT_ENCRYPTION_KEY")
    if not raw:
        return None
    value = str(raw).strip()
    return value or None


def _build_section_hashes(bundle: Dict[str, Any]) -> Dict[str, str]:
    section_hashes: Dict[str, str] = {}
    for key, value in bundle.items():
        if value is None:
            continue
        if value == [] or value == {}:
            continue
        section_hashes[str(key)] = sha256_hex(value)
    return section_hashes


def build_trace_export_document(
    bundle: Dict[str, Any],
    *,
    exported_by: str,
    sign_bundle: bool = True,
    encrypt_bundle: bool = False,
) -> Dict[str, Any]:
    """
    Build a protected export document for trace bundles.
    """
    section_hashes = _build_section_hashes(bundle)
    bundle_hash = sha256_hex(bundle)
    manifest: Dict[str, Any] = {
        "exported_at": datetime.now(UTC).isoformat(),
        "exported_by": exported_by,
        "version": "1.1",
        "hash_algorithm": "sha256",
        "bundle_hash": bundle_hash,
        "section_hashes": section_hashes,
    }

    hmac_secret = _resolve_export_hmac_secret() if sign_bundle else None
    if sign_bundle and hmac_secret:
        manifest["signature_algorithm"] = "hmac-sha256"
        manifest["bundle_signature"] = hmac_sha256_hex(bundle, hmac_secret)
    else:
        manifest["signature_algorithm"] = "none"

    if not encrypt_bundle:
        manifest["encrypted"] = False
        return {
            "manifest": manifest,
            "bundle": bundle,
        }

    encryption_key = _resolve_export_encryption_key()
    if not encryption_key:
        raise ValueError("TRACE_EXPORT_FERNET_KEY (or TRACE_EXPORT_ENCRYPTION_KEY) is required when encrypt_bundle=true")
    if Fernet is None:
        raise ValueError("cryptography.fernet is unavailable; cannot encrypt export payload")

    payload_plaintext = canonical_json(bundle).encode("utf-8")
    encrypted_payload = Fernet(encryption_key.encode("utf-8")).encrypt(payload_plaintext).decode("utf-8")
    envelope = {
        "manifest": {
            **manifest,
            "encrypted": True,
            "encryption_algorithm": "fernet",
        },
        "payload_encrypted": encrypted_payload,
    }
    envelope["manifest"]["envelope_hash"] = sha256_hex(envelope)
    if sign_bundle and hmac_secret:
        envelope["manifest"]["envelope_signature"] = hmac_sha256_hex(envelope, hmac_secret)
    return envelope
