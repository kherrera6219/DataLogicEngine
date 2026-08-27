# DataLogicEngine maintenance and disaster-recovery plan

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ENG-007 |
| Title | Maintenance and disaster-recovery plan |
| Document version | v1.1.1 |
| Product version | 4.4.3 |
| Status | qualification_only |
| Audience | Owner/operator, platform and data engineering, support, security, quality, and recovery reviewers |
| Owner | Platform Operations |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Implemented coordinated backup/restore, migration, service lifecycle, support, and release controls |
| Confidentiality | Public |
| Last reviewed | 2026-08-11 |
| Next-review trigger | Store, backup, restore, retention, migration, recovery, update, service, or support-policy change |
| Requirements and evidence | Product/data requirements, recovery implementation/tests, runbooks, and Phase 3/4/13/15 evidence |

## Purpose and qualification boundary

Define preventive maintenance, backup, recovery, rollback, and evidence needed
to restore the supported local-first Windows application without bypassing data
authority or security controls. Populated engineering drills passed, but signed
clean-machine restore, retained-data upgrade, supported-Windows protection/ACL,
object-store final selection, and independent recovery review remain open. The
2026-08-10 engineering install did verify one-time populated 0.1.1 adoption with
an immutable recovery copy and retained relational/graph/object counts; that is
not a clean-machine restore or full rollback qualification.

## Recovery objectives

Recovery-point and recovery-time objectives must be ratified from the supported
hardware, data-size, workload, and signed installed drill. Until that record
exists, no numeric RPO/RTO is approved. The minimum objective is consistent
restoration of every required authority and cross-store reference without secret
exposure, silent data loss, or false readiness.

## Protected recovery set

The coordinated set includes PostgreSQL, required Redis durable/coordination
state where specified, Neo4j, ChromaDB, app-owned S3-compatible object store objects/namespaces, Unified/Truth
memory and approved local records, installation/product/schema identity,
migration ledgers, and manifests/references required to reconcile sessions,
traces, knowledge, simulations, gateway jobs, MCP state, and audit.

Provider/internal-service/connector credentials, installation/signing secrets,
certificate private keys, logs, environment/settings files, and backup recovery
passphrases are excluded or handled only through their separately approved
protected recovery mechanism.

## Preventive maintenance

- Review readiness, service identity, migrations, queues/jobs, partial operations,
  disk margin, resource trends, and recent lifecycle/failure events.
- Verify backup age, encryption, manifest/hash, retention, off-device custody,
  and most recent restore drill.
- Review provider/model manifest, budgets, key age/test, connector fingerprint/
  consent, client keys/scopes, firewall/private-gateway disabled state, and
  external telemetry opt-in.
- Reconcile ingestion object/graph/vector revisions, memory integrity, simulation
  artifacts, gateway/MCP large-result references, deletion remnants, and exports.
- Review dependency/security findings, alert 389, Windows/service support,
  certificates, signing/update authority, and available disk for logs/support.
- Apply only approved signed maintenance releases after impact analysis, backup,
  compatibility review, and rollback preparation.

## Backup procedure

1. Confirm the application identity, product/schema versions, required service
   readiness, active migrations, and available destination space.
2. Quiesce or consistently snapshot required operations through the coordinated
   backup command; do not copy live store directories independently.
3. Enter the recovery passphrase interactively. The application must not persist
   or log it.
4. Generate the encrypted archive and signed/hash-verified manifest.
5. Verify every required store/object/reference, archive size/hash, encryption,
   exclusions, and completion state.
6. Record backup ID, source installation/version, time, retention/expiry, storage
   location, custodian, verification result, and next restore-test date.
7. Protect the backup and passphrase separately and test restore on an isolated
   supported machine/root according to policy.

Create a verified backup before upgrade, repair, rollback, destructive migration,
bulk deletion, object-store migration, or incident remediation.

## Restore procedure

1. Declare the incident/recovery owner and stop the desktop and app-owned
   services through the approved lifecycle.
2. Preserve redacted correlation, lifecycle, installer, and failure evidence and
   retain the current root unchanged.
3. Verify the selected backup envelope, manifest, hashes, product/schema versions,
   installation constraints, and recovery-passphrase custody.
4. Restore into a new isolated protected root; never overwrite the active root.
5. Apply only supported versioned migrations and fail on newer, unsupported,
   unversioned populated, partial, or identity-mismatched data.
6. Verify ACLs/volume protection, service identities, required buckets, schema
   parity, cross-store hashes/revisions/references, and secret exclusions.
7. Start offline first. Verify readiness and representative local session, trace,
   ingestion/retrieval, simulation, gateway, MCP-state, export, and deletion data.
8. Atomically activate the restored root while retaining the prior root for the
   approved rollback window.
9. Re-enable provider, clients, connectors, or private networking one at a time
   only after their checks pass.
10. Record achieved recovery point/time, losses, gaps, evidence, reviewer result,
    and corrective actions.

## Failure and rollback

If verification fails, stop the restored instance, preserve both roots and
redacted evidence, and do not mark ready. Return to the known compatible root or
repeat restore from another verified backup. Never point an older binary at a
newer unsupported store, partially copy store data, delete the prior root before
acceptance, or use a development fallback to declare recovery.

## Scenario coverage

Recovery qualification covers corrupt/incomplete backup, wrong passphrase,
manifest/hash mismatch, disk-full/interruption, service unavailable, partial
store restore, incompatible product/schema, lost credential reference, ACL or
protected-volume failure, foreign service identity, object/graph/vector drift,
interrupted migration/update, deleted active data with retained backup, provider
offline, gateway/MCP job interruption, and rollback/retry without duplicate
provider/tool effects.

## Disaster and security events

For suspected compromise, isolate external/provider/client/connector paths,
preserve approved evidence, rotate/revoke keys and certificates, use a backup
known to predate compromise only after security review, and validate that the
restored root does not contain the original persistence mechanism. Security
recovery requires independent review before reconnecting external paths.

## Data deletion and retirement

Deletion reconciles active required stores and reports partial failure. Backups,
exports, snapshots, and immutable media follow their approved retention and may
outlive active deletion. At end of retention, remove them through the storage-
appropriate process and record the result. Secure erasure is not guaranteed on
every SSD, VM snapshot, or external system.

Product retirement includes final owner export/backup choice, client/connector/
provider key revocation, update/feed shutdown, active-data deletion, backup
expiry, documentation/evidence preservation, and supported-version disclosure.

## Acceptance record

The final record binds source commit, signed installer hash/signature, Windows/
hardware profile, data size, service/object implementation and versions,
product/schema versions, backup hash/manifest, scenarios, achieved RPO/RTO,
failures/retests, remnant scan, reviewers, and owner approval. Until accepted,
the recovery plan remains `qualification_only` and production is **NO-GO**.
