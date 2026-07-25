# DataLogicEngine requirements traceability matrix

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ASR-001 |
| Title | Requirements traceability matrix |
| Document version | v1.1.0 |
| Product version | 4.3.0 |
| Status | release_blocked |
| Audience | Product owner, engineering, quality, assurance, release authority, and professional reviewers |
| Owner | Quality Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Product requirements, implemented architecture/contracts, tests, phase evidence, and release gates |
| Confidentiality | Public |
| Last reviewed | 2026-07-25 |
| Next-review trigger | Requirement, implementation, test, evidence, finding, risk acceptance, or release-decision change |
| Requirements and evidence | `docs/PRODUCT_REQUIREMENTS.md`, source/tests, canonical documents, and `reports/production-readiness/2026/` |

## Traceability rules

Every approved requirement has one stable ID, owner, implementation/control
location, verification method, evidence state, and release disposition. A source
test or engineering checkpoint is not a signed-installed pass. `Partial` means
implemented/verified evidence exists but one or more named acceptance gates are
retained. `Open` means required evidence or authority is absent. Only the release
record can promote the exact artifact to `Pass` for production.

## Functional requirements

| ID | Primary implementation/control | Verification/evidence | Status and retained gate |
|---|---|---|---|
| DLE-FR-001 | Versioned gateway, API envelope, backend governed path, built-in chat | Route/single-path/contract tests; Phase 5/8 evidence | Partial: installed built-in/native/SSE/async parity retained |
| DLE-FR-002 | Causal orchestrator, run/trace schemas, provider/tool/memory/audit bindings | Causality/schema/correlation tests; Phase 5/13 evidence | Partial: installed multi-process/store trace retained |
| DLE-FR-003 | Typed outcomes, error taxonomy, measured confidence/stage UI contracts | API/UI/error/evidence tests; Phase 6/12/13 evidence | Partial: packaged failure and visual walkthrough retained |
| DLE-FR-004 | Provider manifest, encrypted provider records, backend adapters/test route | Credential/provider/budget/privacy tests; Phase 7 evidence | Partial: installed OpenAI/Google matrix retained |
| DLE-FR-005 | Electron routes and backend handlers for product surfaces | Control inventory, axe/keyboard/workflow tests; Phase 12/13 evidence | Partial: installed durable-effect/NVDA/visual acceptance retained |
| DLE-FR-006 | Ingestion jobs/reconciliation, source objects, Neo4j/Chroma revisions, provenance | Hostile parser/retrieval/reconcile/delete tests; Phase 9 evidence | Partial: populated installed restart/recovery/remnant drill retained |
| DLE-FR-007 | Unified memory trust/promotion/integrity/export/delete/compaction | Memory contract/recovery tests; Phase 9 evidence | Partial: installed retained-data recovery retained |
| DLE-FR-008 | Authoritative simulation lifecycle/budget/checkpoint/artifact/result | Simulation contract/failure tests; Phase 10 evidence | Partial: installed provider/restart/UI/artifact acceptance retained |
| DLE-FR-009 | MCP registry/fingerprint/scope/consent, process loop, Job Object, result governance | MCP policy/lifecycle/hostile fixture tests; Phase 11 evidence | Partial: installed OS containment/Electron lifecycle retained |
| DLE-FR-010 | Client-key verifier, scopes/limits/jobs/idempotency/trace ownership/SDKs | Gateway auth/isolation/SDK/compatibility tests; Phase 8 evidence | Partial: signed installed same-host/private acceptance retained |
| DLE-FR-011 | Phase 18 canonical KA manifest/crosswalk, typed controller/selector, authoritative service ports, API/SDK/desktop workflow, and causal execution records | One named functional test per KA, manifest/call-path/selector gates, effect receipts, integration/security/performance/trace/replay suites, and Phase 18 evidence | Partial: CP18-A/CP18-B 213-capability no-duplicate authority and single runtime passed; CP18-C active, CP18-D through CP18-H retained, and rebuild paused |

## Data and lifecycle requirements

| ID | Primary implementation/control | Verification/evidence | Status and retained gate |
|---|---|---|---|
| DLE-DR-001 | Runtime factory/supervisor and five app-owned service adapters | Five-service qualification, precheck/capability tests; Phase 3 | Partial: exact installed service delivery/identity/failure matrix retained |
| DLE-DR-002 | Versioned migration coordinator and per-store ledger | Migration/schema parity and populated lifecycle tests; Phase 4 | Partial: 0.1.1 retained-data signed upgrade retained |
| DLE-DR-003 | Encrypted coordinated backup, manifest, isolated restore/activation | Populated backup/restore drill; Phase 4 | Partial: signed clean-machine restore and independent review retained |
| DLE-DR-004 | Cross-store deletion/reconciliation and tombstone/remnant contracts | Seven-surface delete/partial-failure tests; Phase 4/9 | Partial: installed remnant and backup-expiry evidence retained |
| DLE-DR-005 | Protected-volume/runtime-root ACL and DPAPI/key boundaries | Source/negative protection tests; Phase 4/14/15 | Partial: supported-Windows protected-volume/ACL matrix retained |

