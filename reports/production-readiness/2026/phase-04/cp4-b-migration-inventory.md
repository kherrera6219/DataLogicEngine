# CP4-B Migration and Supported-Upgrade Inventory

## Status

- Inventory schema: `1.0.0`
- Captured: `2026-07-14T08:34:48.008650+00:00`
- Production migration ready: **No**
- Alembic revisions: **21**
- Alembic base/head: `000000000001` / `b7c8d9e0f1a2`
- Alembic graph errors: **0**
- Managed coordinated backup available: **Yes**

The PostgreSQL Alembic graph is a single linear chain. The startup migration
coordinator probes every retained store before readiness, records per-store
versions, requires verified coordinated backup before destructive work, and
fails closed on newer or unsupported data. Legacy `db.create_all()` remains
a development helper and is not the production coordinator.

## Store migration surfaces

| Surface | Target version | Version probe | Forward migration | Rollback policy | Status | Blocker |
|---|---|---|---|---|---|---|
| postgresql | alembic:b7c8d9e0f1a2 | SELECT version_num FROM alembic_version | transactional Alembic upgrade through the single revision head | revision-specific downgrade only after verified coordinated backup | fresh_install_and_current_head_coordinated_restore_passed | supported_0_1_1_upgrade_not_qualified |
| redis | dle.redis.v1 | GET dle:schema:redis | versioned namespace migration or explicit disposable-key invalidation | restore durable keys from coordinated backup; invalidate disposable keys | version_ledger_fresh_bootstrap_and_durable_restore_passed | supported_0_1_1_redis_adoption_not_qualified |
| neo4j | dle.neo4j.v1 | MATCH (v:DLESchemaVersion {component:'neo4j'}) RETURN v.version | ordered constraints, indexes, labels, relationships, and property transforms | restore isolated graph dump or apply an explicitly reversible graph revision | version_ledger_schema_restore_and_current_revision_passed | supported_0_1_1_neo4j_adoption_not_qualified |
| chroma | dle.chroma.v1 | read versioned collection registry and source corpus revision | build compatible collection, reconcile sources, verify query parity, then switch | retain prior collection until parity and owner-confirmed cutover | versioned_registry_collection_restore_and_count_parity_passed | supported_0_1_1_chroma_rebuild_not_qualified |
| minio | dle.minio.v1 | HEAD app-owned schema manifest object and verify metadata/hash | version object metadata, bucket policies, lifecycle, and retention contracts | restore portable bucket snapshot with key/metadata/hash parity | minio_schema_manifest_portable_restore_and_hash_parity_passed | supported_0_1_1_minio_adoption_not_qualified |
| local_json_memory | unified-memory.v1 | read and validate root JSON version field before loading vertices or edges | write migrated graph to a temporary path and atomically replace after validation | retain and restore the last valid versioned JSON graph | version_enforcement_atomic_write_startup_and_restore_passed | - |
| retained_configuration | configuration.v1 | validate each retained configuration and DPAPI vault schema version | validate, transform, protect secrets, and atomically replace each retained file | retain last valid configuration and refuse startup on incompatible newer versions | credential_vault_migration_and_configuration_restore_passed | - |
| sqlite_development | development-sqlite.v1 | inspect SQLite tables/columns and retained desktop file version | development-only additive migration; never production authority | copy disposable development database before change or recreate it | retained_reinstall_contract_passed_production_import_missing | released_sqlite_to_postgresql_import_not_implemented |

## Supported upgrade sources

- `0.1.1` retained-data input is in scope; its populated upgrade, uninstall/reinstall, rollback, and clean-restore matrix is not yet passed.

## Blocking gaps

- `released_sqlite_to_postgresql_import_not_implemented`
- `supported_0_1_1_chroma_rebuild_not_qualified`
- `supported_0_1_1_minio_adoption_not_qualified`
- `supported_0_1_1_neo4j_adoption_not_qualified`
- `supported_0_1_1_redis_adoption_not_qualified`
- `supported_0_1_1_upgrade_not_qualified`

## Release constraints

- MinIO remains the production object-store migration authority.
- SeaweedFS candidate evidence may test contract portability but is not
  a production migration target.
- Startup against a newer incompatible data version must fail closed.
- Partial store migration must remain visible and rollback/retryable.
