"""Offline clean-root restore for the supervised data plane."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json
from pathlib import Path
from typing import Any

from backend.runtime.ownership import InstallationIdentity, RuntimeLock
from backend.storage.coordinated_backup import (
    BackupComponent,
    CoordinatedBackupCoordinator,
    CoordinatedBackupError,
)
from backend.storage.managed_backup import (
    MANAGED_BACKUP_COMPONENTS,
    ChromaCollectionBackupAdapter,
    ManagedBackupResources,
    MinIOPortableBackupAdapter,
    Neo4jLogicalBackupAdapter,
    PostgreSQLDumpBackupAdapter,
    RedisDurableExportAdapter,
    RetainedFilesBackupAdapter,
)
from backend.storage.migration_inventory import SUPPORTED_UPGRADE_SOURCES


class ManagedRestoreEnvironment:
    """Lazily owns isolated services created inside the coordinator's staging root."""

    def __init__(
        self,
        *,
        product_version: str,
        lock_path: str | Path,
        profile: str,
        runtime_binary: str,
    ) -> None:
        self.product_version = str(product_version)
        self.lock_path = Path(lock_path).resolve()
        self.profile = str(profile)
        self.runtime_binary = str(runtime_binary)
        self.isolated_root: Path | None = None
        self.manager = None
        self.resources = ManagedBackupResources()
        self.adapters: dict[str, Any] = {}
        self.started = False

    def ensure_started(self, isolated_root: Path) -> None:
        root = Path(isolated_root).resolve()
        if self.started:
            if root != self.isolated_root:
                raise CoordinatedBackupError("managed_restore_isolation_root_changed")
            return
        identity = InstallationIdentity.load_or_create(
            root / "installation.json",
            version=self.product_version,
        )
        from backend.runtime.podman_data_plane import PodmanDataPlaneManager

        manager = PodmanDataPlaneManager(
            runtime_root=root,
            installation_id=identity.installation_id,
            profile=self.profile,
            lock_path=self.lock_path,
            runtime=self.runtime_binary,
        )
        outcomes = manager.start_all()
        if not all(outcomes.values()):
            if self.profile == "qualification":
                manager.remove_qualification_profile()
            raise CoordinatedBackupError("managed_restore_isolated_services_failed")
        self.manager = manager
        self.isolated_root = root
        self.adapters = self._build_adapters(manager, root)
        self.started = True

    def _build_adapters(self, manager, isolated_root: Path) -> dict[str, Any]:
        import redis
        from neo4j import GraphDatabase

        from backend.storage.chroma_http import ChromaHttpClient
        from backend.storage.object_store import ObjectStore, S3Backend

        settings = manager.connection_settings()
        recovery_settings = manager.recovery_connection_settings()
        metadata = manager.service_metadata()
        redis_client = self.resources.own(
            redis.Redis.from_url(recovery_settings["redis_url"])
        )
        neo4j_driver = self.resources.own(
            GraphDatabase.driver(
                settings["neo4j_uri"],
                auth=(settings["neo4j_user"], settings["neo4j_password"]),
            )
        )
        chroma_client = self.resources.own(
            ChromaHttpClient(
                host=settings["chroma_host"],
                port=settings["chroma_port"],
            )
        )
        object_store = ObjectStore(
            S3Backend(
                settings["object_endpoint"],
                settings["object_access_key"],
                settings["object_secret_key"],
                settings["object_region"],
            )
        )
        return {
            "postgresql": PostgreSQLDumpBackupAdapter(
                manager,
                str(metadata["postgresql"]["version"]),
                "restored-from-manifest",
                outstanding=0,
            ),
            "redis": RedisDurableExportAdapter(
                redis_client,
                str(metadata["redis"]["version"]),
                "restored-from-manifest",
            ),
            "neo4j": Neo4jLogicalBackupAdapter(
                neo4j_driver,
                str(metadata["neo4j"]["version"]),
                "restored-from-manifest",
            ),
            "chroma": ChromaCollectionBackupAdapter(
                chroma_client,
                str(metadata["chroma"]["version"]),
                "restored-from-manifest",
            ),
            "minio": MinIOPortableBackupAdapter(
                object_store,
                settings["object_buckets"],
                str(metadata["minio"]["version"]),
                "restored-from-manifest",
            ),
            "retained": RetainedFilesBackupAdapter(
                isolated_root,
                "restored-from-manifest",
            ),
        }

    def adapter(self, name: str, isolated_root: Path):
        self.ensure_started(isolated_root)
        return self.adapters[name]

    def verify_cross_store(self, _isolated_root: Path, manifest: Mapping[str, Any]):
        components = dict(manifest.get("components") or {})
        if set(components) != set(MANAGED_BACKUP_COMPONENTS):
            return {"status": "fail", "safe_reason": "restore_component_set_invalid"}
        failed = [
            name
            for name, adapter in self.adapters.items()
            if (adapter._restore_result or {}).get("status") != "pass"
        ]
        if failed:
            return {"status": "fail", "safe_reason": "restore_component_not_verified"}
        return {
            "status": "pass",
            "verified_components": sorted(components),
            "outstanding_work": int(
                components["postgresql"].get("outstanding_work") or 0
            ),
        }

    def close(self, *, success: bool) -> None:
        self.resources.close()
        if self.manager is None:
            return
        if success:
            return
        self.manager.stop_all()
        if self.profile == "qualification":
            self.manager.remove_qualification_profile()


