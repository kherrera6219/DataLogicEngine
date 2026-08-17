"""Fail-closed coordinator for versioned multi-store startup migrations."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Set
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Protocol


MIGRATION_LEDGER_SCHEMA_VERSION = "1.0.0"


class MigrationCoordinatorError(RuntimeError):
    """Safely reportable migration gate failure."""


class StoreMigrationAdapter(Protocol):
    """Store-native version and migration operations."""

    def probe_version(self) -> str | None: ...

    def is_empty(self) -> bool: ...

    def bootstrap(self, target_version: str) -> None: ...

    def migrate(self, current_version: str, target_version: str) -> None: ...


class MigrationCoordinator:
    """Coordinate store versions before application stores/workers become ready."""

    def __init__(
        self,
        *,
        adapters: Mapping[str, StoreMigrationAdapter],
        target_versions: Mapping[str, str],
        ledger_path: str | Path,
        product_version: str,
        supported_paths: Set[tuple[str, str, str]] | None = None,
        backup_required_paths: Set[tuple[str, str, str]] | None = None,
        backup_verifier: Callable[[], bool] | None = None,
    ) -> None:
        if set(adapters) != set(target_versions):
            raise ValueError("migration_adapter_target_mismatch")
        self.adapters = dict(adapters)
        self.target_versions = {
            str(store): str(version).strip()
            for store, version in target_versions.items()
        }
        if any(not version for version in self.target_versions.values()):
            raise ValueError("migration_target_version_required")
        self.ledger_path = Path(ledger_path).resolve()
        self.product_version = str(product_version).strip()
        if not self.product_version:
            raise ValueError("product_version_required")
        self.supported_paths = set(supported_paths or set())
        self.backup_required_paths = (
            set(self.supported_paths)
            if backup_required_paths is None
            else set(backup_required_paths)
        )
        if not self.backup_required_paths <= self.supported_paths:
            raise ValueError("migration_backup_path_not_supported")
        self.backup_verifier = backup_verifier

    def assess(self) -> dict[str, dict[str, str | None]]:
        """Classify every store without mutation."""

        result: dict[str, dict[str, str | None]] = {}
        for store in sorted(self.adapters):
            adapter = self.adapters[store]
            target = self.target_versions[store]
            try:
                observed = adapter.probe_version()
                empty = adapter.is_empty()
            except Exception as exc:
                raise MigrationCoordinatorError(
                    f"migration_probe_failed:{store}"
                ) from exc
            if observed is None:
                action = "bootstrap" if empty else "blocked_unversioned"
            elif observed == target:
                action = "current"
            elif (store, observed, target) in self.supported_paths:
                action = "upgrade"
            else:
                action = "blocked_unsupported"
            result[store] = {
                "observed_version": observed,
                "target_version": target,
                "action": action,
            }
        return result

    def run(self) -> dict[str, object]:
        """Apply only authorized paths, verify versions, and persist a safe ledger."""

        assessment = self.assess()
        for store, item in assessment.items():
            action = item["action"]
            if action == "blocked_unversioned":
                raise MigrationCoordinatorError(f"unversioned_data:{store}")
            if action == "blocked_unsupported":
                raise MigrationCoordinatorError(f"unsupported_data_version:{store}")

        upgrade_stores = [
            store for store, item in assessment.items() if item["action"] == "upgrade"
        ]
        backup_required_stores = [
            store
            for store in upgrade_stores
            if (
                store,
                str(assessment[store]["observed_version"]),
                self.target_versions[store],
            )
            in self.backup_required_paths
        ]
        if backup_required_stores:
            if self.backup_verifier is None:
                raise MigrationCoordinatorError("coordinated_backup_required")
            try:
                backup_verified = bool(self.backup_verifier())
            except Exception as exc:
                raise MigrationCoordinatorError("coordinated_backup_verification_failed") from exc
            if not backup_verified:
                raise MigrationCoordinatorError("coordinated_backup_required")

        store_results: dict[str, dict[str, str | None]] = {}
        for store in sorted(self.adapters):
            adapter = self.adapters[store]
            item = assessment[store]
            target = self.target_versions[store]
            action = item["action"]
            try:
                if action == "bootstrap":
                    adapter.bootstrap(target)
                elif action == "upgrade":
                    adapter.migrate(str(item["observed_version"]), target)
                observed_after = adapter.probe_version()
            except Exception as exc:
                raise MigrationCoordinatorError(
                    f"migration_action_failed:{store}"
                ) from exc
            if observed_after != target:
                raise MigrationCoordinatorError(
                    f"migration_target_verification_failed:{store}"
                )
            store_results[store] = {
                "action": action,
                "observed_version": observed_after,
                "target_version": target,
                "status": "ready",
            }

        ledger: dict[str, object] = {
            "schema_version": MIGRATION_LEDGER_SCHEMA_VERSION,
            "product_version": self.product_version,
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "ready",
            "stores": store_results,
            "coordinated_backup_verified": bool(backup_required_stores),
            "backup_required_stores": backup_required_stores,
            "downgrade_automatic": False,
        }
        self._write_ledger(ledger)
        return ledger

    def _write_ledger(self, ledger: dict[str, object]) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.ledger_path.with_suffix(self.ledger_path.suffix + ".tmp")
        payload = json.dumps(ledger, sort_keys=True, indent=2) + "\n"
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.ledger_path)
        finally:
            temporary.unlink(missing_ok=True)
