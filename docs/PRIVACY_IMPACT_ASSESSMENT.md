# DataLogicEngine privacy impact assessment and data inventory

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ASR-005 |
| Title | Privacy impact assessment and data inventory |
| Document version | v1.1.1 |
| Product version | 4.4.2 |
| Status | not_evaluated |
| Audience | Product owner, privacy/security, data engineering, operations, legal reviewers, and release authority |
| Owner | Privacy Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Implemented data flows, privacy/provider/connector controls, retention/deletion contracts, and current evidence gaps |
| Confidentiality | Public |
| Last reviewed | 2026-08-11 |
| Next-review trigger | Purpose, data category, subject group, store, provider/connector, retention, deletion, telemetry, region, or legal basis change |
| Requirements and evidence | Product requirements, privacy notice, data/security architecture, tests, provider/connector records, and independent review |

## Assessment status and scope

This is the engineering privacy-impact baseline for the single-owner local-first
Windows product. It is `not_evaluated` for production because deployment-specific
legal basis, jurisdiction, provider/connector contracts, retention periods,
children/high-risk-use restrictions, installed no-egress/deletion/remnant proof,
and independent privacy/legal review are not complete.

The 2026-08-10 installed engineering candidate preserved existing app-owned data
through verified one-time adoption. Installed redaction/no-egress, provider,
deletion/remnant, retention/legal-basis, and independent privacy review remain
open; the `not_evaluated` production status is unchanged.
The newer August 11 local artifact has not completed installed privacy,
redaction, deletion, or no-egress validation.

The default product owner/vendor does not operate customer data or provider
accounts as a multi-tenant SaaS. The customer/owner controls the Windows system
or VM, provider/connector accounts, data, exports, backups, and policy. That model
reduces vendor custody but does not eliminate local, provider, connector, client,
export, support, or administrator privacy risk.

## Purpose and necessity

Data is processed to provide governed AI requests, evidence/trace review,
sessions, knowledge ingestion/retrieval, graph/vector/memory, simulations,
approved tools/connectors, same-host client integration, administration,
security/audit, diagnostics/support, backup/recovery, deletion, and release
assurance. Each enabled feature must limit collection and retention to what its
documented contract requires and expose an owner control or justified lifecycle.

High-risk or regulated use is not approved by default. DataLogicEngine is not an
autonomous professional authority and must not be the sole basis for decisions
affecting rights, health, safety, employment, credit, housing, legal status, or
essential services.

## Data inventory

| Category | Examples | Local authority/location | External path |
|---|---|---|---|
| Identity/configuration | Windows/install identity, sessions, preferences, provider/client/connector config | PostgreSQL and protected local settings | None by default |
| Restricted secrets | Provider/connector/service keys, install secret, certificate key, recovery passphrase | DPAPI/approved protected store; passphrase not persisted | Provider/connector auth only; never UI/support/log |
| User content | Prompts, messages, documents, notes, uploads, normalized/chunked content | PostgreSQL, app-owned S3-compatible object store, Neo4j, ChromaDB, memory | Selected provider/connector/client/export path |
| AI context/output | Retrieved evidence, personas/context, tool results, model input/output | Trace/data authorities according to workflow | One configured provider when owner initiates |
| Trace/audit | Runs, stages, policy, claims/citations, confidence, convergence, safe errors | PostgreSQL/object/memory/log authorities | Scoped client/export/support metadata |
| Knowledge/simulation | Sources, provenance, graph/vector revisions, checkpoints/artifacts/results | PostgreSQL, app-owned S3-compatible object store, Neo4j, ChromaDB, memory | Provider/tool/export if initiated |
| Gateway/MCP | Client identity/scopes/jobs, connector fingerprint/consent/calls/result hashes | PostgreSQL, Redis, encrypted app-owned S3-compatible object store objects | Approved client or local connector |
| Operational | Health/readiness, resource state, content-free usage, redacted logs/crash/support manifests | Local app-owned records/logs | External telemetry only by explicit opt-in; reviewed bundle sharing |
| Backup/export | Encrypted coordinated backups, trace/data exports, bundle archives | Owner-selected protected local/off-device storage | Wherever owner explicitly stores/shares |

The approved requirement is the capability **app-owned S3-compatible object
store**. ADR-0010 selects SeaweedFS 4.40-dle.1 for rebuilt installed
qualification; telemetry/logging, protected-volume, retention, deletion,
security, and independent license behavior remain installed release gates.

