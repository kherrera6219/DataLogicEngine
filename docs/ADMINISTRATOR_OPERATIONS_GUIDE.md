# DataLogicEngine administrator and operations guide

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-USER-003 |
| Title | Administrator and operations guide |
| Document version | v1.2.1 |
| Product version | 4.4.2 |
| Status | qualification_only |
| Audience | Single owner/operator, Windows administrators, support engineers, and release reviewers |
| Owner | Platform Operations |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Implemented runtime supervision, data lifecycle, gateway, diagnostics, and operational controls |
| Confidentiality | Public |
| Last reviewed | 2026-08-11 |
| Next-review trigger | Service, readiness, migration, backup, recovery, gateway, connector, diagnostics, or incident-control change |
| Requirements and evidence | Product requirements, architecture, runbook sources, tests, and installed qualification evidence |

## Operating boundary

The 2026-08-10 unsigned qualification candidate installed per-machine, launched from Program
Files, reached `/ready`, and supervised the five app-owned loopback services in
the `datalogicengine` Podman machine. Retained relational, graph, and object data
was adopted and verified; administrators must not initialize a replacement
database or restart the superseded legacy container. Signed lifecycle, recovery,
provider, accessibility, independent, pilot, and soak acceptance remains open.
The newer August 11 local artifact has not completed installed-mode acceptance;
operators must not transfer the August 10 readiness or retained-data evidence
to it.

DataLogicEngine 4.4.2 is a single-owner local-first Windows application. The
normal desktop profile binds the backend and internal services to installation-
specific local boundaries. The application owns PostgreSQL, Redis, Neo4j,
ChromaDB, and app-owned S3-compatible object store production responsibilities; externally managed databases
and public web/SaaS operation are outside the approved contract.

This guide describes the intended production operating model, but the signed
installed lifecycle, service, provider, failure/recovery, soak, accessibility,
and pilot matrices remain open. Use it for controlled qualification until the
release-readiness record promotes the exact signed artifact.

## Responsibility model

| Responsibility | Owner |
|---|---|
| Windows endpoint/VM, account, disk, encryption, updates, and endpoint security | Customer/owner operator |
| Provider accounts, keys, billing, regional settings, and provider retention | Customer/owner operator |
| Local application data, backup schedule, restore drills, retention, and exports | Customer/owner operator |
| Application binaries, migrations, manifests, and supported procedures | DataLogicEngine release authority |
| Client keys, connector consent, scopes, firewall, and private gateway approval | Customer/owner operator |
| Production go/no-go and accepted residual risks | Product owner/release authority |

## Startup and readiness

The installed desktop owns process construction, installation identity, runtime
root and ACL checks, exclusive lock, configuration, service supervision,
migrations, routes/workers, readiness, lifecycle events, and shutdown. Do not
start backend modules by importing `app.py` or replace installed startup with a
development script.

Use the UI and authenticated Diagnostics to distinguish:

- `/live`: the backend process can answer;
- `/ready`: all mandatory startup gates passed;
- `/health`: safe aggregate health;
- capabilities: authenticated per-service and operation state;
- lifecycle events: signed desktop suspend/resume/time-change/logoff/shutdown.

A live process may correctly be not ready. Do not bypass a failure for an
unverified listener, missing service, incompatible schema, foreign runtime root,
unprotected volume, invalid ACL, unknown installation version, or unsigned/
unapproved release policy.

## Required services

| Service | Production responsibility | Failure behavior |
|---|---|---|
| PostgreSQL | Relational authority for identity, configuration, jobs, traces, consent, audit, and lifecycle state | Not ready; no SQLite substitution |
| Redis | Session/cache, rate/concurrency, content-free coordination, queue, stream, and cancellation | Not ready; no silent memory substitute |
| Neo4j | Durable graph authority | Degraded/not ready according to required capability; no fabricated graph result |
| ChromaDB | Vector storage and semantic retrieval | Required retrieval capability fails closed |
| app-owned S3-compatible object store | App-owned S3-compatible objects and required buckets | Required artifact path fails closed; no filesystem production fallback |

ADR-0010 selects SeaweedFS 4.40-dle.1 as the implementation for rebuilt
installed qualification. It is not production-authorized until the installed
independent gates pass. Internal database, object, supervisor, and diagnostic
ports must not be exposed to client machines.

## Provider operations

The supported providers are OpenAI and Google. The owner saves credentials
through Provider Connections or the approved protected source. The renderer and
gateway clients never receive plaintext provider credentials. A key may be
`stored` but is not `available` until a bounded live test succeeds.

Before enabling provider-backed use:

1. review provider contract, data categories, region, retention, and billing;
2. configure call, token, spend, retry, and timeout controls;
3. perform the installed bounded test and verify exact provider/model identity;
4. inspect the content-free local usage/egress ledger;
5. test unavailable, invalid-key, rate-limit, quota, timeout, and cancellation
   behavior without duplicate spend or fabricated fallback.

Unknown price remains unknown. The application does not centrally manage the
owner's provider bill.

## Backup

Use only the coordinated backup operation. It shall quiesce or consistently
capture required stores, encrypt payloads with the user-supplied recovery
passphrase, create a signed or hash-verified manifest, and exclude environment
files, provider/internal credentials, logs, and key material.

