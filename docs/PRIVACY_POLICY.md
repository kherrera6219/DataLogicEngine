# Privacy Policy

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.15.0 |
| Last updated | 2026-07-14 |
| Effective date | 2026-05-30 |
| Status | Active |
| Owner | Privacy + Security Engineering |
| Review cadence | Every 60 days |

## 1. Introduction

DataLogicEngine is a local-first knowledge graph workspace for governed AI reasoning. This Privacy Policy explains how the application collects, uses, stores, exports, deletes, and protects information across the current Local-First Desktop build, the same Windows application running inside a Windows virtual machine, and controlled web/cloud deployments where configured.

This policy is written for the current architecture: local-first storage, configurable AI providers, DMRF/Truth Engine traces, privacy controls, user export/delete flows, and trace/export integrity.

## 2. Deployment modes and data residency

Data handling depends on deployment mode.

| Mode | Description | Data residency |
|---|---|---|
| Local-first desktop | Windows 11 desktop/Electron application with loopback backend and app-owned local stores. | Application data is stored on the local machine unless the user/configuration sends selected content to configured AI providers or connectors. |
| Windows VM | Same Windows app stack running inside a Windows VM. | Application databases remain internal to the installed app stack on the VM. |
| Controlled web/cloud | Hosted deployment where explicitly configured. | Data residency depends on the deployment architecture, configured database/storage services, provider settings, and organizational policy. |

The default local-first architecture does not require externally hosted PostgreSQL, Redis, Neo4j, ChromaDB, vector database, or object-store services as runtime database sources.

### Phase 3 local data-plane status

The current engineering profile keeps PostgreSQL, Redis, Neo4j, ChromaDB, and
object-store traffic on installation-specific loopback endpoints inside an
app-owned rootless Podman network. Service credentials are generated per
installation and protected locally. The profile does not authorize a cloud
database or hosted object store as the production data authority.

The qualification object service is SeaweedFS, but it is not approved for
production and does not change this policy's MinIO-specific production
architecture. Its telemetry behavior, logs, TLS, data-at-rest limitations,
retention, deletion, vulnerability posture, installer delivery, and independent
legal/security review must be resolved before final selection. Phase 4 now
provides cross-store retention, deletion, migration, backup, and restore
engineering contracts without authorizing the candidate for production.

## 3. Information we collect or store

Depending on enabled features, DataLogicEngine may collect or store:

1. **Local identity information** — local Windows profile/session metadata used for local desktop behavior.
2. **Account/session information** — username, session metadata, API keys/tokens where enabled (single-mode / OS-level auth — no multi-user roles or MFA).
3. **User content** — prompts, chat messages, uploaded documents, local corpus data, notes, project data, and knowledge records you explicitly input or ingest.
4. **AI processing context** — selected prompt context, retrieved evidence, graph context, DSQP persona metadata, model/provider metadata, and trace/run metadata.
5. **Trace and audit data** — DMRF steps, TruthGate decisions, TruthCore workflow state, evidence, claims, policy decisions, memory events, export records, and audit logs.
6. **Technical data** — timestamps, device/runtime information, application logs, route metrics, error reports, health/readiness/metrics data, and local storage status.
7. **Provider/connector configuration** — AI provider configuration, MCP connector/server configuration, scopes, and credentials where configured.
8. **Privacy preference data** — AI processing preferences, history/storage preferences, notification preferences, export/delete requests, consent records where enabled.

## 4. How we use information

DataLogicEngine uses information to:

1. provide local-first AI reasoning, knowledge graph, trace, and memory features;
2. authenticate and authorize users or local desktop sessions;
3. execute configured AI provider or MCP connector requests;
4. build traces, evidence, claims, personas, and audit records;
5. support export/delete/privacy workflows;
6. prevent abuse, fraud, prompt injection, unauthorized access, and security threats;
7. monitor health, performance, reliability, and release readiness;
8. comply with legal, security, audit, and operational obligations where applicable.

## 5. Local-first storage

In local-first desktop mode, application data is stored in local app-owned stores such as:

```text
databases/postgresql/
databases/redis/
databases/neo4j/
databases/chroma/
databases/objects/
databases/memory/memory_graph.json
```