## Data flows and recipients

### OpenAI and Google

For an owner-initiated governed request, selected prompt/message content,
retrieved text/chunks, persona/context, tool results, and provider/model metadata
may be sent to one configured provider. Provider terms, region, retention,
enterprise controls, billing, and account security are the owner's responsibility.
The renderer does not call providers or receive their credentials.

### MCP connectors

The initial approved connector is an owner-consented local stdio process bound
to exact command fingerprint, file root, scopes, and encrypted credentials. It
may process selected input/results and may itself egress according to its code.
Network connectors are not approved. Result content remains untrusted.

### Client Gateway

Approved same-host applications may submit content and receive scoped results/
trace metadata using a copy-once key. They receive no provider or internal-
service credentials. Private Windows network access is disabled pending TLS/
firewall/two-machine qualification; public/browser access is unsupported.

### Exports, support, and telemetry

Exports go to owner-selected locations. Diagnostics/support bundles are local,
content-free/allowlisted, previewed, re-redacted, hashed, and not uploaded by the
app. External telemetry is disabled by default and requires explicit opt-in; a
DSN alone cannot enable it.

## Retention and deletion

The deployment must approve periods/triggers for sessions/messages, traces/audit,
knowledge sources/chunks, simulations/artifacts, gateway jobs/results, MCP
results, usage metadata, logs, bundles, exports, and backups. Historical examples
are not policy. Provider/connector/client copies follow their contracts.

The canonical deletion path reconciles applicable PostgreSQL, Redis, Neo4j,
ChromaDB, app-owned S3-compatible object store, memory/local, and log surfaces and reports partial failure.
Shared chunks remain only while referenced. Non-PII tombstones and backup
remnants require a documented basis/expiry. Exports, snapshots, immutable media,
and external copies require separate action; secure erasure cannot be guaranteed
for every SSD, snapshot, or third party.

## Risk assessment

| Risk | Current control | Residual/open evidence |
|---|---|---|
| Provider/connector over-disclosure | Preflight categories, owner initiation, scopes/consent, backend-owned calls | Installed content-category/no-egress and contract review |
| Secret/content in logs/support | Redaction, allowlist, preview/fingerprint, no upload | Installed all-output canaries and independent review |
| Cross-client/owner access | Single-owner auth, client scopes/ownership, no direct stores | Installed gateway isolation/penetration review |
| Excessive retention/remnants | Owner controls, bounded jobs, coordinated deletion | Ratified periods, installed partial/remnant/backup expiry proof |
| Backup/export exposure | Encryption/manifests, user passphrase, local preview | Custody policy, clean restore, sharing/legal process |
| Untrusted AI/tool output | Injection/secret checks, evidence/claim validation, human oversight | Live provider/hostile connector/human acceptance |
| Training dataset export | Mandatory secret/PII redaction, app-owned output root, explicit release and containment screening, owner-authenticated manual action | Pattern redaction is defense in depth, not proof that all sensitive context is absent; review artifacts before external use |
| Endpoint compromise | Protected volume/ACL, DPAPI, least privilege | Supported-Windows matrix and endpoint operating policy |
| Misleading AI reliance | Limitations, not-measured, trace/evidence review | Packaged copy/usability and blinded human review |
| Selected object-store privacy drift | Production authorization false and exact locked implementation | Installed security/privacy/license/Windows qualification |

## Individual/owner controls

Supported controls include review/export/deletion for sessions, traces, knowledge,
memory, usage metadata, and other named workflows; provider/model and processing
preferences; connector consent/revocation; client-key lifecycle; support preview;
telemetry opt-in; backup/restore; and uninstall data choice. Exact installed
discoverability, accessibility, durable effects, deletion completeness, and
response timing remain validation gates.

## Required approvals before production

- Deployment purpose, subject groups, prohibited/high-risk uses, jurisdictions,
  legal basis, notices/consent, data roles, contacts, and request process.
- Provider, connector, client, subprocessor, region, retention, and transfer review.
- Owner-approved retention schedule and deletion/remnant/backup handling.
- Signed installed privacy UI, egress, telemetry, support, export/delete, backup/
  restore, provider/connector/client, and all-output canary evidence.
- Independent privacy/security and owner legal review with findings resolved or
  time-bounded accepted risk.

Until these are complete, this assessment remains `not_evaluated` and
production/public release is **NO-GO**.
