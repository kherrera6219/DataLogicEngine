"""Main-process-only capability guard for desktop file operations."""

from __future__ import annotations

import os

from flask import jsonify, request

from backend.security.desktop_local_auth import (
    get_or_create_install_secret,
    verify_desktop_ipc_signature,
)


def require_desktop_ipc_capability(expected_capability: str):
    """Require an Electron-main signature for path-bearing desktop operations."""
    if os.environ.get("IS_DESKTOP_APP", "false").lower() != "true":
        return None

    remote_addr = (request.remote_addr or "").strip().lower()
    if remote_addr not in {"", "127.0.0.1", "::1", "localhost"}:
        return jsonify(
            {
                "success": False,
                "error": "Desktop file capability denied",
                "code": "DESKTOP_IPC_CAPABILITY_REQUIRED",
            }
        ), 403

    capability = (request.headers.get("X-Desktop-IPC-Capability") or "").strip()
    timestamp = (request.headers.get("X-Desktop-Auth-Timestamp") or "").strip()
    request_nonce = (request.headers.get("X-Desktop-Auth-Request-Nonce") or "").strip()
    signature = (request.headers.get("X-Desktop-IPC-Signature") or "").strip()
    if capability != expected_capability:
        return jsonify(
            {
                "success": False,
                "error": "Desktop file capability denied",
                "code": "DESKTOP_IPC_CAPABILITY_REQUIRED",
            }
        ), 403

    valid, _ = verify_desktop_ipc_signature(
        method=request.method,
        full_path=request.full_path,
        timestamp=timestamp,
        capability=capability,
        signature=signature,
        install_secret=get_or_create_install_secret(),
        request_nonce=request_nonce,
    )
    if not valid:
        return jsonify(
            {
                "success": False,
                "error": "Desktop file capability denied",
                "code": "DESKTOP_IPC_CAPABILITY_REQUIRED",
            }
        ), 403
    return None
