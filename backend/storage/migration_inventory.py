"""Read-only Phase 4 migration-surface and Alembic graph inventory."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MIGRATION_INVENTORY_SCHEMA_VERSION = "1.0.0"
SUPPORTED_UPGRADE_SOURCES = ("0.1.1",)


@dataclass(frozen=True, slots=True)
class MigrationSurface:
    key: str
    target_version: str
    version_probe: str
    forward_migration: str
    rollback_policy: str
    status: str
    blocker: str | None = None


MIGRATION_SURFACES: tuple[MigrationSurface, ...] = (
    MigrationSurface(
        key="postgresql",
        target_version="alembic:c8d9e0f1a2b3",
        version_probe="SELECT version_num FROM alembic_version",
        forward_migration="transactional Alembic upgrade through the single revision head",
        rollback_policy="revision-specific downgrade only after verified coordinated backup",
        status="fresh_install_and_current_head_coordinated_restore_passed",
        blocker="supported_0_1_1_upgrade_not_qualified",
    ),
    MigrationSurface(
        key="redis",
        target_version="dle.redis.v1",
        version_probe="GET dle:schema:redis",
        forward_migration="versioned namespace migration or explicit disposable-key invalidation",
        rollback_policy="restore durable keys from coordinated backup; invalidate disposable keys",
        status="version_ledger_fresh_bootstrap_and_durable_restore_passed",
        blocker="supported_0_1_1_redis_adoption_not_qualified",
    ),
    MigrationSurface(
        key="neo4j",
        target_version="dle.neo4j.v1",
        version_probe="MATCH (v:DLESchemaVersion {component:'neo4j'}) RETURN v.version",
        forward_migration="ordered constraints, indexes, labels, relationships, and property transforms",
        rollback_policy="restore isolated graph dump or apply an explicitly reversible graph revision",
        status="version_ledger_schema_restore_and_current_revision_passed",
        blocker="supported_0_1_1_neo4j_adoption_not_qualified",
    ),
    MigrationSurface(
        key="chroma",
        target_version="dle.chroma.v1",
        version_probe="read versioned collection registry and source corpus revision",
        forward_migration="build compatible collection, reconcile sources, verify query parity, then switch",
        rollback_policy="retain prior collection until parity and owner-confirmed cutover",
        status="versioned_registry_collection_restore_and_count_parity_passed",
        blocker="supported_0_1_1_chroma_rebuild_not_qualified",
    ),
    MigrationSurface(
        key="minio",
        target_version="dle.minio.v1",
        version_probe="HEAD app-owned schema manifest object and verify metadata/hash",
        forward_migration="version object metadata, bucket policies, lifecycle, and retention contracts",
        rollback_policy="restore portable bucket snapshot with key/metadata/hash parity",
        status="minio_schema_manifest_portable_restore_and_hash_parity_passed",
        blocker="supported_0_1_1_minio_adoption_not_qualified",
    ),
    MigrationSurface(
        key="local_json_memory",
        target_version="unified-memory.v2",
        version_probe="read and validate root JSON version field before loading vertices or edges",
        forward_migration="write migrated graph to a temporary path and atomically replace after validation",
        rollback_policy="retain and restore the last valid versioned JSON graph",
        status="version_enforcement_atomic_write_startup_and_restore_passed",
        blocker=None,
    ),
    MigrationSurface(
        key="retained_configuration",
        target_version="configuration.v1",
        version_probe="validate each retained configuration and DPAPI vault schema version",
        forward_migration="validate, transform, protect secrets, and atomically replace each retained file",
        rollback_policy="retain last valid configuration and refuse startup on incompatible newer versions",
        status="credential_vault_migration_and_configuration_restore_passed",
        blocker=None,
    ),
    MigrationSurface(
        key="sqlite_development",
        target_version="development-sqlite.v1",
        version_probe="inspect SQLite tables/columns and retained desktop file version",
        forward_migration="development-only additive migration; never production authority",
        rollback_policy="copy disposable development database before change or recreate it",
        status="retained_reinstall_contract_passed_production_import_missing",
        blocker="released_sqlite_to_postgresql_import_not_implemented",
    ),
)


def _assignment_value(tree: ast.Module, name: str) -> object:
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets: Iterable[ast.expr]
        if isinstance(node, ast.Assign):
            targets = node.targets
            value_node = node.value
        else:
            targets = (node.target,)
            value_node = node.value
        if any(isinstance(target, ast.Name) and target.id == name for target in targets):
            return ast.literal_eval(value_node)
    raise ValueError(f"migration_assignment_missing:{name}")


def _normalize_parents(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (tuple, list)) and all(isinstance(item, str) for item in value):
        return tuple(value)
    raise ValueError("migration_down_revision_invalid")


def inventory_alembic_revisions(versions_dir: str | Path) -> dict[str, object]:
    """Parse the Alembic graph without importing or executing migration code."""

    directory = Path(versions_dir).resolve()
    revisions: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for path in sorted(directory.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            revision = str(_assignment_value(tree, "revision"))
            parents = _normalize_parents(_assignment_value(tree, "down_revision"))
        except (OSError, SyntaxError, ValueError) as exc:
            errors.append(f"migration_parse_failed:{path.name}:{type(exc).__name__}")
            continue
        if revision in revisions:
            errors.append(f"duplicate_alembic_revision:{revision}")
            continue
        revisions[revision] = {"file": path.name, "down_revisions": list(parents)}

    revision_ids = set(revisions)
    referenced: set[str] = set()
    children: dict[str, list[str]] = {revision: [] for revision in revisions}
    for revision, item in revisions.items():
        for parent in item["down_revisions"]:
            referenced.add(parent)
            if parent not in revisions:
                errors.append(f"missing_alembic_parent:{revision}:{parent}")
            else:
                children[parent].append(revision)

    bases = sorted(
        revision for revision, item in revisions.items() if not item["down_revisions"]
    )
    heads = sorted(revision_ids - referenced)
    if len(bases) != 1:
        errors.append(f"alembic_base_count:{len(bases)}")
    if len(heads) != 1:
        errors.append(f"alembic_head_count:{len(heads)}")

    linear_order: list[str] = []
    if len(bases) == 1:
        current = bases[0]
        visited: set[str] = set()
        while current not in visited:
            visited.add(current)
            linear_order.append(current)
            next_items = sorted(children[current])
            if not next_items:
                break
            if len(next_items) != 1:
                errors.append(f"alembic_branch_without_merge:{current}")
                break
            current = next_items[0]
        if len(visited) != len(revisions):
            errors.append("alembic_graph_not_single_linear_chain")

    return {
        "revision_count": len(revisions),
        "revisions": [
            {
                "revision": revision,
                "file": revisions[revision]["file"],
                "down_revisions": revisions[revision]["down_revisions"],
            }
            for revision in sorted(revisions)
        ],
        "bases": bases,
        "heads": heads,
        "linear_order": linear_order,
        "errors": sorted(set(errors)),
    }


def build_migration_inventory(root: str | Path) -> dict[str, object]:
    """Return the truthful current migration support matrix."""

    repository_root = Path(root).resolve()
    alembic = inventory_alembic_revisions(repository_root / "migrations" / "versions")
    blockers = sorted(
        {
            surface.blocker
            for surface in MIGRATION_SURFACES
            if surface.blocker is not None
        }
    )
    return {
        "schema_version": MIGRATION_INVENTORY_SCHEMA_VERSION,
        "supported_upgrade_sources": list(SUPPORTED_UPGRADE_SOURCES),
        "production_migration_ready": not blockers and not alembic["errors"],
        "managed_backup_required_before_destructive_migration": True,
        "legacy_create_all_is_production_coordinator": False,
        "alembic": alembic,
        "surfaces": [
            {
                "key": surface.key,
                "target_version": surface.target_version,
                "version_probe": surface.version_probe,
                "forward_migration": surface.forward_migration,
                "rollback_policy": surface.rollback_policy,
                "status": surface.status,
                "blocker": surface.blocker,
            }
            for surface in MIGRATION_SURFACES
        ],
        "blockers": blockers,
        "release_constraints": {
            "production_object_store": "minio",
            "seaweedfs_production_selected": False,
            "coordinated_backup_available": True,
            "coordinated_restore_available": True,
            "current_version_populated_restore_qualified": True,
            "supported_prior_release_upgrade_qualified": False,
            "downgrade_against_newer_data_allowed": False,
        },
    }
