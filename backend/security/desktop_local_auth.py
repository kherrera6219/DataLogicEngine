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
from threading import Lock
from typing import MutableMapping, Tuple
from urllib.parse import urlsplit


DESKTOP_NONCE_SESSION_KEY = "desktop_auth_nonce"
DESKTOP_NONCE_EXPIRES_SESSION_KEY = "desktop_auth_nonce_expires_at"
_ISSUED_DESKTOP_NONCES: dict[str, int] = {}
_ISSUED_DESKTOP_NONCES_LOCK = Lock()
_CONSUMED_REQUEST_NONCES: dict[str, int] = {}
_CONSUMED_REQUEST_NONCES_LOCK = Lock()
_INSTALL_SECRET_CACHE: str | None = None
_INSTALL_SECRET_CACHE_LOCK = Lock()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_secret_file() -> Path:
    return _repo_root() / "instance" / "desktop_install_secret.dpapi"


def _nonce_ttl_seconds() -> int:
    raw = os.environ.get("DESKTOP_AUTH_NONCE_TTL_SECONDS", "90")
    try:
        ttl = int(raw)
    except (TypeError, ValueError):
        ttl = 90
    return max(30, min(ttl, 300))


def _secret_rotation_days() -> int:
    raw = os.environ.get("DESKTOP_INSTALL_SECRET_ROTATION_DAYS", "180")
    try:
        days = int(raw)
    except (TypeError, ValueError):
        days = 180
    return max(30, min(days, 365))


def _secret_file_expired(secret_file: Path) -> bool:
    try:
        age_seconds = max(0.0, time.time() - secret_file.stat().st_mtime)
    except OSError:
        return True
    return age_seconds >= _secret_rotation_days() * 24 * 60 * 60


def get_or_create_install_secret() -> str:
    """Resolve the desktop secret from process handoff or DPAPI storage."""
    global _INSTALL_SECRET_CACHE

    env_secret = (os.environ.get("DESKTOP_INSTALL_SECRET") or "").strip()
    if env_secret:
        return env_secret

    secret_file = Path(os.environ.get("DESKTOP_INSTALL_SECRET_FILE") or _default_secret_file())
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    from backend.security import dpapi_store
    from backend.security.windows_acl import ensure_restricted_user_acl

    production_desktop = (
        os.environ.get("FLASK_ENV", "").lower() == "production"
        and os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"
    )

    with _INSTALL_SECRET_CACHE_LOCK:
        if _INSTALL_SECRET_CACHE:
            return _INSTALL_SECRET_CACHE

        if secret_file.exists() and not _secret_file_expired(secret_file):
            ensure_restricted_user_acl(secret_file, required=production_desktop)
            encrypted = secret_file.read_text(encoding="utf-8").strip()
            existing = dpapi_store.decrypt_data(encrypted)
            if not existing:
                raise RuntimeError("Desktop install secret could not be decrypted")
            _INSTALL_SECRET_CACHE = existing
            return existing

        generated = secrets.token_hex(32)
        encrypted = dpapi_store.encrypt_data(generated)
        if not encrypted:
            if production_desktop or os.environ.get("FLASK_ENV", "").lower() == "production":
                raise RuntimeError("DPAPI is required for the production desktop install secret")
            _INSTALL_SECRET_CACHE = generated
            return generated

        secret_file.write_text(encrypted, encoding="utf-8")
        try:
            os.chmod(secret_file, 0o600)
        except OSError:
            pass
        ensure_restricted_user_acl(secret_file, required=production_desktop)
        _INSTALL_SECRET_CACHE = generated
        return generated


def _remember_issued_nonce(nonce: str, expires_at: int) -> None:
    now = int(time.time())
    with _ISSUED_DESKTOP_NONCES_LOCK:
        expired = [key for key, expiry in _ISSUED_DESKTOP_NONCES.items() if expiry <= now]
        for key in expired:
            _ISSUED_DESKTOP_NONCES.pop(key, None)
        _ISSUED_DESKTOP_NONCES[nonce] = expires_at


