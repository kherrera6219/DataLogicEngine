# DataLogicEngine Disaster Recovery Runbook

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.0.0 |
| Last updated | 2026-07-13 |
| Status | Active engineering runbook; signed clean-machine drill pending |
| Owner | Platform Operations |

## Recovery boundary

DataLogicEngine recovery is an offline, all-store operation. A production backup
is one encrypted `.dlebackup` archive containing PostgreSQL, Redis durable state,
Neo4j, ChromaDB, MinIO, and approved retained configuration/JSON components under
one signed manifest. A per-store copy is not a supported recovery set.

MinIO remains the production object-store authority. SeaweedFS qualification
artifacts do not change the restore target or authorize production use.

## Create a backup

1. Open **Settings > Storage** in the desktop application.
2. Choose a destination folder.
3. Enter and confirm a recovery passphrase of at least 12 characters.
4. Start the backup and wait for the integrity-verified completion result.
5. Retain the passphrase separately. It is not stored in the archive or app.

The backend stops the materialization worker, verifies the migration ledger,
exports all six components, records outstanding work, hashes and signs the
manifest, encrypts the archive with AES-256-GCM, reads it back, and only then
reports success.

## Restore to a clean root

The application must be stopped. Never restore over a running installation.

```powershell
python scripts/restore_managed_backup.py `
  "D:\Backups\datalogic-<backup-id>.dlebackup" `
  "$env:LOCALAPPDATA\DataLogicEngine-restored" `
  --profile qualification
```

The command prompts locally for the recovery secret. It then:

1. verifies the archive header, authentication tag, signed manifest, hashes,
   component set, product compatibility, and safe paths;
2. creates a new installation identity and recovery-only credentials;
3. starts isolated services on isolated ports;
4. restores and verifies all stores and retained files;
5. checks cross-store state, including outstanding outbox work;
6. atomically activates the restored root only after every check passes; and
7. preserves the prior root for rollback.

Restart the application against the restored root and verify readiness, storage
status, a representative chat/trace, graph traversal, vector retrieval, and
artifact readback before approving deletion of the prior root.

## Failure and rollback

- Authentication, compatibility, component, hash, path, capacity, or store
  verification failure leaves the active root unchanged.
- A failed post-swap validation restores the prior root.
- Do not delete the prior root until owner-confirmed validation and retention
  expiry.
- Do not use Redis `FLUSHALL`, raw volume copying, Git checkout, or individual
  database imports as a substitute for coordinated recovery.
- Preserve the redacted failure result and diagnostic bundle for review.

## Current qualification

The Phase 4 populated engineering drill passed encrypted backup, clean-root
isolated restore, restart activation, prior-root preservation, PostgreSQL user
and pending-outbox recovery, Redis key recovery, Neo4j node recovery, Chroma
record recovery, MinIO object-hash parity, retained JSON recovery, and
cross-store deletion parity.

Production/public recovery remains **NO-GO** until the signed installer completes
the clean-machine restore drill, the supported 0.1.1 retained-data upgrade is
proven, BitLocker/ACL checks pass on the supported Windows matrix, and an
independent recovery review approves the result.

Evidence: `reports/production-readiness/2026/phase-04/phase04_data_lifecycle_qualification.json`.