class _RestoreProxy:
    def __init__(self, name: str, environment: ManagedRestoreEnvironment):
        self.name = name
        self.environment = environment

    def export(self, _destination: Path) -> BackupComponent:
        raise CoordinatedBackupError("managed_restore_proxy_export_unsupported")

    def restore(self, source: Path, isolated_root: Path) -> None:
        self.environment.adapter(self.name, isolated_root).restore(source, isolated_root)

    def verify_restore(self, isolated_root: Path, component: BackupComponent):
        return self.environment.adapter(self.name, isolated_root).verify_restore(
            isolated_root,
            component,
        )


def _assert_target_offline(target_root: Path) -> None:
    identity_path = target_root / "installation.json"
    if not identity_path.is_file():
        return
    try:
        payload = json.loads(identity_path.read_text(encoding="utf-8"))
        identity = InstallationIdentity(**payload)
    except (OSError, TypeError, ValueError) as exc:
        raise CoordinatedBackupError("restore_target_identity_invalid") from exc
    lock = RuntimeLock(target_root / "runtime.lock", identity)
    try:
        lock.acquire()
    except Exception as exc:
        raise CoordinatedBackupError("restore_target_application_running") from exc
    finally:
        lock.release()


def restore_managed_backup_offline(
    archive: str | Path,
    target_root: str | Path,
    *,
    recovery_secret: str,
    product_version: str,
    lock_path: str | Path,
    profile: str = "qualification",
    runtime_binary: str = "podman",
    environment_factory: Callable[[], ManagedRestoreEnvironment] | None = None,
    post_swap_validator: Callable[[Path], bool] | None = None,
) -> dict[str, Any]:
    """Restore and activate a new installation identity while the app is offline."""
    target = Path(target_root).expanduser().resolve()
    _assert_target_offline(target)
    environment = (
        environment_factory()
        if environment_factory is not None
        else ManagedRestoreEnvironment(
            product_version=product_version,
            lock_path=lock_path,
            profile=profile,
            runtime_binary=runtime_binary,
        )
    )
    coordinator = CoordinatedBackupCoordinator(
        adapters={
            name: _RestoreProxy(name, environment)
            for name in MANAGED_BACKUP_COMPONENTS
        },
        product_version=product_version,
        migration_versions={},
        required_components=MANAGED_BACKUP_COMPONENTS,
        compatibility_check=lambda manifest: str(manifest.get("product_version") or "")
        in {str(product_version), *SUPPORTED_UPGRADE_SOURCES},
        cross_store_verifier=environment.verify_cross_store,
    )
    success = False
    try:
        result = coordinator.restore_to_clean_root(
            archive,
            target,
            recovery_secret=recovery_secret,
            post_swap_validator=post_swap_validator,
        )
        success = True
        identity = json.loads((target / "installation.json").read_text(encoding="utf-8"))
        result.update(
            {
                "activation": "restart_application",
                "installation_id": identity["installation_id"],
                "profile": profile,
            }
        )
        return result
    finally:
        environment.close(success=success)
