"""Typed Phase 3 delivery plan and protected per-install credential vault.

This module does not start containers. It validates the candidate lock, derives
stable installation-specific identities/ports, and protects generated service
credentials. Production plan construction fails closed until every service in
the lock is explicitly production-approved.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from backend.security.dpapi_store import decrypt_data, encrypt_data
from backend.security.windows_acl import ensure_restricted_user_acl


CREDENTIAL_SCHEMA_VERSION = "1.1.0"
LEGACY_CREDENTIAL_SCHEMA_VERSION = "1.0.0"
LOCK_SCHEMA_VERSION = "1.0.0"
REQUIRED_SERVICES = (
    "postgresql",
    "redis",
    "neo4j",
    "chromadb",
    "object_store_candidate",
)
KNOWN_DEFAULT_SECRETS = frozenset(
    {
        "postgres",
        "password",
        "neo4j",
        "neo4jpassword",
        "minioadmin",
        "minioadmin123",
        "changeme",
        "secret",
    }
)


class DataPlaneDeliveryError(RuntimeError):
    """Raised for a safely reportable delivery lock or credential failure."""


@dataclass(frozen=True, slots=True)
class ServiceArtifact:
    name: str
    product: str
    version: str
    image: str
    linux_amd64_digest: str
    license: str
    production_approved: bool


@dataclass(frozen=True, slots=True)
class ServiceCredential:
    username: str
    password: str
    access_key: str = ""
    secret_key: str = ""

    def secret_values(self) -> tuple[str, ...]:
        return tuple(
            value
            for value in (self.password, self.access_key, self.secret_key)
            if value
        )


@dataclass(frozen=True, slots=True)
class ServiceDelivery:
    name: str
    container_name: str
    host: str
    host_ports: tuple[int, ...]
    image: str
    linux_amd64_digest: str
    memory_bytes: int
    cpus: float
    pids_limit: int
    required: bool = True


@dataclass(frozen=True, slots=True)
class DataPlanePlan:
    installation_id: str
    profile: str
    network_name: str
    services: tuple[ServiceDelivery, ...]
    production_authorized: bool

    def to_redacted_dict(self) -> dict[str, Any]:
        return {
            "installation_id": self.installation_id,
            "profile": self.profile,
            "network_name": self.network_name,
            "production_authorized": self.production_authorized,
            "services": [asdict(service) for service in self.services],
        }


def _require_digest_image(image: str, digest: str) -> None:
    if "@sha256:" not in image:
        raise DataPlaneDeliveryError("service_image_is_not_digest_pinned")
    if not digest.startswith("sha256:") or len(digest) != 71:
        raise DataPlaneDeliveryError("service_platform_digest_invalid")


def load_candidate_lock(path: str | Path) -> tuple[dict[str, Any], dict[str, ServiceArtifact]]:
    """Load and validate the immutable candidate lock without granting approval."""

    lock_path = Path(path).resolve()
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise DataPlaneDeliveryError("candidate_lock_unreadable") from exc
    if payload.get("schema_version") != LOCK_SCHEMA_VERSION:
        raise DataPlaneDeliveryError("candidate_lock_schema_unsupported")
    if payload.get("production_provisioning_authorized") is not False:
        raise DataPlaneDeliveryError("candidate_lock_must_not_self_authorize")

    raw_services = payload.get("services")
    if not isinstance(raw_services, dict):
        raise DataPlaneDeliveryError("candidate_lock_services_missing")
    artifacts: dict[str, ServiceArtifact] = {}
    for name in REQUIRED_SERVICES:
        item = raw_services.get(name)
        if not isinstance(item, dict):
            raise DataPlaneDeliveryError(f"candidate_lock_service_missing:{name}")
        product = str(item.get("product") or name)
        version = str(item.get("version") or "")
        image = str(item.get("image") or "")
        digest = str(item.get("linux_amd64_digest") or "")
        license_name = str(item.get("license") or "")
        if not version or not license_name:
            raise DataPlaneDeliveryError(f"candidate_lock_service_metadata_missing:{name}")
        _require_digest_image(image, digest)
        artifacts[name] = ServiceArtifact(
            name=name,
            product=product,
            version=version,
            image=image,
            linux_amd64_digest=digest,
            license=license_name,
            production_approved=item.get("production_approved") is True,
        )
    return payload, artifacts


def _validate_installation_id(installation_id: str) -> str:
    normalized = str(installation_id).strip().lower()
    if len(normalized) < 12 or any(character not in "0123456789abcdef" for character in normalized):
        raise DataPlaneDeliveryError("installation_id_invalid")
    return normalized


def _generated_secret(byte_count: int = 36) -> str:
    value = secrets.token_urlsafe(byte_count)
    if len(value) < 32 or value.lower() in KNOWN_DEFAULT_SECRETS:
        raise DataPlaneDeliveryError("generated_secret_quality_failure")
    return value


def generate_service_credentials() -> dict[str, ServiceCredential]:
    """Generate unique least-privilege application credentials per service."""

    credentials = {
        "postgresql": ServiceCredential("dle_app", _generated_secret()),
        "postgresql_migration": ServiceCredential("dle_migration", _generated_secret()),
        "redis": ServiceCredential("dle_app", _generated_secret()),
        "redis_recovery": ServiceCredential("dle_recovery", _generated_secret()),
        "neo4j": ServiceCredential("neo4j", _generated_secret()),
        "object_store_bootstrap": ServiceCredential(
            "dle_bootstrap",
            _generated_secret(),
            access_key=f"DLEBOOT{secrets.token_hex(16).upper()}",
            secret_key=_generated_secret(),
        ),
        "object_store_app": ServiceCredential(
            "dle_app",
            _generated_secret(),
            access_key=f"DLEAPP{secrets.token_hex(16).upper()}",
            secret_key=_generated_secret(),
        ),
    }
    all_secrets = [
        value
        for credential in credentials.values()
        for value in credential.secret_values()
    ]
    if len(set(all_secrets)) != len(all_secrets):
        raise DataPlaneDeliveryError("generated_credentials_not_unique")
    return credentials


class DataPlaneCredentialVault:
    """DPAPI-protected, ACL-restricted per-install credential persistence."""

    def __init__(self, path: str | Path, *, require_dpapi: bool = True) -> None:
        self.path = Path(path).resolve()
        self.require_dpapi = require_dpapi
        self._prepared_installation_id: str | None = None
        self._prepared_credentials: dict[str, ServiceCredential] | None = None

    def load_or_create(self, installation_id: str) -> dict[str, ServiceCredential]:
        normalized_id = _validate_installation_id(installation_id)
        if self.path.exists():
            return self._load(normalized_id)
        credentials = generate_service_credentials()
        self._store(normalized_id, credentials)
        return credentials

    def load_or_prepare(self, installation_id: str) -> dict[str, ServiceCredential]:
        """Load credentials or prepare them in memory for post-lock persistence."""
        normalized_id = _validate_installation_id(installation_id)
        if self.path.exists():
            return self._load(normalized_id)
        if self._prepared_credentials is None:
            self._prepared_installation_id = normalized_id
            self._prepared_credentials = generate_service_credentials()
        elif self._prepared_installation_id != normalized_id:
            raise DataPlaneDeliveryError("credential_vault_prepared_installation_mismatch")
        return dict(self._prepared_credentials)

    def persist_prepared(self, installation_id: str) -> dict[str, ServiceCredential]:
        """Persist prepared credentials after the caller owns the runtime lock."""
        normalized_id = _validate_installation_id(installation_id)
        if self.path.exists():
            return self._load(normalized_id)
        if (
            self._prepared_credentials is None
            or self._prepared_installation_id != normalized_id
        ):
            raise DataPlaneDeliveryError("credential_vault_not_prepared")
        self._store(normalized_id, self._prepared_credentials)
        return dict(self._prepared_credentials)

    def _protect(self, value: str) -> str:
        encrypted = encrypt_data(value)
        if not encrypted:
            if self.require_dpapi:
                raise DataPlaneDeliveryError("dpapi_protection_required")
            return f"test-only:{value}"
        return f"dpapi:v1:{encrypted}"

    def _unprotect(self, value: str) -> str:
        if value.startswith("dpapi:v1:"):
            decrypted = decrypt_data(value.removeprefix("dpapi:v1:"))
            if not decrypted:
                raise DataPlaneDeliveryError("dpapi_decryption_failed")
            return decrypted
        if not self.require_dpapi and value.startswith("test-only:"):
            return value.removeprefix("test-only:")
        raise DataPlaneDeliveryError("credential_not_dpapi_protected")

    def _store(
        self,
        installation_id: str,
        credentials: dict[str, ServiceCredential],
    ) -> None:
        services: dict[str, dict[str, str]] = {}
        for name, credential in sorted(credentials.items()):
            services[name] = {
                "username": credential.username,
                "password": self._protect(credential.password),
                "access_key": self._protect(credential.access_key) if credential.access_key else "",
                "secret_key": self._protect(credential.secret_key) if credential.secret_key else "",
            }
        payload = {
            "schema_version": CREDENTIAL_SCHEMA_VERSION,
            "installation_id": installation_id,
            "services": services,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            if os.name != "nt":
                self.path.chmod(0o600)
            ensure_restricted_user_acl(self.path, required=self.require_dpapi)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def _load(self, installation_id: str) -> dict[str, ServiceCredential]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as exc:
            raise DataPlaneDeliveryError("credential_vault_unreadable") from exc
        schema_version = payload.get("schema_version")
        if schema_version not in {
            CREDENTIAL_SCHEMA_VERSION,
            LEGACY_CREDENTIAL_SCHEMA_VERSION,
        }:
            raise DataPlaneDeliveryError("credential_vault_schema_unsupported")
        if payload.get("installation_id") != installation_id:
            raise DataPlaneDeliveryError("credential_vault_installation_mismatch")
        raw_services = payload.get("services")
        if not isinstance(raw_services, dict):
            raise DataPlaneDeliveryError("credential_vault_services_missing")

        credentials: dict[str, ServiceCredential] = {}
        for name, item in raw_services.items():
            if not isinstance(item, dict):
                raise DataPlaneDeliveryError("credential_vault_service_invalid")
            credentials[name] = ServiceCredential(
                username=str(item.get("username") or ""),
                password=self._unprotect(str(item.get("password") or "")),
                access_key=(
                    self._unprotect(str(item["access_key"])) if item.get("access_key") else ""
                ),
                secret_key=(
                    self._unprotect(str(item["secret_key"])) if item.get("secret_key") else ""
                ),
            )
        if schema_version == LEGACY_CREDENTIAL_SCHEMA_VERSION:
            credentials["redis_recovery"] = ServiceCredential(
                "dle_recovery",
                _generated_secret(),
            )
            self._store(installation_id, credentials)
        required = {
            "postgresql",
            "postgresql_migration",
            "redis",
            "redis_recovery",
            "neo4j",
            "object_store_bootstrap",
            "object_store_app",
        }
        if set(credentials) != required:
            raise DataPlaneDeliveryError("credential_vault_service_set_invalid")
        return credentials


def derive_service_ports(installation_id: str) -> dict[str, tuple[int, ...]]:
    """Derive stable high loopback ports without using vendor-wide defaults."""

    normalized_id = _validate_installation_id(installation_id)
    seed = int(hashlib.sha256(normalized_id.encode("ascii")).hexdigest()[:8], 16)
    base = 20000 + ((seed % 1000) * 8)
    return {
        "postgresql": (base,),
        "redis": (base + 1,),
        "neo4j": (base + 2, base + 3),
        "chromadb": (base + 4,),
        "object_store_candidate": (base + 5,),
    }


def build_delivery_plan(
    lock_path: str | Path,
    installation_id: str,
    *,
    profile: str,
) -> DataPlanePlan:
    """Build a redaction-safe plan and fail closed for unapproved production."""

    normalized_id = _validate_installation_id(installation_id)
    payload, artifacts = load_candidate_lock(lock_path)
    if profile not in {"qualification", "production"}:
        raise DataPlaneDeliveryError("delivery_profile_invalid")
    production_authorized = bool(
        payload.get("production_provisioning_authorized")
        and all(artifact.production_approved for artifact in artifacts.values())
    )
    if profile == "production" and not production_authorized:
        raise DataPlaneDeliveryError("production_data_plane_not_approved")

    prefix = f"dle-{normalized_id[:12]}"
    ports = derive_service_ports(normalized_id)
    limits = {
        "postgresql": (1_073_741_824, 1.0, 256),
        "redis": (536_870_912, 0.5, 128),
        "neo4j": (2_147_483_648, 1.5, 512),
        "chromadb": (1_610_612_736, 1.0, 256),
        "object_store_candidate": (1_073_741_824, 1.0, 256),
    }
    services = tuple(
        ServiceDelivery(
            name=name,
            container_name=f"{prefix}-{name.replace('_candidate', '')}",
            host="127.0.0.1",
            host_ports=ports[name],
            image=artifacts[name].image,
            linux_amd64_digest=artifacts[name].linux_amd64_digest,
            memory_bytes=limits[name][0],
            cpus=limits[name][1],
            pids_limit=limits[name][2],
        )
        for name in REQUIRED_SERVICES
    )
    return DataPlanePlan(
        installation_id=normalized_id,
        profile=profile,
        network_name=f"{prefix}-internal",
        services=services,
        production_authorized=production_authorized,
    )
