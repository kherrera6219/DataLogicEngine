# DataLogicEngine product requirements and acceptance specification

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-PROD-001 |
| Title | Product requirements and acceptance specification |
| Document version | v1.5.0 |
| Product version | 4.4.3 |
| Status | active |
| Audience | Product owner, engineering, quality, assurance, operators, and professional reviewers |
| Owner | Product Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Approved product boundary, production completion plan, implemented runtime, and acceptance evidence |
| Confidentiality | Public |
| Last reviewed | 2026-08-27 |
| Next-review trigger | Product scope, supported workflow, architecture, interface, risk, or release-gate change |
| Requirements and evidence | `PRODUCTION_COMPLETION_PLAN_2026.md`, `TODO.md`, architecture records, tests, and `reports/production-readiness/2026/` |

## Purpose

Define the approved product contract for DataLogicEngine 4.4.3 and the evidence
needed to claim that contract is satisfied. This document states requirements;
it does not convert an engineering checkpoint into production approval.

CP19-L passed on 2026-08-10 and one clean unsigned candidate installed and
reached readiness with retained app-owned data. The newer 2026-08-11 local
engineering build is a different, unsigned artifact that has passed integrity
but not installed-mode acceptance. CP19-M signed installed and all retained
acceptance requirements remain binding for the exact final artifact.

## Product definition

DataLogicEngine is licensed, local-first Windows software that provides a
versioned AI gateway, governed reasoning path, evidence and trace review,
knowledge and memory services, controlled connectors, and a desktop application
for configuration, administration, audit, observability, support, and validation.
The built-in chat is the reference client for the same governed path exposed to
approved applications, agents, and chatbots.

The customer or owner controls the Windows system or VM, provider accounts and
keys, connector credentials, local data, retention, backups, and operating
policy. The approved product is not a vendor-operated multi-tenant SaaS.

## Supported product boundary

| Area | Approved contract |
|---|---|
| Operating system | Windows 11 x64 desktop or an owner-controlled Windows VM |
| Application | Electron desktop shell with a backend bound to loopback by default |
| Integration | Versioned same-host API gateway; private Windows gateway only after its separate qualification |
| Identity | Single owner/operator with Windows and installation-bound controls; not multi-tenant identity |
| Providers | Owner-configured OpenAI or Google credentials and approved manifest models |
| Data plane | App-owned PostgreSQL, Redis, Neo4j, ChromaDB, and app-owned S3-compatible object store production services |
| Connectors | Owner-approved local MCP stdio processes within recorded scope and consent |
| Distribution | Signed, timestamped Windows installer after all release authorities pass |

The product requirement is the capability **app-owned S3-compatible object
store**. ADR-0010 selects SeaweedFS 4.40-dle.1 for rebuilt installed
qualification after the engineering contract, durability, backup/restore,
security, licensing, migration/rollback, Windows, and owner-decision gates
passed. Production authorization remains false until installed release
acceptance passes.

## Explicit exclusions

The 4.4.3 contract excludes public-internet gateway exposure, public
self-registration, multi-tenancy, vendor-hosted customer data or API spend,
Kubernetes, managed cloud databases as production authorities, mobile clients,
and macOS or Linux packaging. CORS/browser gateway use and network MCP
connectors are also excluded unless a later approved requirement reopens them.

## Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| DLE-FR-001 | Every approved client request shall enter through the versioned gateway/security envelope and the backend-owned governed request path. | Route inventory, contract tests, built-in-chat parity, installed native/SSE/async traces |
| DLE-FR-002 | The governed path shall record one causal run identity across admission, policy, routing, personas, model/tool execution, evidence, convergence, memory, audit, and response. | Trace schema/tests and installed correlation walkthrough |
| DLE-FR-003 | The product shall distinguish completed, blocked, failed, cancelled, capability-unavailable, and not-measured outcomes without fabricating stages, confidence, provider state, or durable effects. | API/UI contract tests, failure injection, trace review |
| DLE-FR-004 | The owner shall be able to configure and bounded-test OpenAI or Google credentials without exposing plaintext credentials to the renderer or clients. | Credential tests, provider manifest, installed provider matrix |
| DLE-FR-005 | The desktop shall provide real backend-backed chat, session history, trace, graph/knowledge, simulation, Truth Engine, MCP, settings, privacy, diagnostics, and administration workflows. | UI inventory, handler-to-durable-effect matrix, installed walkthrough |
| DLE-FR-006 | Knowledge ingestion shall preserve source identity and provenance across PostgreSQL, object storage, graph, vector, retrieval, update, repair, and deletion operations. | Ingestion/reconciliation tests and populated installed drill |
| DLE-FR-007 | Memory promotion, export, deletion, compaction, and recovery shall be owner-controlled, integrity-checked, and trust-aware. | Memory contract tests and retained-data recovery evidence |
| DLE-FR-008 | Simulations shall enforce budgets and lifecycle states, retain checkpoints and artifacts, and expose truthful UI and API outcomes. | Simulation tests and installed provider/restart/artifact matrix |
| DLE-FR-009 | MCP registration shall not execute a connector; first use shall require exact command fingerprint, scope, file-root, and owner consent. | MCP policy tests and installed lifecycle/containment matrix |
| DLE-FR-010 | Same-host client keys shall be copy-once, least-privilege, revocable, bounded, and isolated across client jobs and traces. | Gateway key/job tests, SDK compatibility, installed acceptance |
| DLE-FR-011 | Every preserved Knowledge Algorithm capability shall have one canonical stable identity, exactly one implementation owner and primary owning subsystem, production behavior, typed governed contract, reachable manifest-selected application call path, individually named functional test, explicit limitation/failure/side-effect semantics, and causal trace record without reducing an approved capability. | Retained Phase 18 manifest/crosswalk plus Phase 19 per-KA tests, selector/owner/call-path matrix, ten-layer/persona/refinement and owning-subsystem integration, API/SDK/UI workflow, effect receipts, trace/replay evidence, and rebuilt-installed acceptance |

## Data and lifecycle requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| DLE-DR-001 | Production startup shall require healthy, identity-verified app-owned PostgreSQL, Redis, Neo4j, ChromaDB, and object storage and shall reject development fallbacks. | Runtime precheck, service qualification, installed failure matrix |
| DLE-DR-002 | Versioned migrations shall complete before readiness and shall reject newer, unsupported, or unversioned populated data. | Migration ledger tests and retained-data upgrade drill |
| DLE-DR-003 | Coordinated backups shall be encrypted, signed or integrity-verified, exclude secret material, and restore into an isolated root before activation. | Backup/restore tests and clean-machine recovery evidence |
| DLE-DR-004 | Deletion shall reconcile all required stores, report partial failure, and retain only documented audit tombstones or time-bounded backup remnants. | Seven-surface deletion tests and installed remnant scan |
| DLE-DR-005 | Production data and secrets shall remain under an approved protected Windows volume and restricted installation/runtime ACL boundary. | DPAPI/ACL tests and supported-Windows matrix |

## Security, privacy, and AI requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| DLE-SR-001 | The renderer and approved clients shall never receive provider credentials, internal-service credentials, installation secrets, or unrestricted filesystem authority. | Boundary tests, packaged content review, penetration review |
| DLE-SR-002 | Production shall fail closed for missing trust, readiness, migration, storage-protection, signature, update, scope, policy, or required evidence gates. | Adversarial tests and installed failure/recovery matrix |
| DLE-SR-003 | Logs, metrics, errors, support bundles, exports, and diagnostics shall redact secrets and disallowed content. External telemetry, license check-in, update-check egress, crash-reporting egress, and phone-home shall remain disabled and unapproved. | Canary suites, bundle preview/hash tests, no-egress evidence |
| DLE-PR-001 | Before provider processing, the UI shall disclose that selected prompt, retrieved context, persona/context material, and tool results may leave the device. | Privacy notice/UI review and provider preflight tests |
| DLE-PR-002 | The owner shall be able to review and control stored sessions, traces, provider usage metadata, ingested data, exports, connectors, and supported deletion actions. | UI/API tests and installed privacy walkthrough |
| DLE-AI-001 | AI output shall be presented as assistance, not autonomous professional authority, and high-risk use shall require human oversight. | AI system card, user copy review, blinded acceptance |
| DLE-AI-002 | Evidence support, confidence components, limitations, abstention, and provider/model identity shall be reported truthfully; missing inputs shall be `not measured`. | Evaluation schema/tests and provider/model evaluation rows |