Depending on configuration, local storage can include:

1. SQL records;
2. graph records;
3. vector embeddings;
4. local object-store artifacts;
5. UnifiedMemory JSON persistence;
6. TruthMemory audit/explainability records;
7. trace export bundles and manifests.
8. Client Gateway names, copy-once key verification metadata, scopes, limits,
   request/job/trace identifiers, content-free usage/audit state, encrypted
   durable requests/results, and retained large encrypted job-result objects.

Local-first does not mean no data ever leaves the machine. Data can leave the machine when a user or deployment configures cloud AI providers, MCP connectors, external APIs, web/cloud deployment, or export/share workflows.

Approved Client Gateway applications may submit prompt/message content to the
local service. The application principal is not a DataLogicEngine user or tenant.
Its secret is shown once, only protected verification material is retained, and
provider credentials are never returned. Client-owned trace reads expose safe
stage metadata; evidence references require a separate scope and exclude stored
snippets. Logs, metrics, lifecycle audit, and support output omit request/result
content and authorization headers.

## 6. Cloud AI providers and third parties

To provide advanced reasoning, DataLogicEngine may send selected prompts,
retrieved text or document chunks, persona/context material, tool results, and
provider/model metadata to one configured AI provider for an owner-initiated
governed request. The chat preflight identifies the applicable categories before
external processing. The renderer cannot contact providers directly.

Current cloud model providers exposed by the active app are:

1. OpenAI;
2. Google Gemini.

Archived docs and future integrations may mention other providers, but they are not part of the current user-facing model-selection surface unless explicitly reintroduced and documented.

Data handling by these providers is governed by the provider account, API terms, regional settings, retention settings, enterprise agreement, and user/deployment configuration.

You can control provider behavior through application settings where available,
including AI model/provider selection, AI processing preferences, server-owned
call/token/spend limits, and the local usage-ledger controls. A configured key is
not reported available until a bounded live test succeeds.

## 7. MCP connectors and external tools

The initial connector contract supports owner-approved local stdio processes.
Network destinations are rejected pending separate qualification, but a local
connector may itself process selected request data, tool inputs, metadata, or
retrieved context. Future network-capable connectors would require an updated
privacy/egress contract and owner approval.

Connector data handling depends on:

1. the connector being used;
2. the tool input/output schema;
3. API-token, connector credential, or connector-scope configuration;
4. local connector configuration;
5. the external service's own privacy and retention rules.

Registration does not run the connector. Before first use, the owner reviews the
exact executable/arguments fingerprint, approved file root, and granular scopes.
Credential values are encrypted with Windows DPAPI and are never returned to the
renderer. PostgreSQL retains consent, lifecycle, request/result hashes, operation,
scope, duration, trust, and safe error metadata. Redis live events are
content-free. Small governed result content may be retained in PostgreSQL and
large results in the app-owned `mcp-results` object bucket under normal
retention/export/deletion rules.

All connector output is treated as untrusted and checked for secret disclosure
and prompt-injection indicators before any later governed workflow may use it.
Execution-history responses omit retained result content.

## 8. Trace, audit, and export data

DataLogicEngine creates trace and audit records to support explainability, debugging, compliance, and security.

Trace data may include:

1. run IDs and correlation IDs;
2. user/session context;
3. DMRF steps;
4. TruthGate decisions;
5. evidence and claim records;
6. persona/DSQP metadata;
7. policy decisions;
8. memory events;
9. artifacts and export manifests.

Trace exports may include section hashes, bundle hashes, optional HMAC signatures, optional encrypted payloads, and manifest metadata. Export integrity is designed to help users, reviewers, and auditors verify that an exported trace bundle has not been modified.

Phase 7 also keeps a local content-free provider usage/egress ledger. It records
provider/model, purpose, governed stage, retry/attempt identity, token counts,
latency, status/failure class, disclosed data categories, timestamps, and a
request/session reference. It does not store provider credentials or
prompt/response content. Unknown price is stored as unknown, not zero. The local
owner can review, export, or explicitly reset this ledger.

## 9. Data protection

Current protection measures include:

