"""Desktop install secrets must never be persisted as plaintext."""

from __future__ import annotations

import os
import time

import pytest

from backend.security import desktop_local_auth


def _clear_cache() -> None:
    desktop_local_auth._INSTALL_SECRET_CACHE = None


def test_install_secret_is_dpapi_encrypted_at_rest(tmp_path, monkeypatch):
    secret_file = tmp_path / "desktop-install-secret.dpapi"
    monkeypatch.delenv("DESKTOP_INSTALL_SECRET", raising=False)
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setattr(
        "backend.security.dpapi_store.encrypt_data",
        lambda value: f"encrypted::{value[::-1]}",
    )
    monkeypatch.setattr(
        "backend.security.dpapi_store.decrypt_data",
        lambda value: value.removeprefix("encrypted::")[::-1],
    )
    _clear_cache()

    secret = desktop_local_auth.get_or_create_install_secret()
    stored = secret_file.read_text(encoding="utf-8")

    assert secret not in stored
    _clear_cache()
    assert desktop_local_auth.get_or_create_install_secret() == secret


def test_production_fails_closed_when_dpapi_is_unavailable(tmp_path, monkeypatch):
    monkeypatch.delenv("DESKTOP_INSTALL_SECRET", raising=False)
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET_FILE", str(tmp_path / "secret.dpapi"))
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setattr("backend.security.dpapi_store.encrypt_data", lambda _value: "")
    _clear_cache()

    with pytest.raises(RuntimeError, match="DPAPI is required"):
        desktop_local_auth.get_or_create_install_secret()


def test_expired_install_secret_rotates(tmp_path, monkeypatch):
    secret_file = tmp_path / "desktop-install-secret.dpapi"
    monkeypatch.delenv("DESKTOP_INSTALL_SECRET", raising=False)
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("DESKTOP_INSTALL_SECRET_ROTATION_DAYS", "30")
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setattr(
        "backend.security.dpapi_store.encrypt_data",
        lambda value: f"encrypted::{value[::-1]}",
    )
    monkeypatch.setattr(
        "backend.security.dpapi_store.decrypt_data",
        lambda value: value.removeprefix("encrypted::")[::-1],
    )
    _clear_cache()
    original = desktop_local_auth.get_or_create_install_secret()
    old_time = time.time() - 31 * 24 * 60 * 60
    os.utime(secret_file, (old_time, old_time))
    _clear_cache()

    rotated = desktop_local_auth.get_or_create_install_secret()
    assert rotated != original


def test_signed_desktop_request_nonce_blocks_replay():
    timestamp = str(int(time.time()))
    nonce = "phase1-request-nonce-0001"
    secret = "phase1-request-signing-secret"
    desktop_local_auth._CONSUMED_REQUEST_NONCES.clear()
    signature = desktop_local_auth.build_desktop_request_signature(
        "POST",
        "/api/v1/settings/ai",
        timestamp,
        secret,
        request_nonce=nonce,
    )

    first = desktop_local_auth.verify_desktop_request_signature(
        method="POST",
        full_path="/api/v1/settings/ai",
        timestamp=timestamp,
        signature=signature,
        install_secret=secret,
        request_nonce=nonce,
    )
    second = desktop_local_auth.verify_desktop_request_signature(
        method="POST",
        full_path="/api/v1/settings/ai",
        timestamp=timestamp,
        signature=signature,
        install_secret=secret,
        request_nonce=nonce,
    )

    assert first == (True, "")
    assert second == (False, "Desktop request replay detected")
