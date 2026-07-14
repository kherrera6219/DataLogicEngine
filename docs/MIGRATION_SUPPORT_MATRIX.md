# DataLogicEngine Migration Support Matrix

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.0.0 |
| Last updated | 2026-07-13 |
| Status | Active engineering contract; installed-release qualification pending |
| Owner | Platform Engineering |
| Machine-readable evidence | `reports/production-readiness/2026/phase-04/cp4-b-migration-inventory.json` |

## Supported migration contract

Production startup invokes the migration coordinator before stores, workers, or
readiness. The coordinator probes every retained store, uses a dedicated
migration credential, records an atomic per-store ledger, refuses newer or
unversioned populated data, and requires a verified coordinated backup before a
destructive upgrade. `AUTO_CREATE_SCHEMA` and `db.create_all()` are development
helpers and are not production migration paths.

| Surface | Current target | Current-version result | Prior 0.1.1 result |
|---|---|---|---|
| PostgreSQL | Alembic `a9b0c1d2e3f4` | Fresh/current migration and restore passed | Populated upgrade not yet qualified |
| Redis | `dle.redis.v1` | Durable export, restore, and version ledger passed | Adoption/migration not yet qualified |
| Neo4j | `dle.neo4j.v1` | Logical restore, schema marker, and parity passed | Adoption/migration not yet qualified |
| ChromaDB | `dle.chroma.v1` | Collection restore and record parity passed | Rebuild/adoption not yet qualified |
| MinIO | `dle.minio.v1` | Bucket/object hash and metadata parity passed | Adoption/migration not yet qualified |
| UnifiedMemory JSON | `unified-memory.v1` | Version enforcement and atomic replace passed | Retained legacy inputs remain Phase 9 work |
| Retained configuration | `configuration.v1` | Validation, DPAPI-vault migration, and restore passed | Installed retained-data matrix not yet qualified |
| Development SQLite | `development-sqlite.v1` | Development reinstall policy passed | Production SQLite-to-PostgreSQL import not implemented |

## Release interpretation

The current-version populated backup/restore engineering drill passed. The full
CP4-B exit statement is intentionally not claimed because the only released
installer, 0.1.1, must still be rebuilt, installed, populated, uninstalled with
retained data, and upgraded through the supported production path. That test is
a release-candidate gate; failure must block release, not silently discard data.

MinIO remains the production object-store migration authority. SeaweedFS may be
used for Replacement Control qualification only and is not a supported
production migration target.

## Verification

Run:

```powershell
python scripts/inventory_migration_surfaces.py
python -m pytest tests/migrations -q
```

The generated JSON is authoritative for the revision graph, exact blockers, and
release constraints.