1. local-first storage by default for desktop/VM mode;
2. local filesystem permissions and ACLs where applicable;
3. desktop local-auth controls for loopback/Electron runtime;
4. Windows DPAPI protection for desktop install, provider, and saved internal-service credentials;
5. field-level encryption where implemented by the application model/service layer;
6. CSRF, CORS, trusted-host, rate-limit, and session controls for API routes;
7. TruthGate and DMRF injection defense for governed AI flows;
8. export integrity hashing/signing/encryption options;
9. signed release workflow for public Windows distribution;
10. opaque Electron picker tokens so selected ingestion/backup paths are not exposed to the renderer;
11. exclusion of `.env`, secret/settings files, logs, and key material from desktop backups.
12. AES-256-GCM encryption and a signed/hash-verified manifest for portable
    coordinated backups using a user-controlled recovery passphrase;
13. fail-closed production checks for protected Windows volumes and restricted
    runtime-root ACLs.
14. DPAPI encryption for Windows offline replay payloads, with bounded item/byte
    counts and expiry. Non-Windows Fernet replay is development/test-only;
    production desktop replay fails closed without DPAPI.

Implementation note: field-level encryption writes new payloads with AES-256-GCM; legacy Fernet-encrypted values remain decryptable for backward compatibility, and a Windows DPAPI helper protects local data.

Provider content leaves the machine only through the backend when the user has
configured a provider and initiates a governed request. The packaged renderer's
content policy does not allow direct provider-network access.

## 10. Data retention

Retention depends on deployment configuration and enabled features.

Default guidance:

1. **Chat and user content** — retained until deleted by the user/admin or removed by configured retention policy.
2. **Local documents and ingested content** — retained locally until deleted or purged by the user/admin.
3. **Trace and audit data** — retained according to audit/security policy; older guidance used 90 days for security logs.
4. **Export bundles** — retained wherever the user/admin saves them; exported files may remain outside the application after download.
5. **Provider data** — governed by the configured provider's own retention and API policy.
6. **Connector data** — governed by connector/service policy and local audit settings.
7. **Client Gateway jobs** — encrypted requests/results and Redis coordination
   state expire under the configured bounded job policy. Large retained results
   follow the same policy in the app-owned `gateway-results` S3 bucket.
8. **Client-key audit tombstones** — key secret/verification material is
   destroyed on deletion while non-secret lifecycle identity may be retained for
   referential audit and incident review.

Administrators should configure and document retention policies for production or shared deployments.

## 11. Your rights and controls

Where enabled, users can:

1. access/export data through `Settings > Privacy`;
2. request deletion through `Settings > Privacy`;
3. control AI processing preferences;
4. select preferred AI provider/model where enabled;
5. disable or limit AI history/storage where supported;
6. manage notification preferences;
7. remove local data through uninstall options such as `-KeepData` or `-DeleteData` for Windows desktop uninstall flows.

The canonical deletion operation reconciles PostgreSQL, Redis, Neo4j, ChromaDB,
MinIO, local JSON, and logs. It records a non-PII tombstone and does not report
success when any required surface fails. Approved immutable remnants require a
disclosed retention basis. Backup copies expire under the backup-retention
policy and may outlive active-data deletion until that expiry.

Deletion timing depends on deployment policy, backup retention, and explicit
legal/security obligations. Secure deletion cannot be guaranteed on every SSD,
virtual disk, snapshot, or retained backup.

## 12. Security and incident response

Privacy incidents may include:

1. PII leakage in response, logs, traces, exports, or notifications;
2. unauthorized access to user data;
3. local data-store exposure;
4. connector over-sharing;
5. provider misconfiguration;
6. export integrity failure;
7. local storage permission failure.

Incident procedures are defined in `docs/OPERATIONAL_RUNBOOKS.md`.

## 13. Children's data

DataLogicEngine is intended for professional, enterprise, technical, and local-user workflows. It is not designed for use by children.

## 14. Changes to this policy

This policy should be updated whenever data collection, AI provider behavior, connector behavior, trace/export behavior, retention policy, or deployment mode materially changes.

Active privacy documents must include document version and update date metadata.

