# DataLogicEngine privacy, provider, retention, and AI limitations notice

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-USER-005 |
| Title | Privacy, provider, retention, and AI limitations notice |
| Document version | v1.0.0 |
| Product version | 4.3.0 |
| Status | release_blocked |
| Audience | Users, evaluators, administrators, privacy/security reviewers, and release authority |
| Owner | Privacy Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Implemented data paths, provider/connector controls, retention/deletion contracts, and AI evaluation records |
| Confidentiality | Public |
| Last reviewed | 2026-08-10 |
| Next-review trigger | Data category, storage, provider, connector, gateway, telemetry, retention, deletion, AI limitation, or legal change |
| Requirements and evidence | Product requirements, architecture, privacy/security tests, AI system card, and Phase 7/9/11/13 evidence |

## Important current status

DataLogicEngine 4.3.0 is not approved for production or public distribution.
This notice describes the implemented and approved local-first contract while
clearly retaining installed, independent, legal, security, provider, deletion,
backup/restore, and release evidence that remains open. It is not a claim of
certification, regulatory approval, or legal suitability for a particular use.

The 2026-08-10 engineering installation preserved existing local data in the
app-owned services and did not create a fallback user database. Installed
all-output redaction/no-egress, provider, deletion/recovery, independent privacy,
and exact signed-artifact acceptance remain open.

## Local-first does not mean air-gapped

The approved product runs on a user-controlled Windows 11 system or Windows VM.
Application databases and services are app-owned and local by default. Selected
data can leave the device when the owner initiates a request to a configured
OpenAI or Google provider, starts an approved MCP connector operation, uses an
approved Client Gateway application, exports/shares data, or explicitly opts in
to external telemetry.

The product owner/vendor does not normally host customer data, control customer
provider accounts, or centrally manage customer API spend. The customer/owner is
responsible for the endpoint, provider and connector accounts, local retention,
backups, exports, and operating policy.

## Data the application may process or retain

Depending on enabled workflows, local app-owned stores may contain:

- local identity, installation, session, configuration, and preference data;
- prompts, chat messages, uploaded/ingested documents, normalized content,
  chunks, hashes, knowledge records, graph and vector materializations;
- selected retrieved evidence, persona/context material, tool inputs/results,
  provider/model metadata, and AI responses;
- causal runs, executed stages, policy decisions, claims, citations, confidence/
  quality components, convergence, memory, trace, audit, and export records;
- simulation requests, checkpoints, artifacts, budgets, and outcomes;
- MCP registry, fingerprint, scope, consent, lifecycle, safe error, and governed
  result records;
- Client Gateway identity, protected key-verification material, scopes, limits,
  jobs, request/result references, usage, and audit state;
- content-free diagnostics, resource/health state, redacted logs, crash IDs,
  support-bundle manifests, and update/release state.

Production responsibilities span PostgreSQL, Redis, Neo4j, ChromaDB, app-owned S3-compatible object store,
app-owned memory/local records, and approved log/export/backup locations.
ADR-0010 selects SeaweedFS 4.40-dle.1 as the implementation of the app-owned
S3-compatible object-store capability for rebuilt installed qualification.
Production use remains disabled until installed privacy/security acceptance.

## OpenAI and Google processing

For an owner-initiated governed request, the backend may send selected prompt or
message content, retrieved text or document chunks, persona/context material,
tool results, and provider/model metadata to one configured provider. The chat
preflight identifies applicable data categories before external processing. The
renderer does not directly call model providers and does not receive provider
credentials.

Provider processing is governed by the owner's provider account, API terms,
region, enterprise agreement, retention settings, and billing controls. A key
may be stored locally but is not reported available until a bounded live test
passes. The application keeps content-free usage/egress metadata such as
provider/model, purpose, stage, attempt, tokens, latency, status/failure class,
disclosed categories, time, and request/session reference. It does not put
prompt/response content or credentials in that ledger. Unknown price is shown
as unknown, never zero.

## MCP connectors and external tools

The initial supported connector is an owner-approved local stdio process.
Registration does not execute it. Before first use, the owner reviews the exact
executable/arguments fingerprint, file root, scopes, credentials, and expected
capabilities. Credentials are protected with Windows DPAPI and are not returned
to the UI.

A local connector may process selected tool input, request context, or retrieved
material and may itself communicate externally according to its code and
configuration. Connector output is untrusted, bounded, hashed, redacted, and
checked for secret disclosure and prompt-injection indicators. Network MCP
targets are outside the initial approved contract.

## Client Gateway