## Quality and release requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| DLE-QR-001 | Supported user workflows shall meet keyboard, scaling, contrast, labeling, error-state, and screen-reader requirements. | Automated axe/keyboard gates plus manual packaged NVDA review |
| DLE-QR-002 | The release shall be built from exact locked Python, Node, Electron, workflow, and version authorities with SBOMs and provenance. | Lock/version/workflow gates, SBOMs, attestations |
| DLE-QR-003 | Two isolated builds from identical approved inputs shall meet the approved reproducibility rule or have documented normalized differences accepted by release authority. | Independent build comparison |
| DLE-QR-004 | The final installer and executables shall be signed by the approved publisher, timestamped, hash-bound, malware-scanned, and legally redistributable. | Signature inventory, malware scan, legal and notices records |
| DLE-QR-005 | Install, repair, upgrade, rollback, uninstall, reboot, sleep/resume, service failure, recovery, load, 24-hour stress, and 72-hour normal/idle behavior shall pass on the supported Windows matrix. | Phase 15 CP15-A through CP15-H installed evidence |
| DLE-QR-006 | No production or public-release claim shall be made while a P0/P1 finding, unaccepted P2, critical dependency alert, legal authority, signing gate, or mandatory independent review remains open. | Release readiness record and owner go/no-go decision |

## User experience acceptance

An unfamiliar supported user must be able to use only the canonical documents
to identify the product boundary, install the signed release, configure a
provider, perform a governed request, inspect its trace and evidence, manage
local data, export approved records, recover from common failures, back up and
restore, update or roll back, and uninstall with an informed data-retention
choice. An unfamiliar evaluator must be able to distinguish demonstrated
behavior from qualification-only, not-evaluated, unsupported, and
release-blocked behavior.

## Current acceptance status

Engineering checkpoints exist for Phases 0 through 17, but the signed installed
acceptance matrices and independent/manual gates remain open. Two clean candidate
builds still differ at the byte level, the current candidate is unsigned, and
its packaged backend correctly refused startup when protected-volume readiness
could not be proved. Installed and independent acceptance of the selected object
store, legal/distribution authority, accessibility/manual review, pilot, and
soak gates also remain open. Phase 18 closed incomplete after retaining 213
unique implementation owners and zero source gaps; CP18-D failed and CP18-E-H
did not pass. Phase 19 canonical KA system-of-systems integration is active;
CP19-A owner/consumer authority and CP19-B typed result-contract parity passed;
CP19-C selector/DAG integration also passed with 213 positive and 213 negative
fixtures and a base 119-edge zero-cycle dependency graph. CP19-D canonical
ten-layer product-path integration passed with typed causal L1-L10 trace state,
production-mode L1 selection, bounded L6-L9 revalidation, and L10-gated success
persistence. CP19-E full correct-ID fail-closed L9/L10 safety passed: all 14
algorithms execute through committed child traces, its then-current graph was 134
edges/zero cycles, PII is removed from release and trace state, and required
failure/timeout, trace forgery, containment, confidence, recursion, promotion,
and false receipts block. CP19-F causal Quad Persona/DSQP also passed:
`KA-012` -> `KA-013` -> `KA-030` consumes the four axes 8-11 profiles once,
preserves dissent and explicit sufficiency without fabricated confidence, and
causally changes the single provider prompt. The CP19-F corrected graph was
132 edges/zero cycles. CP19-G canonical 12-step refinement also passed: all
steps are trace-accounted, zero step-level provider subcalls occur, at most one
rewrite is allowed, L6-L10 revalidation is mandatory, and lifecycle output is
proposal-only. The CP19-G graph was 131 edges/zero cycles with 29
production-enabled capabilities. CP19-H Truth/data/knowledge integration and
CP19-I simulation/MCP/provider/security/operations/effect integration now also
pass. The CP19-I manifest production-enabled 149 capabilities and kept 136
dependency edges acyclic, enforces bounded effect proposals, and retains
authoritative owning-service receipts. CP19-J now also passes the
principal-owned encrypted/idempotent durable API/SDK/desktop plan, exact
confirmation, execute/cancel/recovery, and result/trace/artifact/effect
workflow. CP19-K then qualified 213/213 KAs and the current manifest
`2026.08.11-al10.2` production-enables 211 capabilities with 112 acyclic
dependency edges. CP19-L passed; CP19-M exact installed acceptance remains
open.
Dependabot alert 389 is fixed.
Production/public release is **NO-GO**.

## Change control

Any change to product scope, provider/model support, data-plane responsibility,
network exposure, identity model, retention, AI limitation, installer behavior,
or release evidence shall receive impact analysis across code, tests, UI copy,
this specification, linked canonical documents, and the release record.