## 15. Contact

Privacy questions or requests should be sent to:

```text
privacy@datalogicengine.com
```

Use this contact only when the mailbox is operational for the project or deployment. Otherwise, use the administrator/contact process defined for the deployment.

## Phase 9 local knowledge handling

Desktop-selected sources are copied into an app-owned staging area before
parsing; renderer code does not retain unrestricted filesystem authority. The
local data plane may retain the approved original, normalized content, chunks,
hashes, defense outcome, graph/vector materializations, retrieval decisions,
and last-retrieval state. Original and normalized payloads reside in the
`knowledge-sources` object bucket; Redis coordination contains no source text.

Deleting a source initiates reference-aware reconciliation across PostgreSQL,
Neo4j, Chroma, required objects, and provenance-linked UnifiedMemory records.
Shared chunks remain only while another active source references them. Memory
review/export/delete/compaction/recovery controls are owner-only. Installed
backup, deletion-remnant, and recovery proof remain release gates.

## Phase 13 diagnostics, support, and telemetry handling

System Diagnostics exposes authenticated content-free runtime, service,
request, logging, resource, configuration-shape, and external-telemetry state.
It does not expose provider credentials, authorization headers, prompts,
documents, provider payloads, request/response bodies, or decrypted backups.

Support bundles are created only after explicit owner preview and confirmation.
They include a versioned manifest, sanitized environment/configuration shape,
source/system/resource state, optional local probe/precheck metadata, and only
allowlisted bounded logs that are re-redacted during staging. Generic reports
and user content are excluded. The preview/export fingerprint must match; files
and archive are SHA-256 hashed, old exact-name app-owned archives are bounded,
and CLI encryption uses an interactively supplied passphrase. The application
does not upload a bundle.

Backend and renderer external telemetry are disabled by default and require a
separate explicit owner opt-in. A configured DSN or provider object alone cannot
enable egress. Local crash IDs remain available without external telemetry.
Installed no-egress and all-output canary evidence remains a release gate.

## Change notes for v2.15.0

1. Added the authenticated content-free Diagnostics, explicit support preview/
   confirmation/export, allowlist/redaction/hash/encryption/retention, and
   external-telemetry opt-in privacy contract.

## Change notes for v2.14.0

1. Documented the Phase 11 local-stdio consent, DPAPI, retention, untrusted-
   result, and network-disabled privacy boundary.

## Change notes for v2.13.0

1. Added the app-owned acquisition, original/normalized artifact, retrieval
   decision, memory trust, and reference-aware deletion privacy contract.

## Change notes for v2.12.0

1. Added Client Gateway principal, copy-once secret, encrypted job/result,
   trace/evidence scope, content-free audit, and bounded retention behavior.

## Change notes for v2.11.0

1. Added Phase 7 provider preflight categories, one-provider/no-silent-failover
   behavior, content-free local usage/egress records, and unknown-price truth.
2. Documented DPAPI-protected, bounded, expiring transient-failure replay and
   owner review/export/reset controls.

## Change notes for v2.10.0

1. Added the coordinated portable-backup, cross-store deletion/tombstone, and
   protected-volume/ACL privacy contracts.
2. Stated backup-retention and secure-deletion residual risks explicitly.

## Change notes for v2.9.0

1. Recorded the local loopback/rootless five-service engineering profile and
   per-install protected credentials.
2. Preserved the candidate-only SeaweedFS boundary and identified the privacy,
   retention, deletion, and recovery reviews that remain open.

## Change notes for v2.8.0

1. Added the Phase 1 DPAPI, renderer path-minimization, backup-exclusion, and backend-only provider-egress controls.

## Change notes for v2.7.0

1. Replaced stale OAuth-scope wording with current API-token, connector credential, and connector-scope privacy language.
2. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Updated policy for local-first desktop, Windows VM, and controlled web/cloud deployment modes.
3. Added AI provider, MCP connector, trace/audit/export, local storage, and privacy preference sections.
4. Added current data-protection controls and implementation caveat for Fernet/DPAPI versus AES-256-GCM target-state language.
5. Added retention, user controls, and incident-response alignment with current architecture.
