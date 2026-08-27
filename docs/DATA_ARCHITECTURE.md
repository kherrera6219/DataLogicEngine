# DataLogicEngine data architecture and schema specification

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ENG-002 |
| Title | Data architecture and schema specification |
| Document version | v1.2.2 |
| Product version | 4.4.3 |
| Status | active |
| Audience | Data, platform, security, privacy, quality, operations, and professional reviewers |
| Owner | Data Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Implemented store adapters/schemas, migration and lifecycle contracts, ADRs, and qualification evidence |
| Confidentiality | Public |
| Last reviewed | 2026-08-21 |
| Next-review trigger | Store, schema, migration, classification, retention, encryption, backup/restore, or object-store decision change |
| Requirements and evidence | Product requirements, schema/migration tests, lifecycle reports, ADR-0006/0010, and Phase 3/4/9/11 evidence |

## Scope and invariants

Production data is app-owned, installation-bound, and local to the supported
Windows desktop or VM. PostgreSQL, Redis, Neo4j, ChromaDB, and app-owned S3-compatible object store are required
production services; SQLite, memory-only coordination, embedded vector mode, and
filesystem object storage are development/bootstrap/repair boundaries only.
Production readiness must not silently substitute them.

Every durable workflow has one named authority. Derived graph, vector, object,
cache, stream, export, and UI views must remain traceable to that authority and
must report partial/inconsistent state instead of fabricating success.

Under Phase 19, a Knowledge Algorithm never becomes a second data authority.
Each KA has one implementation owner and one primary owning subsystem. Pure KAs
return typed analysis or validation results; effect-oriented KAs return
proposals. Only the authoritative ingestion, retrieval, graph, memory,
simulation, MCP, provider, security, operations, or lifecycle service may write
state, and only its policy-, idempotency-, transaction-, and reconciliation-
bound receipt may be recorded as `applied_effect`. Partial cross-store work
remains partial and cannot be promoted to validated knowledge.

## Store responsibility map

| Store | Authoritative responsibilities | Prohibited production use |
|---|---|---|
| PostgreSQL | Installation/user configuration, provider records, sessions/messages, causal runs, traces/evidence/claims, ingestion jobs/files/chunks/revisions, simulations/checkpoints, MCP registry/consent/lifecycle, gateway clients/jobs, audit and migration ledgers | Replacement by SQLite or automatic schema creation |
| Redis | Sessions/cache, rate and concurrency limits, bounded queues/streams, cancellation, and content-free job/event coordination | Durable content authority or silent in-memory fallback |
| Neo4j | Durable knowledge graph nodes, edges, provenance, and graph revisions | Unverified external/Aura authority |
| ChromaDB | Vector collections, embeddings, semantic retrieval, and revision state | Hosted vector authority or untracked embedded fallback |
| app-owned S3-compatible object store | Required original/normalized knowledge objects, trace exports, simulation artifacts, deliverables, graph/evaluation assets, gateway results, MCP results, audit objects | Filesystem or public cloud bucket production fallback |
| Unified/Truth memory | Structured reasoning memory, governed trust/promotion, explainability, integrity/recovery state | Independent source of truth that bypasses PostgreSQL/provenance authority |

ADR-0010 defines the app-owned S3-compatible object-store capability and selects
SeaweedFS 4.40-dle.1 for rebuilt installed qualification after the engineering
Replacement Control gates passed. Production authorization remains false until
the retained installed and independent release gates pass.

## Required object namespaces

The production object service must provide at least these isolated app-owned
buckets or equivalent namespaces:

`audit-logs`, `simulation-artifacts`, `deliverables`, `graphs`,
`evaluation-data`, `trace-exports`, `gateway-results`, `knowledge-sources`, and
`mcp-results`.

Clients and the renderer never receive object-store credentials or direct object
URLs that bypass authorization. PostgreSQL retains durable identity, ownership,
hash, lifecycle, retention, and cross-store references.

## Core data domains

- Installation and identity: installation ID/version, runtime root, owner, locks,
  service identity, protected credentials, and lifecycle operations.
- Governed requests: admission, request/session/client identity, policy, routing,
  provider/tool attempts, executed stages, evidence, claims, confidence,
  convergence, response, audit, and usage metadata.
- Sessions and messages: the durable Session Library; `/projects` paths are
  compatibility names, not an independent workspace/project data model.
- Knowledge: source/job/file/chunk/corpus/revision authority, original and
  normalized objects, defense/parser outcome, graph/vector materializations,
  retrieval/provenance state, update/repair/deletion.
- Simulation: request, budget, lifecycle, checkpoint, event, artifact, result,
  validation, and causal run bindings.
- MCP: exact command/fingerprint, scope/file root, consent, encrypted credential
  reference, process/lifecycle, discovery, call, safe error, result hash/content.
- Client Gateway: client identity, protected key verifier, scopes/limits,
  requests/jobs/results/cancellation, idempotency, usage, audit, and trace access.

## Classification and protection

