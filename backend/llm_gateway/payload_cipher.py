"""Authenticated encryption for durable gateway request and result payloads."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from backend.security.dpapi_store import decrypt_data, encrypt_data, is_available


def _fallback_cipher() -> Fernet:
    secret = (
        os.environ.get("ENCRYPTION_KEK_SECRET")
        or os.environ.get("SESSION_SECRET")
        or os.environ.get("FLASK_SECRET_KEY")
    )
    production_desktop = (
        os.environ.get("FLASK_ENV", "").lower() == "production"
        and os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"
    )
    if production_desktop or not secret:
        raise RuntimeError("DPAPI is required for production gateway job payloads")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_payload(payload: dict[str, Any]) -> tuple[str, str]:
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    if is_available():
        ciphertext = encrypt_data(serialized)
        if not ciphertext:
            raise RuntimeError("DPAPI gateway payload encryption failed")
        return "dpapi:v1", ciphertext
    return "fernet:v1", _fallback_cipher().encrypt(serialized.encode("utf-8")).decode("ascii")


def decrypt_payload(encryption: str, ciphertext: str) -> dict[str, Any]:
    if encryption == "dpapi:v1":
        serialized = decrypt_data(ciphertext)
        if not serialized:
            raise ValueError("DPAPI gateway payload decryption failed")
    elif encryption == "fernet:v1":
        try:
            serialized = _fallback_cipher().decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Gateway payload authentication failed") from exc
    else:
        raise ValueError("Unsupported gateway payload encryption")
    payload = json.loads(serialized)
    if not isinstance(payload, dict):
        raise ValueError("Gateway payload is not an object")
    return payload