## Security, privacy, and AI requirements

| ID | Primary implementation/control | Verification/evidence | Status and retained gate |
|---|---|---|---|
| DLE-SR-001 | Preload/API allowlists, opaque picker tokens, backend-owned credentials/services | Boundary/secret/API/packaging tests; Phase 1/7/9/11 | Partial: packaged penetration and leakage review retained |
| DLE-SR-002 | Fail-closed readiness, policy, migration, storage, release, scope, update gates | Negative/adversarial tests across Phases 1-15 | Partial: full installed failure/recovery matrix retained |
| DLE-SR-003 | Redacted logs/errors/metrics/diagnostics/support/export and telemetry opt-in | Canary/support/no-egress source tests; Phase 13 | Partial: installed all-output canary/no-egress retained |
| DLE-PR-001 | Provider preflight categories, cloud disclosure, backend egress ledger | Provider privacy/UI/schema tests; Phase 7/12 | Partial: packaged provider disclosure walkthrough retained |
| DLE-PR-002 | Session/trace/knowledge/memory/connector/client/export/delete owner controls | API/UI/lifecycle tests; Phase 9/11/12/13 | Partial: installed cross-store durable-effect/remnant proof retained |
| DLE-AI-001 | AI limitation copy, system card, high-risk oversight and release policy | Documentation/UI review and human rubric | Partial: blinded signed-RC human acceptance retained |
| DLE-AI-002 | Evidence/confidence schema, claim/citation validation, abstention/not-measured | Golden corpus/KA/evidence tests; Phase 6 | Partial: installed OpenAI/Google corpus/model rows retained |

## Quality and release requirements

| ID | Primary implementation/control | Verification/evidence | Status and retained gate |
|---|---|---|---|
| DLE-QR-001 | Accessible component/route patterns, axe and keyboard gates | 28-route automated evidence; Phase 12 | Partial: packaged scaling/contrast/visual and manual NVDA retained |
| DLE-QR-002 | Product-version authority, exact Python/Node/Electron/workflow locks, SBOM/provenance | Release trust/verifier gates; Phase 14/15 | Partial: final signed artifact evidence retained |
| DLE-QR-003 | Isolated candidate build and normalized comparison workflow | Two GitHub candidate builds; Phase 15 | Open: hashes differ and nondeterminism is unresolved |
| DLE-QR-004 | Publisher/signature, malware/license/legal/redistribution controls | Signature/trust/SBOM/legal registers; Phase 14 | Open: approved publisher, signatures, final scans/legal authority retained |
| DLE-QR-005 | Lifecycle/Windows/service/provider/failure/load/soak acceptance plans | Phase 15 CP15-A through CP15-H protocols | Open: signed installed matrices, pilot, 24/72-hour soaks retained |
| DLE-QR-006 | Finding severity policy and go/no-go record | TODO, security alerts, release checklist/evidence | Open: alert 389 and other named authorities/gates keep NO-GO |

## Architecture and document coverage

| Concern | Canonical authority |
|---|---|
| Product/user contract | `docs/PRODUCT_REQUIREMENTS.md`, `docs/USER_GUIDE.md` |
| Installation/operations/support | `docs/INSTALLATION_GUIDE.md`, `docs/ADMINISTRATOR_OPERATIONS_GUIDE.md`, `docs/TROUBLESHOOTING_SUPPORT_GUIDE.md` |
| Architecture/data/interfaces/security | `docs/ARCHITECTURE.md`, `docs/DATA_ARCHITECTURE.md`, `docs/INTERFACE_INTEGRATION.md`, `docs/SECURITY_ARCHITECTURE.md` |
| Privacy and AI limitations | `docs/PRIVACY_AI_NOTICE.md`, `docs/evaluation/AI_SYSTEM_CARD.md` |
| Lifecycle/recovery/V&V | `docs/SOFTWARE_LIFECYCLE_PLAN.md`, `docs/MAINTENANCE_DISASTER_RECOVERY.md`, `docs/VERIFICATION_VALIDATION_REPORT.md` |
| Release and external review | Planned canonical release-readiness, third-party, accessibility, professional, Microsoft, and independent-review records |

## Findings and change control

Each finding links affected requirement IDs, severity, source commit/artifact,
reproduction, correction/removal/risk acceptance, regression evidence, owner,
expiration, and release disposition. Each requirement change triggers impact
analysis across implementation, interfaces, data, security/privacy, UI copy,
tests, canonical documents, migration/compatibility, and release evidence.

## Overall status

All 29 product requirement IDs have an implementation/control or planned
Phase 18 control and a named verification path. None may be interpreted as final
production pass while their retained gates are open. The exact 4.3.0 release
remains **NO-GO**.
