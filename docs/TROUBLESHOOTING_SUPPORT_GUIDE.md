# DataLogicEngine troubleshooting and support guide

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-USER-004 |
| Title | Troubleshooting and support guide |
| Document version | v1.2.1 |
| Product version | 4.4.1 |
| Status | qualification_only |
| Audience | Users, evaluators, operators, support engineers, and security reviewers |
| Owner | Support Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Implemented error taxonomy, diagnostics/support controls, lifecycle runbooks, and release gates |
| Confidentiality | Public |
| Last reviewed | 2026-08-11 |
| Next-review trigger | User-visible error, diagnostics, support-bundle, recovery, reporting-channel, or release-status change |
| Requirements and evidence | Product requirements, runtime/error contracts, support tests, operational procedures, and Phase 13/15 evidence |

## First rule: preserve the safety gate

DataLogicEngine intentionally refuses unsafe startup or execution. Do not work
around an error by disabling storage protection, ACLs, authentication, signature,
migration, readiness, provider, scope, or required-service checks. Record the
safe error code and fix the underlying condition.

Every current 4.4.1 artifact is qualification-only, unsigned, and not approved
for public installation. The 2026-08-10 installed candidate reached readiness
with its managed five-service data plane. Do not resolve a startup problem by
creating another database, switching to SQLite/memory/filesystem fallbacks, or
restarting superseded legacy service containers.

The August 11 local build is a different artifact and has not passed installed
acceptance. Always record the exact SHA-256 before applying troubleshooting
evidence from another build.

On Windows, the backend may log that signal-based request timeout is unavailable
and that the packaged server timeout should be used. This is a non-blocking
platform warning when `/ready` and Diagnostics are healthy; it is not the prior
core-services startup failure.

## Before requesting help

Record only non-secret facts:

- product version and exact installer filename/hash/signature status;
- Windows edition/build and whether it is a desktop or owner-controlled VM;
- action attempted and expected versus actual result;
- time and stable correlation, run, trace, job, or operation ID;
- safe error code/class and the displayed readiness/capability state;
- whether the problem started after install, repair, upgrade, restore, provider,
  connector, gateway, Windows, antivirus, firewall, sleep/resume, or disk change;
- minimal reproduction steps and whether data may have changed.

Never include API keys, authorization headers, passwords, recovery passphrases,
certificate private keys, installation secrets, raw prompts/documents, provider
payloads, or unreviewed logs/bundles in an issue.

## Diagnostics and local support bundle

Open **Admin > Diagnostics** and review the content-free state first. Select
**Preview bundle**, inspect the exact inventory and fingerprint, and only then
confirm **Generate local bundle**. The app writes a local archive and SHA-256
sidecar; it does not upload them.

Before sharing, confirm the preview still matches, review every file, and use the
approved encrypted-sharing path. Bundles exclude generic reports and user
content and re-redact allowlisted logs, but preview and human review remain
mandatory. A bundle generation or redaction failure is itself a blocker; do not
zip the runtime/data directory manually.

## Common problems

### The app is live but not ready

This usually means the process started but a mandatory identity, storage,
service, migration, or policy gate failed.

1. Read the displayed safe blocker and authenticated capability state.
2. Confirm another DataLogicEngine instance does not own the runtime lock.
3. Confirm the configured runtime root belongs to the current Windows owner and
   is on an approved protected volume with restricted ACLs.
4. Check all required service identities and state; an open port is not proof
   that the listener belongs to DataLogicEngine.
5. Check migration status and product/schema compatibility.
6. Preserve evidence before repair or restore.

Do not delete a live lock, reuse a foreign listener, enable automatic schema
creation, switch to SQLite/filesystem/memory fallbacks, or weaken production mode.

### `at_rest_protection_not_ready`

The runtime could not prove the Windows protected-volume or ACL boundary. This
is expected fail-closed behavior on an unqualified workstation.

1. Confirm the machine and selected data root are in the supported release
   matrix.
2. Confirm the volume protection and required Windows identity/ACL state.
3. Do not move data by partial directory copy.
4. Use the approved backup/isolated-restore procedure if relocation is required.
5. Rerun installed qualification against the exact signed candidate.

### `runtime_already_owned` or port ownership failure

Close the other DataLogicEngine instance through its normal shutdown. If another
product owns a desired port, reconfigure or stop that product through its own
procedure. Never terminate an unknown process automatically or point
DataLogicEngine at it. After an abnormal shutdown, verify the process tree is
gone before treating a retained lock as stale.

### No active provider or provider unavailable

