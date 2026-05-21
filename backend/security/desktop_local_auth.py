"""
Desktop localhost auth helpers.

Implements a per-install secret and one-time challenge/response nonce flow
for desktop loopback authentication endpoints.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path
from typing import MutableMapping, Tuple
from urllib.parse import urlsplit


DESKTOP_NONCE_SESSION_KEY = "desktop_auth_nonce"
DESKTOP_NONCE_EXPIRES_SESSION_KEY = "desktop_auth_nonce_expires_at"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_secret_file() -> Path:
    return _repo_root() / "instance" / "desktop_install_secret.txt"


def _nonce_ttl_seconds() -> int:
    raw = os.environ.get("DESKTOP_AUTH_NONCE_TTL_SECONDS", "90")
    try:
        ttl = int(raw)
    except (TypeError, ValueError):
        ttl = 90
    return max(30, min(ttl, 300))


def get_or_create_install_secret() -> str:
    """Resolve install secret from env or local secret file."""
    env_secret = (os.environ.get("DESKTOP_INSTALL_SECRET") or "").strip()
    if env_secret:
        return env_secret

    secret_file = Path(os.environ.get("DESKTOP_INSTALL_SECRET_FILE") or _default_secret_file())
    secret_file.parent.mkdir(parents=True, exist_ok=True)

    if secret_file.exists():
        existing = secret_file.read_text(encoding="utf-8").strip()
        if existing:
            return existing

    generated = secrets.token_hex(32)
    secret_file.write_text(generated, encoding="utf-8")
    try:
        os.chmod(secret_file, 0o600)
    except OSError:
        # File mode hardening is best-effort on platforms that support chmod.
        pass
    return generated


def build_desktop_auth_signature(nonce: str, install_secret: str) -> str:
    """Create deterministic HMAC signature for desktop challenge nonce."""
    return hmac.new(
        install_secret.encode("utf-8"),
        nonce.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def build_desktop_request_signature(
    method: str,
    full_path: str,
    timestamp: str,
    install_secret: str,
) -> str:
    """Create HMAC signature for a desktop loopback API request."""
    parsed = urlsplit(full_path)
    path_with_query = parsed.path or full_path or "/"
    if parsed.query:
        path_with_query = f"{path_with_query}?{parsed.query}"
    payload = f"{method.upper()}\n{path_with_query}\n{timestamp}"
    return hmac.new(
        install_secret.encode("utf-8"),
        payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def verify_desktop_request_signature(
    *,
    method: str,
    full_path: str,
    timestamp: str,
    signature: str,
    install_secret: str,
) -> Tuple[bool, str]:
    """Validate signed per-request desktop auth headers."""
    if not timestamp:
        return False, "Desktop auth timestamp required"
    if not signature:
        return False, "Desktop request signature required"

    try:
        timestamp_seconds = int(timestamp)
    except (TypeError, ValueError):
        return False, "Desktop auth timestamp invalid"

    max_skew_seconds = int(os.environ.get("DESKTOP_AUTH_MAX_SKEW_SECONDS", "300"))
    if abs(int(time.time()) - timestamp_seconds) > max(30, min(max_skew_seconds, 900)):
        return False, "Desktop auth timestamp expired"

    expected_signature = build_desktop_request_signature(
        method=method,
        full_path=full_path,
        timestamp=timestamp,
        install_secret=install_secret,
    )
    if not hmac.compare_digest(signature, expected_signature):
        return False, "Desktop request signature invalid"

    return True, ""


def issue_desktop_auth_challenge(session_obj: MutableMapping[str, object]) -> Tuple[str, int]:
    """Issue one-time nonce and persist it in the current session."""
    nonce = secrets.token_urlsafe(32)
    ttl_seconds = _nonce_ttl_seconds()
    session_obj[DESKTOP_NONCE_SESSION_KEY] = nonce
    session_obj[DESKTOP_NONCE_EXPIRES_SESSION_KEY] = int(time.time()) + ttl_seconds
    return nonce, ttl_seconds


def verify_desktop_auth_challenge(
    session_obj: MutableMapping[str, object],
    nonce: str,
    signature: str,
    install_secret: str,
) -> Tuple[bool, str]:
    """
    Validate nonce + signature against one-time session challenge.

    Challenge is invalidated regardless of outcome to prevent replay attempts.
    """
    expected_nonce = str(session_obj.get(DESKTOP_NONCE_SESSION_KEY) or "")
    expires_at_raw = session_obj.get(DESKTOP_NONCE_EXPIRES_SESSION_KEY)

    session_obj.pop(DESKTOP_NONCE_SESSION_KEY, None)
    session_obj.pop(DESKTOP_NONCE_EXPIRES_SESSION_KEY, None)

    if not nonce:
        return False, "Desktop auth nonce required"
    if not signature:
        return False, "Desktop auth signature required"
    if not expected_nonce:
        return False, "Desktop auth challenge missing or already consumed"

    try:
        expires_at = int(expires_at_raw) if expires_at_raw is not None else 0
    except (TypeError, ValueError):
        expires_at = 0

    if expires_at <= int(time.time()):
        return False, "Desktop auth challenge expired"

    if not hmac.compare_digest(nonce, expected_nonce):
        return False, "Desktop auth nonce mismatch"

    expected_signature = build_desktop_auth_signature(nonce, install_secret)
    if not hmac.compare_digest(signature, expected_signature):
        return False, "Desktop auth signature invalid"

    return True, ""