For every backup, record the product/schema versions, installation identity,
artifact path, size, hash, manifest verification, passphrase custodian, retention
class, and restore-test status. Never store the recovery passphrase in the app,
bundle, log, issue, or repository.

Create and verify a backup before upgrade, repair, rollback, destructive
migration, bulk deletion, or object-store migration.

## Restore and disaster recovery

1. Stop the desktop and all app-owned services through the approved lifecycle.
2. Preserve redacted incident evidence and the current root.
3. Select a compatible backup and verify its encryption envelope, manifest,
   hashes, product/schema versions, and installation constraints.
4. Restore into a new isolated root; never overwrite the active root in place.
5. Verify store identities, migrations, cross-store references, required buckets,
   ACLs, protected volume, and readiness without exposing credentials.
6. Atomically activate the restored root and preserve the previous root for the
   accepted rollback window.
7. Run provider-offline and representative local workflows before re-enabling
   external processing, clients, or connectors.

A signed clean-machine restore, retained-data upgrade, and independent recovery
review remain release gates.

## Retention and deletion

Define owner-approved retention for sessions/messages, traces/audit, ingestion
sources and chunks, simulation artifacts, MCP results, gateway jobs/results,
usage metadata, logs, support bundles, exports, and backups. Provider and
connector copies follow their external contracts.

Use the canonical deletion operation. Success requires reconciliation across all
applicable PostgreSQL, Redis, Neo4j, ChromaDB, app-owned S3-compatible object store, memory/local, and log
surfaces. A partial failure must be visible and repairable. Non-PII audit
tombstones and time-bounded backup remnants may remain only with a documented
basis. Exported files and snapshots are separate operator responsibilities.

## Diagnostics, logs, and support bundles

Diagnostics is authenticated and content-free. It may show safe runtime,
service, request, logging, resource, configuration-shape, and telemetry state,
but not provider credentials, authorization headers, prompts, documents,
provider payloads, request/response bodies, or decrypted backups.

Support bundles require owner preview and confirmation. Verify the preview
inventory and fingerprint, generate locally, confirm the SHA-256 sidecar, and
encrypt before approved sharing. The app does not upload a bundle. External
telemetry is disabled by default and requires a separate explicit opt-in; a DSN
alone must not enable egress.

## Client Gateway

The approved initial gateway is same-host. Issue each named application a
copy-once `ukg_` key with the minimum scopes, limits, expiry, and concurrency.
Record its owner and purpose. Test denial, rotation, revocation, job cancellation,
and client isolation. Clients receive no provider or data-service credentials.

`private_windows_gateway` is disabled and fails closed. It may be enabled only
after the exact signed release passes TLS certificate/name/chain/revocation,
Windows Firewall, two-machine client, key/mTLS identity, failure/recovery,
backup/restore, logging/redaction, update/rollback, and owner-approval evidence.
CORS, browser use, and public-internet exposure remain unsupported.

## MCP connector operations

Registration records but does not run one exact absolute command. Before first
start, review the executable and argument fingerprint, approved file root,
granular scopes, credentials, expected tools/resources/prompts, timeout, and
data handling. Credentials use Windows DPAPI and are never returned to the UI.

Treat connector output as untrusted. On compromise or drift: stop the connector,
revoke consent and credentials, preserve redacted hashes/audit evidence, verify
the process tree is terminated, and require a new fingerprint and acceptance
before restart. Network targets and shell/package-runner authority are outside
the initial connector contract.

## Incident response

1. Classify severity and protect people/data before availability.
2. Stop the affected operation or external path without deleting evidence.
3. Record correlation/run/operation IDs, safe error codes, product/installer
   identity, service state, time, and recent lifecycle action.
4. Preview a redacted support bundle and collect only approved evidence.
5. Repair the root cause; do not disable the gate or substitute a development
   fallback.
6. Rerun the relevant normal, adversarial, failure, recovery, and regression
   matrix against the exact replacement build.
7. Record owner/reviewer disposition and any residual risk with expiration.

Security vulnerabilities follow `SECURITY.md`. Common user-facing recovery is
in `docs/TROUBLESHOOTING_SUPPORT_GUIDE.md`.

## Routine operating checklist

- Confirm product, installer, and release-manifest identity.
- Review readiness and required service identity/state.
- Review provider availability, budgets, and usage metadata.
- Review backup age, verification, retention, and last restore drill.
- Review storage growth, disk margin, logs, support bundles, queues, and jobs.
- Review failed/partial deletions, migrations, ingestion reconciliation, and
  simulation/MCP/gateway operations.
- Review client keys, connector consent, external telemetry, firewall, and
  update-disabled state.
- Review security findings, dependency alert 389, legal/signing authority, and
  retained Phase 15 qualification gates before any release claim.

## Shutdown and maintenance

Use the desktop's bounded graceful shutdown. If forced cleanup occurs, verify
process-tree termination, locks, interrupted jobs/migrations, and store
consistency before restart. For repair, upgrade, rollback, uninstall, and data
choice, follow `docs/INSTALLATION_GUIDE.md`. Production/public release remains
**NO-GO** until the release-readiness record says otherwise.
