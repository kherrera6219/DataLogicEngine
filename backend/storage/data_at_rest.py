"""Phase 4 data classification and Windows at-rest protection verification."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from pathlib import Path
import subprocess
from typing import Callable


AT_REST_POLICY_VERSION = "2026.07.13-v1"
ACTIVE_DATA_PROTECTION_MODEL = (
    "windows_volume_encryption_plus_dpapi_wrapped_secrets_plus_portable_backup_aes256gcm"
)
SECURE_DELETE_RESIDUAL_RISK = (
    "Secure deletion cannot be guaranteed on every SSD, virtual disk, snapshot, "
    "or retained backup; cryptographic erasure and retention expiry are used where applicable."
)


@dataclass(frozen=True, slots=True)
class DataClassification:
    key: str
    sensitivity: str
    locations: tuple[str, ...]
    protection: tuple[str, ...]
    retention_class: str


@dataclass(frozen=True, slots=True)
class VolumeProtection:
    status: str
    encrypted: bool
    protection_enabled: bool
    provider: str


DATA_CLASSIFICATIONS = (
    DataClassification("provider_credentials", "restricted", ("postgresql", "dpapi_vault"), ("dpapi", "bitlocker"), "installation_lifetime"),
    DataClassification("client_credentials", "restricted", ("postgresql",), ("field_encryption", "bitlocker"), "revocation_policy"),
    DataClassification("prompts_and_chats", "confidential", ("postgresql", "exports"), ("bitlocker", "encrypted_export"), "chat_policy"),
    DataClassification("external_client_requests_results", "confidential", ("postgresql", "minio"), ("bitlocker", "object_access_policy"), "gateway_policy"),
    DataClassification("traces_and_evidence", "confidential", ("postgresql", "minio"), ("bitlocker", "object_access_policy"), "trace_policy"),
    DataClassification("gateway_audit_and_usage", "confidential", ("postgresql", "minio", "logs"), ("bitlocker", "integrity_chain"), "audit_policy"),
    DataClassification("ingested_documents", "confidential", ("postgresql", "chroma", "neo4j"), ("bitlocker", "loopback_auth"), "ingestion_policy"),
    DataClassification("embeddings", "confidential", ("chroma",), ("bitlocker", "loopback_auth"), "source_policy"),
    DataClassification("graph_data", "confidential", ("neo4j", "postgresql"), ("bitlocker", "loopback_auth"), "graph_policy"),
    DataClassification("simulations", "confidential", ("postgresql", "minio"), ("bitlocker", "object_access_policy"), "simulation_policy"),
    DataClassification("exports", "confidential", ("user_selected_path",), ("owner_selected_encryption", "short_lived_staging"), "export_policy"),
    DataClassification("logs", "internal", ("runtime_logs",), ("bitlocker", "restricted_acl", "content_minimization"), "log_rotation_policy"),
    DataClassification("backups", "restricted", ("user_selected_path",), ("aes_256_gcm", "owner_recovery_secret", "signed_manifest"), "backup_policy"),
    DataClassification("support_bundles", "confidential", ("user_selected_path",), ("redaction", "owner_selected_encryption"), "support_policy"),
    DataClassification("retained_json_sqlite", "confidential", ("runtime_databases",), ("bitlocker", "restricted_acl", "versioned_format"), "retained_data_policy"),
    DataClassification("temporary_staging", "confidential", ("runtime_staging",), ("bitlocker", "restricted_acl", "immediate_cleanup"), "operation_lifetime"),
)


def probe_windows_volume_encryption(path: str | Path) -> VolumeProtection:
    """Probe BitLocker/device-encryption state without changing the volume."""
    resolved = Path(path).expanduser().resolve()
    if os.name != "nt":
        return VolumeProtection("unsupported_platform", False, False, "none")
    drive = resolved.drive
    if not drive:
        return VolumeProtection("volume_unknown", False, False, "manage-bde")
    try:
        result = subprocess.run(
            ["manage-bde.exe", "-status", drive],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return VolumeProtection("probe_failed", False, False, "manage-bde")
    output = f"{result.stdout}\n{result.stderr}".lower()
    encrypted = "fully encrypted" in output or "percentage encrypted: 100" in output
    protected = "protection on" in output
    return VolumeProtection(
        "protected" if result.returncode == 0 and encrypted and protected else "not_protected",
        encrypted,
        protected,
        "manage-bde",
    )


def find_plaintext_artifact_violations(runtime_root: str | Path) -> list[str]:
    """Find high-signal plaintext secret/portable-artifact contract violations."""
    root = Path(runtime_root).expanduser().resolve()
    violations: list[str] = []
    data_root = root / "databases"
    forbidden_names = {".env", "credentials.json", "secrets.json", "api-keys.json"}
    if data_root.exists():
        for path in data_root.rglob("*"):
            if path.is_file() and path.name.lower() in forbidden_names:
                violations.append(f"plaintext_secret_in_data_root:{path.relative_to(root).as_posix()}")
    backups = root / "backups"
    if backups.exists():
        for path in backups.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".zip", ".tar", ".dump", ".json"}:
                violations.append(f"unencrypted_portable_backup:{path.relative_to(root).as_posix()}")
    staging = root / "staging"
    if staging.exists():
        for path in staging.rglob("*.tmp"):
            if path.is_file():
                violations.append(f"plaintext_staging_residue:{path.relative_to(root).as_posix()}")
    return sorted(violations)


def build_at_rest_report(
    runtime_root: str | Path,
    *,
    volume_probe: Callable[[str | Path], VolumeProtection] = probe_windows_volume_encryption,
    acl_probe: Callable[[str | Path], bool] | None = None,
) -> dict[str, object]:
    root = Path(runtime_root).expanduser().resolve()
    volume = volume_probe(root)
    acl_ok = bool(acl_probe(root)) if acl_probe is not None else False
    violations = find_plaintext_artifact_violations(root)
    if not volume.encrypted or not volume.protection_enabled:
        violations.append("active_data_volume_encryption_not_verified")
    if not acl_ok:
        violations.append("runtime_root_acl_not_verified")
    return {
        "policy_version": AT_REST_POLICY_VERSION,
        "protection_model": ACTIVE_DATA_PROTECTION_MODEL,
        "volume": asdict(volume),
        "restricted_acl_verified": acl_ok,
        "classifications": [asdict(item) for item in DATA_CLASSIFICATIONS],
        "violations": sorted(set(violations)),
        "production_ready": not violations,
        "secure_delete_residual_risk": SECURE_DELETE_RESIDUAL_RISK,
        "key_separation": {
            "active_data": "runtime_root/databases",
            "machine_wrapping": "DPAPI current-user scope",
            "portable_recovery": "owner-controlled recovery secret not persisted in archive",
        },
    }