def _consume_issued_nonce(nonce: str) -> int | None:
    if not nonce:
        return None
    with _ISSUED_DESKTOP_NONCES_LOCK:
        return _ISSUED_DESKTOP_NONCES.pop(nonce, None)


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
    request_nonce: str = "",
) -> str:
    """Create HMAC signature for a desktop loopback API request."""
    parsed = urlsplit(full_path)
    path_with_query = parsed.path or full_path or "/"
    if parsed.query:
        path_with_query = f"{path_with_query}?{parsed.query}"
    payload = f"{method.upper()}\n{path_with_query}\n{timestamp}"
    if request_nonce:
        payload = f"{payload}\n{request_nonce}"
    return hmac.new(
        install_secret.encode("utf-8"),
        payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def build_desktop_ipc_signature(
    method: str,
    full_path: str,
    timestamp: str,
    capability: str,
    install_secret: str,
    request_nonce: str = "",
) -> str:
    """Bind a main-process-only IPC capability to a signed backend request."""
    parsed = urlsplit(full_path)
    path_with_query = parsed.path or full_path or "/"
    if parsed.query:
        path_with_query = f"{path_with_query}?{parsed.query}"
    payload = f"{method.upper()}\n{path_with_query}\n{timestamp}"
    if request_nonce:
        payload = f"{payload}\n{request_nonce}"
    payload = f"{payload}\nipc:{capability}"
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
    request_nonce: str = "",
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

    production_desktop = (
        os.environ.get("FLASK_ENV", "").lower() == "production"
        and os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"
    )
    if production_desktop and not request_nonce:
        return False, "Desktop request nonce required"
    if request_nonce and (len(request_nonce) < 16 or len(request_nonce) > 128):
        return False, "Desktop request nonce invalid"

    expected_signature = build_desktop_request_signature(
        method=method,
        full_path=full_path,
        timestamp=timestamp,
        install_secret=install_secret,
        request_nonce=request_nonce,
    )
    if not hmac.compare_digest(signature, expected_signature):
        return False, "Desktop request signature invalid"

    if request_nonce:
        now = int(time.time())
        expires_at = now + max(30, min(max_skew_seconds, 900))
        with _CONSUMED_REQUEST_NONCES_LOCK:
            expired = [nonce for nonce, expiry in _CONSUMED_REQUEST_NONCES.items() if expiry <= now]
            for nonce in expired:
                _CONSUMED_REQUEST_NONCES.pop(nonce, None)
            if request_nonce in _CONSUMED_REQUEST_NONCES:
                return False, "Desktop request replay detected"
            _CONSUMED_REQUEST_NONCES[request_nonce] = expires_at

    return True, ""


def verify_desktop_ipc_signature(
    *,
    method: str,
    full_path: str,
    timestamp: str,
    capability: str,
    signature: str,
    install_secret: str,
    request_nonce: str = "",
) -> Tuple[bool, str]:
    """Validate the additional signature emitted only by Electron's main process."""
    if not capability:
        return False, "Desktop IPC capability required"
    if not signature:
        return False, "Desktop IPC signature required"
    try:
        timestamp_seconds = int(timestamp)
    except (TypeError, ValueError):
        return False, "Desktop IPC timestamp invalid"
    max_skew_seconds = int(os.environ.get("DESKTOP_AUTH_MAX_SKEW_SECONDS", "300"))
    if abs(int(time.time()) - timestamp_seconds) > max(30, min(max_skew_seconds, 900)):
        return False, "Desktop IPC timestamp expired"
    expected = build_desktop_ipc_signature(
        method,
        full_path,
        timestamp,
        capability,
        install_secret,
        request_nonce,
    )
    if not hmac.compare_digest(signature, expected):
        return False, "Desktop IPC signature invalid"
    return True, ""


def issue_desktop_auth_challenge(session_obj: MutableMapping[str, object]) -> Tuple[str, int]:
    """Issue one-time nonce and persist it in the current session."""
    nonce = secrets.token_urlsafe(32)
    ttl_seconds = _nonce_ttl_seconds()
    expires_at = int(time.time()) + ttl_seconds
    session_obj[DESKTOP_NONCE_SESSION_KEY] = nonce
    session_obj[DESKTOP_NONCE_EXPIRES_SESSION_KEY] = expires_at
    # Electron renders from app:// and calls the Flask API over localhost. Some
    # Chromium builds do not send the session cookie back on that CORS POST, so
    # keep a one-time process-local nonce copy for the packaged desktop flow.
    _remember_issued_nonce(nonce, expires_at)
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
    cached_expires_at = _consume_issued_nonce(nonce)

    if not nonce:
        return False, "Desktop auth nonce required"
    if not signature:
        return False, "Desktop auth signature required"
    if not expected_nonce:
        if cached_expires_at is None:
            return False, "Desktop auth challenge missing or already consumed"
        expected_nonce = nonce
        expires_at_raw = cached_expires_at

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