| Class | Examples | Required handling |
|---|---|---|
| Restricted secret | Provider/connector/internal-service credentials, install secret, recovery passphrase, certificate private key | Never log/export; DPAPI or approved encrypted store; least privilege; rotate/revoke |
| Sensitive content | Prompts, documents, messages, retrieved chunks, tool inputs/results, evidence snippets, AI output | Local by default; scoped access; encrypted/protected storage; redact support paths; governed egress |
| Controlled operational | Trace/audit metadata, hashes, safe errors, client identity/scopes, consent, usage/egress metadata | Authenticated access; integrity and retention controls; content-free where specified |
| Public | Approved documentation, public schemas, non-sensitive release metadata | Version, integrity, and authority controls |

Temporary, staging, export, backup, and support paths inherit the highest
classification of their content. Production staging/spool roots remain below the
protected runtime root and are bounded and cleaned after committed lifecycle
transitions.

## Migration and schema rules

1. `config/product-versions.json` and the versioned migration ledger define the
   supported product/schema boundary.
2. Required per-store migrations run before readiness in dependency order.
3. Production rejects newer, unsupported, unversioned populated, or partially
   migrated data.
4. `AUTO_CREATE_SCHEMA`, `db.create_all()`, and ad hoc store mutation are not
   production migration mechanisms.
5. Each migration is idempotent or safely resumable, records start/result/hash,
   and has backup, failure, recovery, and rollback evidence.
6. Cross-store changes do not report success until required references, hashes,
   and revisions reconcile.

The 2026-08-10 installed engineering candidate adopted the populated 0.1.1
SQLite authority once into PostgreSQL with an immutable recovery copy, verified
receipt, and synchronized sequences. It preserved 22,068 listed relational rows,
20 graph nodes/18 relationships, and eight objects. Exact signed clean-machine
migration, broader upgrade/rollback, recovery, remnant, and independent review
remain release gates.

## Backup, restore, and deletion

Coordinated backup captures a consistent required-store set, encrypts it using a
user-supplied recovery passphrase, creates a signed/hash-verified manifest, and
excludes secrets, environment/settings files, logs, and key material. Restore
verifies and migrates an isolated clean root before atomic activation and keeps
the prior root for the approved rollback window.

## Training dataset exporter architecture

The candidate exporter in `backend/dataset_exporter/` reads the persisted
`TraceRun` input/final-answer fields and recorded `TraceStage` status. Database
exports require completed/released trace evidence, nonempty input and answer,
the requested confidence threshold, and no quarantine or `never_persist`
marker. Missing release evidence fails closed.

The owner API currently permits SFT conversational records and PRM candidate
records whose labels are derived from recorded stage status; those labels are
not human-validated rewards. DPO conversion exists only at the library boundary
and requires a real rejected answer, rejection reason, and rejected source ID.
The current database/API does not manufacture or claim preference pairs.

Every serialized string is passed through the non-optional privacy redactor.
API output is confined below the app-owned runtime `datasets` directory and
uses an application-generated artifact name. JSONL is always available;
Parquet uses allowlisted compression and falls back to JSONL when PyArrow is
not installed.

Optional runtime usage capture is a separate owner flag
(`training_data_capture_enabled`, default off). When enabled, post-release
governed traces may be redacted and staged under `runtime_root/datasets/capture`
after `TraceRun` persistence succeeds. Staging is not training, does not enable
DPO, and cannot bypass quarantine, `never_persist`, or missing release evidence.
Capture failures never roll back the governed trace.

Deletion reconciles all applicable SQL, Redis, graph, vector, object, memory,
local, and log surfaces and reports partial failure. Shared chunks remain only
while an active source references them. Non-PII tombstones and backup remnants
require a documented basis and retention. Exports, snapshots, external provider/
connector copies, and immutable media are separately controlled.

## Retention

Retention is configuration and deployment-policy driven. The owner records the
period and trigger for sessions/messages, traces/audit, knowledge sources/chunks,
simulations/artifacts, gateway jobs/results, MCP results, usage metadata, logs,
support bundles, exports, and backups. Specific periods must not be inferred from
historical examples. Provider and connector copies follow their contracts.

## Integrity and reconciliation

Required records carry stable IDs, ownership, timestamps, versions, and hashes
appropriate to their domain. Ingestion readiness requires PostgreSQL job/file/
chunk/revision authority to match required knowledge objects, Neo4j, and ChromaDB.
Gateway and MCP large results require PostgreSQL reference/hash parity with the
encrypted object. Trace exports and coordinated backups verify manifests before
use. Memory promotion records provenance and trust and fails closed on integrity
drift.

## Validation status

Schema parity, migration coordination, populated engineering backup/restore,
seven-surface deletion, five-service operations, knowledge reconciliation,
memory integrity, gateway, simulation, and MCP data contracts have engineering
evidence. The app-owned Podman delivery and populated retained-data adoption
passed on the 2026-08-10 engineering candidate. Protected-volume/ACL Windows
matrix, signed clean-machine restore/deletion-remnant scan, broader lifecycle
qualification, and independent durability/security/license review remain
release blockers. KA ownership, selector, effect-port, and causal trace source
integration passed through CP19-L; the exact signed rebuilt-installed data/effect
matrix remains blocked through CP19-M.
