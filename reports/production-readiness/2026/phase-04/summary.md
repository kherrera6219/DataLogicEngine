# Phase 4 Engineering Checkpoint Summary

## Decision

Phase 4 data contracts, migrations, backup/recovery, retention/deletion, and
data-at-rest engineering reached a validated checkpoint on 2026-07-13. Phase 5
may begin under the owner-approved installed-gate deferral. Production/public
release remains **NO-GO**.

## Delivered behavior

- Generated ownership evidence covers 67 PostgreSQL entities and 28 logical
  contracts with one authority, stable IDs, versions, materializations,
  transaction boundaries, and compensating actions.
- Transactional outbox and materialization state make PostgreSQL-to-Neo4j,
  PostgreSQL-to-Chroma, and PostgreSQL-to-MinIO work durable, idempotent,
  retryable, and observable.
- Production startup runs a fail-closed coordinator for the 14-revision Alembic
  chain and every retained store before readiness.
- Coordinated backup produces one signed, hashed, AES-256-GCM encrypted archive
  for PostgreSQL, Redis durable state, Neo4j, ChromaDB, MinIO, and retained
  files. The recovery secret is user-controlled and not persisted.
- Offline restore verifies an isolated clean root and service set, creates a new
  installation identity/recovery credentials, checks every store, activates
  atomically, preserves the prior root, and rolls back failed post-validation.
- Cross-store retention/deletion uses per-store reconciliation and a non-PII
  tombstone. Partial failure cannot be reported as success.
- Uninstall disposition is explicit: keep, export-then-delete after a verified
  backup, or delete with truthful residual-risk language.
- Production at-rest policy requires protected Windows volumes, restricted
  ACLs, DPAPI-wrapped local secrets, and portable AES-256-GCM backups.

## Live populated qualification

The five-service drill completed in 127.864 seconds. It produced an encrypted,
integrity-verified six-component backup; restored it into an isolated clean
root; restarted the restored application; recovered one PostgreSQL user, one
pending outbox event, one Redis durable key, one Neo4j node, one Chroma record,
one retained JSON vertex, and one MinIO object with exact SHA-256 parity; kept
the prior root; and passed deletion across PostgreSQL, Redis, Neo4j, ChromaDB,
MinIO, local JSON, and logs. Qualification resources were removed afterward.

## Checkpoint disposition

| Checkpoint | Engineering result | Installed/release status |
|---|---|---|
| CP4-A ownership map | Passed | Complete |
| CP4-B upgrade matrix | Fresh/current migration passed | 0.1.1 populated retained-data upgrade deferred |
| CP4-C backup | Populated coordinated backup passed | Signed installed proof deferred |
| CP4-D restore | Isolated clean-root recovery passed | Signed clean-machine proof deferred |
| CP4-E delete parity | Seven-surface live deletion passed | Installed matrix retained |
| CP4-F at rest | Policy and fail-closed probes implemented | BitLocker/ACL Windows matrix deferred |

## Object-store decision

MinIO remains the product-specific production architecture. SeaweedFS remains a
Replacement Control candidate only. ADR-0004 is Proposed,
`production_authorized=false`, and `production_selected=false`.

## Evidence index

- `cp4-a-data-ownership-matrix.json` / `.md`
- `cp4-b-migration-inventory.json` / `.md`
- `phase04_data_lifecycle_qualification.json`
- `checks.json`
- `artifacts.json`
- `risk-register.md`
- `docs-reviewed.md`
- `rollback.md`
- `test-results/summary.md`
- `runtime/summary.md`
