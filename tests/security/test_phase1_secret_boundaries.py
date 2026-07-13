"""Phase 1 DPAPI, ACL, redaction, and backup-exclusion checks."""

from __future__ import annotations

import zipfile
from types import SimpleNamespace

import pytest


def test_provider_credentials_use_dpapi_at_rest(app, monkeypatch):
    from models import LLMProvider

    monkeypatch.setattr("backend.security.dpapi_store.is_available", lambda: True)
    monkeypatch.setattr(
        "backend.security.dpapi_store.encrypt_data",
        lambda value: f"protected::{value[::-1]}",
    )
    monkeypatch.setattr(
        "backend.security.dpapi_store.decrypt_data",
        lambda value: value.removeprefix("protected::")[::-1],
    )

    with app.app_context():
        provider = LLMProvider(name="OpenAI", provider_type="openai")
        provider.set_api_key("provider-secret-sentinel")
        stored = bytes(provider.api_key_encrypted)

        assert b"provider-secret-sentinel" not in stored
        assert stored.startswith(b"dpapi:v1:")
        assert provider.get_api_key() == "provider-secret-sentinel"


def test_runtime_storage_credentials_are_dpapi_protected(tmp_path, monkeypatch):
    from backend.storage import runtime_settings

    settings_path = tmp_path / "settings.json"
    monkeypatch.setenv("DATALOGIC_STORAGE_SETTINGS_PATH", str(settings_path))
    monkeypatch.setattr(runtime_settings, "encrypt_data", lambda value: f"cipher::{value[::-1]}")
    monkeypatch.setattr(
        runtime_settings,
        "decrypt_data",
        lambda value: value.removeprefix("cipher::")[::-1],
    )
    monkeypatch.setattr(runtime_settings, "ensure_restricted_user_acl", lambda *_args, **_kwargs: True)

    runtime_settings.save_storage_settings(
        {
            "cloud_config": {
                "postgres_url": "postgresql://owner:secret-sentinel@127.0.0.1/db",
                "s3_secret_key": "s3-secret-sentinel",
                "s3_bucket": "documents",
            }
        }
    )

    raw = settings_path.read_text(encoding="utf-8")
    assert "secret-sentinel" not in raw
    assert raw.count("dpapi:v1:") == 2
    loaded = runtime_settings.load_storage_settings()["cloud_config"]
    assert loaded["s3_secret_key"] == "s3-secret-sentinel"
    assert loaded["s3_bucket"] == "documents"


def test_backup_excludes_secret_and_settings_files(tmp_path, monkeypatch):
    from app import create_app
    from backend.routes.storage_routes import _create_backup

    runtime_root = tmp_path / "runtime"
    settings_path = runtime_root / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text("backup-secret-sentinel", encoding="utf-8")
    (runtime_root / ".env").write_text("API_KEY=backup-secret-sentinel", encoding="utf-8")
    instance_dir = runtime_root / "instance"
    instance_dir.mkdir()
    (instance_dir / "desktop_install_secret.dpapi").write_text(
        "backup-secret-sentinel",
        encoding="utf-8",
    )
    memory_dir = runtime_root / "databases" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "safe-data.json").write_text('{"ok": true}', encoding="utf-8")

    monkeypatch.setenv("DATALOGIC_STORAGE_SETTINGS_PATH", str(settings_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    application = create_app(
        "testing",
        {
            "DLE_RUNTIME_ROOT": str(runtime_root),
            "DLE_INITIALIZE_STORES": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{runtime_root / 'ukg_database.db'}",
        },
        start_runtime=False,
    )
    with application.app_context():
        result = _create_backup(str(tmp_path / "backups"))

    with zipfile.ZipFile(result["artifact_path"]) as archive:
        names = set(archive.namelist())
        payloads = b"\n".join(archive.read(name) for name in names if not name.endswith("/"))

    assert "memory/safe-data.json" in names
    assert not any(".env" in name or "settings.json" == name or "secret" in name for name in names)
    assert b"backup-secret-sentinel" not in payloads


def test_structured_logging_redacts_credentials():
    from backend.logging_config import _redact_text_for_logging, _redact_value_for_logging

    sentinel = "sk-abcdefghijklmnopqrstuvwxyz012345"
    assert sentinel not in _redact_text_for_logging(f"api_key={sentinel}")
    assert _redact_value_for_logging({"authorization": f"Bearer {sentinel}"}) == {
        "authorization": "[REDACTED_SECRET]"
    }


def test_windows_acl_helper_uses_current_user_and_system(tmp_path, monkeypatch):
    from backend.security import windows_acl

    target = tmp_path / "protected.secret"
    target.write_text("ciphertext", encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(windows_acl.platform, "system", lambda: "Windows")
    monkeypatch.setattr(windows_acl, "_current_user_sid", lambda: "S-1-5-21-1234")
    monkeypatch.setattr(
        windows_acl.subprocess,
        "run",
        lambda args, **_kwargs: calls.append(args) or SimpleNamespace(returncode=0),
    )

    assert windows_acl.ensure_restricted_user_acl(target, required=True) is True
    command = calls[0]
    assert "/inheritance:r" in command
    assert "*S-1-5-21-1234:F" in command
    assert "*S-1-5-18:F" in command


def test_wrong_kek_fails_without_overwriting_dek_registry(tmp_path, monkeypatch):
    from backend.security.encryption_manager import EncryptionManager

    key_dir = tmp_path / "keys"
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "phase1-correct-kek-secret-32-bytes")
    EncryptionManager(key_dir=str(key_dir))
    registry_path = key_dir / "dek_registry.json"
    original_registry = registry_path.read_bytes()

    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "phase1-wrong-kek-secret-32-bytes-xx")
    with pytest.raises(RuntimeError, match="restore the correct"):
        EncryptionManager(key_dir=str(key_dir))

    assert registry_path.read_bytes() == original_registry
