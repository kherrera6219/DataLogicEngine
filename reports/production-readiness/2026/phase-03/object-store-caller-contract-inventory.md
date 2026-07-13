# Object-Store Caller and Contract Inventory

## Status

| Field | Value |
|---|---|
| Captured | 2026-07-13 |
| Replacement candidate | SeaweedFS 4.29 |
| Production architecture changed | No |
| Inventory result | Complete for current Python runtime callers; managed-profile failure semantics implemented |

## Runtime callers

| Caller | Bucket/key contract | Operations | Current failure behavior | Replacement implication |
|---|---|---|---|---|
| `app.py::_initialize_storage_collections` | six hyphenated required buckets | create/verify bucket | Managed/production initialization fails closed | Application credentials remain least privilege after bootstrap |
| `TruthMemoryCommitService._write_audit_bundle_object` | `audit-logs/<run_id>.json` | create bucket, put JSON with run/tier/evidence hash metadata | Managed profile raises on required write failure | Retry/reconciliation and durable completion state remain Phase 4 contract work |
| `FROSTService._persist_snapshot_object` | `simulation-artifacts/<snapshot_id>.json` | put JSON with artifact type and snapshot ID metadata | Managed profile raises on required write failure | Simulation workflow recovery remains later-phase work |
| `DSQPChain._persist_deliverable` | `deliverables/dsqp/<persona_id>.json` | put JSON with persona/axis metadata | Managed profile raises on required write failure | Cross-store durable completion remains Phase 4 work |
| `app.py::_object_store_bucket_stats` | Five current buckets | list and sum sizes | Reports unavailable with zero counts | Installed status must distinguish unavailable from genuinely empty and report version/identity/endpoint/backup state |
| `scripts/verify_local_data_stack.py::check_object_store` | configured default bucket | create, put, get, delete | Standalone verification result | Must be replaced by the production profile gate and run against the selected app-owned S3 service |
| `backend.routes.storage_routes` | aggregate object-store metrics | status read | Depends on app metrics | Must report the supervisor's verified candidate identity, not directory existence or assumed health |

## Current API contract

`ObjectBackend` exposes create bucket, put, get, head-like `get_info`, list,
exists, delete, and URL generation. `S3Backend` maps these operations to Boto3.
The replacement test matrix additionally covers:

- path-style SigV4 requests to a loopback endpoint;
- anonymous and invalid-credential denial;
- least-privilege denial of arbitrary bucket creation;
- content type and string metadata preservation;
- SHA-256 read-back integrity;
- prefix listing;
- multipart upload;
- presigned GET;
- graceful restart and forced-termination durability;
- portable export, clean-root restore, local-to-S3 migration, and S3-to-local
  rollback.

## Current implementation gaps

1. Production construction is intentionally locked because no object-store
   implementation is production-approved. The qualification profile supplies
   the supervised S3 endpoint; development retains the local backend.
2. Six required buckets are now defined: audit logs, simulation artifacts,
   deliverables, graphs, evaluation data, and trace exports. Some planned future
   contracts still have no active workflow caller.
3. Required audit, simulation, and DSQP writes fail closed in the managed profile;
   retry/reconciliation semantics remain Phase 4 work.
4. No active caller consumes `get_url`; presigned access remains candidate contract
   coverage, not proof of a production workflow.
5. No active caller performs lifecycle/versioning/retention, bucket policy,
   object lock, or cross-store deletion orchestration.
6. Bucket-wide list operations are used for metrics and will require pagination
   and bounded/aggregated status behavior at production scale.
7. Boto3 is now an exact direct dependency; final frozen-wheel/supply-chain
   qualification remains Phase 14 work.

## Decision impact

The live lab proves that SeaweedFS can satisfy the exercised S3 data operations,
durability smoke, portable backup/restore, migration/rollback, managed caller
failure, and supervisor contracts. Future workflow buckets, pagination,
lifecycle/retention, coordinated recovery, and installed-shell qualification
remain required before ADR-0004 can be accepted or the architecture wording can
change.