Approved same-host applications may submit prompts/messages to the local
versioned gateway. They receive a least-privilege copy-once DataLogicEngine key,
not provider credentials or direct database/object-store access. Client trace
reads are scoped and omit stored evidence snippets unless separately authorized.
Logs, metrics, errors, support output, and lifecycle audit omit authorization
headers and request/result content.

The private Windows gateway remains disabled until signed two-machine TLS,
certificate, firewall, identity, recovery, logging, update, and owner-approval
qualification passes. Browser/CORS and public-internet exposure are unsupported.

## Data protection

Implemented protections include installation-bound local authentication,
loopback/trusted-host/CORS/CSRF/session/rate controls, Windows DPAPI protection,
field encryption where specified, restricted paths and ACLs, production
protected-volume checks, backend-owned provider calls, opaque file-picker tokens,
bounded encrypted offline replay, governed connector scope/consent, trace/export
integrity, and fail-closed readiness.

Portable coordinated backups use a user-supplied recovery passphrase, encryption,
and an integrity-verified manifest. They exclude environment files, settings/
secret files, logs, and key material. Support bundles require preview and
confirmation, contain only allowlisted content-free/sanitized records, are
re-redacted, hashed, and created locally. The app does not upload them.

No control eliminates all risk. Installed protected-volume/ACL, canary/no-egress,
penetration, backup/restore, remnant, and independent security/privacy evidence
remain release gates.

## Retention

The owner must define retention for each deployment. Unless an approved policy
states otherwise:

- chats, sessions, ingested content, knowledge, traces, simulations, and local
  artifacts remain until the owner deletes them or a configured policy expires;
- provider copies follow provider terms and account settings;
- connector or external-service copies follow that service's policy;
- gateway requests/results and coordination state use bounded expiry, including
  encrypted large results in the app-owned object store;
- exports remain wherever the owner saves or shares them;
- support bundles remain in the selected local location until removed;
- backups may outlive active-data deletion until their approved retention ends;
- non-secret lifecycle/tombstone identity may remain for audit or incident needs
  after key verification material or active content is destroyed.

Specific time periods must come from the deployment's approved retention record,
not old examples in historical documents.

## User and owner controls

Where supported, the owner can review or control provider/model configuration,
AI processing preferences, session/history state, local usage metadata, ingested
sources, memory, traces, simulations, connectors, client keys/jobs, exports,
support bundles, and deletion operations.

The canonical deletion path reconciles every applicable PostgreSQL, Redis,
Neo4j, ChromaDB, app-owned S3-compatible object store, memory/local, and log surface and reports partial failure.
Shared chunks remain only while an active source still references them. Exported
files, provider/connector copies, backups, snapshots, immutable media, and legal/
security holds may require separate action. Secure deletion cannot be guaranteed
on every SSD, VM snapshot, retained backup, or external system.

## External telemetry

Backend and renderer external telemetry are disabled by default. A DSN or
provider object alone cannot enable egress; the owner must make a separate
explicit opt-in. Local crash identifiers and diagnostics remain available
without external telemetry. Installed no-egress proof is still required before
release.

## AI purpose and limitations

DataLogicEngine helps a human examine supplied information, controlled reasoning
steps, sources, evidence support, and system decisions. It is not an autonomous
authority and is not approved to replace qualified medical, legal, financial,
safety, employment, security, or regulatory judgment.

AI and retrieval output can be incomplete, stale, biased, ambiguous, unsupported,
or wrong. Failure modes include source gaps, retrieval misses, prompt injection,
provider drift/outage, ambiguous claims, imperfect evidence matching, tool or
connector error, and human disagreement. A displayed numeric value is evidence-
support coverage from named components, not a probability that an answer is
correct. Missing quality, freshness, provenance, claim-support, validation, or
confidence inputs are `not measured`.

The system may abstain, block, fail, cancel, or return an unavailable/offline
outcome. Review the trace, executed stages, provider/model identity, evidence,
claims, citations, limitations, and safe failure class. Human oversight is
mandatory for high-risk use and production release approval. OpenAI/Google
installed evaluations and blinded human acceptance remain pending.

## Children and prohibited reliance

The product is intended for professional, technical, and owner-controlled use,
not for children. Do not use it as the sole basis for decisions that materially
affect a person's rights, health, safety, employment, credit, housing, legal
status, or access to essential services.

## Questions, requests, and incidents

Use the deployment administrator or the support route in
`docs/TROUBLESHOOTING_SUPPORT_GUIDE.md` for privacy questions, access/export/
deletion requests, or retention clarification. Suspected vulnerability, secret
exposure, unauthorized access, or privacy incident must follow the private
reporting process in `SECURITY.md`, never a public issue.
