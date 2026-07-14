"""Data-classification, volume-encryption, artifact, and key-separation tests."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from backend.storage.coordinated_backup import CoordinatedBackupCoordinator
from backend.storage.data_at_rest import (
    ACTIVE_DATA_PROTECTION_MODEL,
    DATA_CLASSIFICATIONS,
    SECURE_DELETE_RESIDUAL_RISK,
    VolumeProtection,
    build_at_rest_report,
)
from tests.storage.test_coordinated_backup_restore import RECOVERY_SECRET, _coordinator


def test_every_required_sensitive_data_class_has_protection_and_retention():
    required = {
        "provider_credentials",
        "client_credentials",
        "prompts_and_chats",
        "external_client_requests_results",
        "traces_and_evidence",
        "gateway_audit_and_usage",
        "ingested_documents",
        "embeddings",
        "graph_data",
        "simulations",
        "exports",
        "logs",
        "backups",
        "support_bundles",
        "retained_json_sqlite",
        "temporary_staging",
    }
    registry = {item.key: item for item in DATA_CLASSIFICATIONS}

    assert required == set(registry)
    assert all(item.protection and item.retention_class for item in registry.values())
    assert "volume_encryption" in ACTIVE_DATA_PROTECTION_MODEL


def test_production_report_requires_both_volume_encryption_and_restricted_acl(tmp_path):
    def protected(_path):
        return VolumeProtection("protected", True, True, "test")

    report = build_at_rest_report(
        tmp_path,
        volume_probe=protected,
        acl_probe=lambda _path: True,
    )
    assert report["production_ready"] is True
    assert report["violations"] == []

    unprotected = build_at_rest_report(
        tmp_path,
        volume_probe=lambda _path: VolumeProtection("not_protected", False, False, "test"),
        acl_probe=lambda _path: True,
    )
    assert unprotected["production_ready"] is False
    assert "active_data_volume_encryption_not_verified" in unprotected["violations"]


def test_plaintext_secret_backup_and_staging_residue_fail_closed(tmp_path):
    (tmp_path / "databases").mkdir()
    (tmp_path / "backups").mkdir()
    (tmp_path / "staging").mkdir()
    (tmp_path / "databases" / "credentials.json").write_text("secret", encoding="utf-8")
    (tmp_path / "backups" / "portable.zip").write_bytes(b"plaintext")
    (tmp_path / "staging" / "export.tmp").write_bytes(b"plaintext")

    report = build_at_rest_report(
        tmp_path,
        volume_probe=lambda _path: VolumeProtection("protected", True, True, "test"),
        acl_probe=lambda _path: True,
    )

    assert report["production_ready"] is False
    assert any("plaintext_secret_in_data_root" in item for item in report["violations"])
    assert any("unencrypted_portable_backup" in item for item in report["violations"])
    assert any("plaintext_staging_residue" in item for item in report["violations"])


def test_portable_backup_does_not_depend_on_machine_bound_key(tmp_path):
    coordinator: CoordinatedBackupCoordinator = _coordinator()
    result = coordinator.create_backup(tmp_path, recovery_secret=RECOVERY_SECRET)
    archive = Path(result["artifact_path"])
    manifest = coordinator.inspect_archive(archive, recovery_secret=RECOVERY_SECRET)

    assert manifest["portable_encryption"] is True
    assert manifest["machine_bound_key_required"] is False
    assert b"sensitive postgres value" not in archive.read_bytes()


def test_secure_delete_limit_is_disclosed_truthfully():
    lowered = SECURE_DELETE_RESIDUAL_RISK.lower()
    assert "cannot be guaranteed" in lowered
    assert "ssd" in lowered
    assert "snapshot" in lowered


def test_windows_acl_verification_requires_owner_and_system_without_broad_access(
    monkeypatch,
    tmp_path,
):
    from backend.security import windows_acl

    monkeypatch.setattr(windows_acl.platform, "system", lambda: "Windows")
    monkeypatch.setattr(windows_acl, "_current_user_sid", lambda: "S-1-5-21-42")

    def restricted(command, **_kwargs):
        if command == ["whoami"]:
            return SimpleNamespace(stdout="desktop\\kevin\n")
        return SimpleNamespace(
            stdout=(
                f"{tmp_path} DESKTOP\\kevin:(OI)(CI)(F)\n"
                "          NT AUTHORITY\\SYSTEM:(OI)(CI)(F)\n"
            )
        )

    monkeypatch.setattr(windows_acl.subprocess, "run", restricted)
    assert windows_acl.verify_restricted_user_acl(tmp_path) is True

    def broad(command, **_kwargs):
        if command == ["whoami"]:
            return SimpleNamespace(stdout="desktop\\kevin\n")
        return SimpleNamespace(
            stdout=(
                f"{tmp_path} DESKTOP\\kevin:(F)\n"
                "          NT AUTHORITY\\SYSTEM:(F)\n"
                "          BUILTIN\\Users:(RX)\n"
            )
        )

    monkeypatch.setattr(windows_acl.subprocess, "run", broad)
    assert windows_acl.verify_restricted_user_acl(tmp_path) is False