1. Open Settings > Provider Connections.
2. Confirm an OpenAI or Google key is stored through the approved protected path.
3. Run the bounded live test; `stored` does not mean `available`.
4. Confirm provider/model selection is allowed by the installed manifest.
5. Review local network, time, provider status, account quota, and budget limits.
6. Distinguish invalid credential, policy denial, rate limit, quota, timeout,
   cancellation, and provider outage; do not label all as provider failure.
7. Review the content-free usage ledger for attempts and retry identity.

Provider-backed work requires the owner's provider account and network. The app
must not silently switch to another provider or duplicate spend.

### Chat or client request is blocked, failed, or cancelled

Open Runs/Trace Explorer using the stable trace/run ID. Review the explicit
outcome class, executed stages, policy/evidence status, provider/model, and safe
failure reason. Missing confidence is `not measured`; missing stages must not be
invented. For client requests, also review client scope, expiry, rate/concurrency,
job state, idempotency key, and cancellation state.

### PostgreSQL, Redis, Neo4j, ChromaDB, or object storage fails

1. Stop destructive user actions and preserve operation IDs.
2. Check Diagnostics for the expected installation-specific service identity,
   health, and lifecycle operation.
3. Check disk space, protected-volume state, ACLs, antivirus/file locks, and
   recent restart/update activity.
4. Verify migration and cross-store reconciliation state.
5. Use the coordinated repair or isolated restore; do not copy individual store
   directories or substitute a development backend.

ADR-0010 selects SeaweedFS 4.40-dle.1 for rebuilt installed qualification of the
app-owned S3-compatible object-store capability. Do not enable production use or
substitute a different image: installed protected-volume, recovery,
independent-review, signing, and release gates still control production approval.

### Ingestion or knowledge data is inconsistent

Stop update/deletion retries that could compound the mismatch. Record the source,
job, file, corpus, revision, and operation IDs without copying content into an
issue. Review PostgreSQL job authority and the required object, Neo4j, ChromaDB,
and memory references. Use the approved reconciliation/repair action and verify
provenance, retrieval, shared-chunk references, and deletion remnants afterward.

### MCP connector will not start or changed

Confirm the exact absolute executable/arguments fingerprint, approved file root,
scopes, consent, credentials, and qualification state. Registration does not run
the connector. If the fingerprint or executable changed, keep it stopped, revoke
old consent as appropriate, and perform new review. Shell/package runners,
caller-provided authority, network targets, and unrestricted paths are not part
of the initial contract.

### Client Gateway request is denied

Check the named client key's scope, expiry, revocation, concurrency/rate limits,
allowed operation/model, job ownership, and trace access. Keys are copy-once;
issue a rotated replacement instead of trying to retrieve the secret. The
private Windows gateway remains disabled until its signed two-machine TLS and
firewall qualification passes. Do not expose the loopback gateway publicly.

### Backup, restore, upgrade, rollback, or deletion fails

Stop and preserve the active and previous roots. Record the lifecycle operation
ID, backup/manifest hash, product/schema versions, and failed store without
recording secrets. Do not report success on a partial restore or deletion. Use
an isolated restore root and keep the previous root until verification passes.
Exported files, backups, snapshots, and immutable remnants require separate
retention handling.

### Support bundle, log, or telemetry concern

Cancel sharing. Confirm external telemetry is explicitly opted in; a configured
DSN alone must not enable it. Preview the bundle again and verify that prompts,
documents, provider payloads, request/response bodies, credentials, authorization
headers, private keys, and decrypted backups are absent. Treat any exposure as a
security/privacy incident.

### Installer, signature, update, or uninstall problem

Stop if the file is unsigned, wrong-publisher, hash-mismatched, revoked,
downgraded, replayed, stale, or not named in the release record. Automatic update
is disabled. Preserve installer/update logs and follow the lifecycle guide. Do
not use legacy installer scripts or a `Latest` alias as production evidence.

## Reporting channels

| Need | Channel |
|---|---|
| Setup, usage, or evaluation question | GitHub Discussions |
| Reproducible non-security defect | GitHub Bug Report issue form |
| Proposed product change | GitHub Feature Request issue form |
| Documentation defect | Documentation issue or pull request |
| Security vulnerability or suspected secret/data exposure | Private process in `SECURITY.md`; never a public issue |

Search existing reports first. Provide the minimal safe reproduction and, only
when requested through an approved channel, the reviewed encrypted support
bundle and its SHA-256. Maintainers must bind any fix claim to the replacement
commit/build and rerun the affected normal, adversarial, recovery, and regression
tests.
