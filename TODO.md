# DataLogicEngine Production TODO

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ROOT-005 |
| Title | Open production work and release blockers |
| Document version | v1.0.0 |
| Product version | 4.3.0 |
| Status | release_blocked |
| Audience | Product owner, engineering, assurance, and release reviewers |
| Owner | Production Program Owner |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | `PRODUCTION_COMPLETION_PLAN_2026.md` and validated phase evidence |
| Confidentiality | Public |
| Last reviewed | 2026-07-15 |
| Next-review trigger | Phase checkpoint, blocker disposition, or release-decision change |
| Requirements and evidence | Active plan and `reports/production-readiness/2026/` |
| Active plan | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.20.0 |
| Completed phase | Phase 15 release-candidate engineering checkpoint; installed exit gates retained |
| Current phase | Phase 16 - production documentation replacement and professional review dossier |
| Release decision | Production/public release: **NO-GO** |
| Historical backlog | `docs/archive/session-history/TODO_through_2026-07-12.md` |

This file contains current open work only. Detailed requirements, stop
conditions, and exit gates remain authoritative in the active root plan.

## Completed checkpoints

- The 2026-07-15 CI/security maintenance checkpoint repaired the dependency,
  backend, governance, code-security, and Cosign artifact-signing failures.
  A clean short-path Windows environment installed all 315 hash-locked packages
  with no broken requirements; `pip-audit` reports zero unignored findings;
  Ruff, Bandit, workflow-pin, lock, frontend lint/typecheck, and 2,177 backend
  tests pass. The documented ChromaDB no-fix ignore preserves CI visibility but
  does not close alert 389 or change production/public release from **NO-GO**.
- Phase 16 CP16-A is owner-approved and complete. The information architecture
  inventories all 134 root and `docs/**` Markdown files with zero unclassified
  files and zero duplicate merge routes.
- The approved canonical set is exactly 30 hand-maintained documents across five
  classes: 10 existing and 20 planned. Generated BOM/crosswalk controls do not
  count against the cap.
- The approved disposition totals are 14 authoritative inputs, five generated
  replacements, 43 historical/archive records, and 72 merge routes. No move,
  archive, or deletion is authorized until target and link review passes.
- All ten existing canonical documents now carry the required controlled header;
  the authority verifier passes IDs, owners, approver, product version, status,
  and all 13 fields. The two verifiers and five focused unit tests pass.
- The CP16-B content checkpoint adds and verifies the five canonical product/
  user targets: product requirements, installation/lifecycle, administrator/
  operations, troubleshooting/support, and privacy/AI notice. The canonical
  inventory is now 15 existing and 15 planned targets across 139 Markdown files.
- Canonical entry links now prefer the replacement set. The product/user verifier
  passes all five source maps, required topics, truthful statuses, and prohibited-
  claim checks. Six focused authority/document tests pass. No source was moved,
  archived, or deleted.
- The first CP16-C content batch adds seven canonical engineering/assurance
  targets: data architecture, interface/integration, security architecture,
  software lifecycle, maintenance/disaster recovery, requirements traceability,
  and V&V. The inventory is now 22 existing and eight planned targets across
  146 classified Markdown files.
- The engineering/assurance verifier passes all seven approved source maps,
  required topics, portal links, truthful statuses, and prohibited-claim checks.
  All 22 controlled headers and seven focused tests pass. No source was moved,
  archived, or deleted.
- The second CP16-C content batch adds the KA/TruthCore validation dossier,
  privacy impact assessment, accessibility conformance report, third-party
  software index, and release-readiness record. The canonical set is now 27
  existing and three planned targets across 151 classified Markdown files.
- The expanded engineering/assurance verifier passes 12/12 targets and all 27
  controlled headers pass. CP16-C content construction is complete; installed,
  manual, legal, independent, provider/model, pilot, and soak evidence remains
  retained. No source was moved, archived, or deleted.
- CP16-D/CP16-E content construction adds the professional review index,
  Microsoft submission dossier, and independent review record. All 30 canonical
  documents now exist with valid controlled headers; all 154 Markdown files are
  classified with zero unclassified/duplicate routes.
- The MSI/EXE Store route is selected for qualification from the reviewed
  official Microsoft policy snapshot, not for submission approval. The external-
  review verifier passes 3/3 records while policy/WACK, Partner Center, signing,
  reviewer assignment/findings, legal, and acceptance remain open. No source was
  moved, archived, or deleted.
- Phase 15 reached its release-candidate engineering checkpoint on 2026-07-14.
  Evidence is under `reports/production-readiness/2026/phase-15/`; CP15-A
  through CP15-H remain installed/signed/manual release gates.
- Commit `f2e4174f` freezes candidate inputs and separates unsigned candidate
  qualification from production signing and distribution authority.
- The canonical candidate installer is 299,129,416 bytes with SHA-256
  `5a76e0004e17ccee3e0721ec3f9fe0ee109ccc03d74c5ceb19273e99b3ae4620`;
  installer integrity, exact lock, version, workflow pins, and payload gates pass.
- The frozen backend contains 6,151 files and 513,329,279 bytes with zero
  forbidden source/test/cache, stale Electron test, or required-asset findings.
- The invalid drifted first build remains negative evidence. It contained 10,331
  backend files and a 1,330,613,366-byte portable tree, including developer
  source/tests/caches, and is not a release candidate.
- The packaged runtime reached the frozen backend and correctly failed closed at
  `at_rest_protection_not_ready` because this machine could not prove protected-
  volume readiness. The unsigned signature inventory also correctly fails.
- Two independent GitHub candidate builds succeeded with equal file counts, but
  backend, portable, and installer hashes differ. CP14-B reproducibility remains
  open; exact differing-file evidence is in the Phase 15 comparison report.
- Phase 14 reached its engineering checkpoint on 2026-07-14. Evidence is under
  `reports/production-readiness/2026/phase-14/`; the final installed/signed exit
  rows are retained for Phase 15 rather than misreported complete.
- Product `4.3.0` now has one authority across Python, Electron, UI, support,
  Windows metadata, artifacts, release workflows, and the release manifest.
- Python has 81 exact direct pins and a generated 315-package SHA-256 release
  lock; Node is exact and Electron is locked to 43.1.1.
- All 71 external workflow references are immutable. SBOM/content inventory,
  release-manifest, signing, update-trust, attestation verification, legal, and
  legacy gates fail closed.
- Focused Phase 14 validation passes 27 Python tests, Ruff, 18 version checks,
  lock/workflow/legacy/NSIS governance, frontend update tests/typecheck/Electron
  build, and npm audit. The unsigned stale local artifact correctly fails.
- Phase 0 CP0-A through CP0-G passed on 2026-07-13 and were committed as
  `52363a0e`.
- Phase 1 CP1-A through CP1-F passed on 2026-07-13. Evidence is under
  `reports/production-readiness/2026/phase-01/`; the phase commit is the commit
  containing this ledger update.
- The Phase 1 live inventory covers 424 Flask routes, 12 GraphQL operations, 19
  Electron IPC channels, 6 MCP methods, 5 file capabilities, and 5 network
  surfaces with zero unclassified entries.
- The Phase 1 mandatory security, public-error, packaged Electron, secret,
  backend, frontend, documentation, ACL, and CodeQL-status checks pass.
- Phase 2 CP2-A through CP2-E passed on 2026-07-13. Evidence is under
  `reports/production-readiness/2026/phase-02/`; the phase commit is the commit
  containing this ledger update.
- Phase 2 provides an import-safe application factory, per-app runtime and
  service supervisor, deterministic startup phases, installation/runtime lock,
  truthful readiness/capabilities, mutation drain, Windows lifecycle handling,
  and bounded Electron shutdown.
- Final Phase 2 validation reports 590 backend unit/route checks, 398 security/
  route checks, and 403 frontend checks passed. The 426-route manifest and all
  startup, public-error, secret, packaged Electron, and precheck gates pass.
- Phase 3 reached its engineering checkpoint on 2026-07-13. Evidence is under
  `reports/production-readiness/2026/phase-03/`; installed-production gates are
  retained rather than misreported as passed.
- One protected, per-install, digest-pinned Podman profile supervises
  PostgreSQL, Redis, Neo4j, ChromaDB, and a qualification-only S3 candidate with
  loopback ports, verified identity, resource/security limits, and cleanup.
- Live qualification passed real operations and restart durability for all five
  services, six required object buckets, truthful status, and resource cleanup.
- Full validation passed 1,814 backend tests (18 skipped), 402 frontend tests,
  frontend lint/typecheck/build, and Ruff.
- SeaweedFS is not production-selected: ADR-0004 remains Proposed, production
  authorization is false, and the architecture remains MinIO-specific.
- Phase 4 reached its engineering checkpoint on 2026-07-13. Evidence is under
  `reports/production-readiness/2026/phase-04/`; installed-release gates are
  retained rather than misreported as passed.
- The ownership registry covers 70 PostgreSQL entities and 28 logical data
  classes with one authority each. PostgreSQL-authoritative graph/vector
  materializations and required MinIO artifact writes use a durable, retryable
  outbox without changing object authority.
- Production startup now applies a fail-closed 14-revision migration chain and
  per-store version ledger before readiness. Newer, unsupported, and unversioned
  populated data are refused.
- A populated five-service drill passed encrypted six-component backup,
  isolated clean-root restore, restart, PostgreSQL/Redis/Neo4j/Chroma/MinIO/JSON
  value and hash parity, prior-root preservation, and cross-store deletion.
- The desktop backup requires a user recovery passphrase that is not stored.
  Offline restore creates a new installation identity and recovery credentials.
- The approved at-rest design requires protected Windows volumes, restrictive
  ACLs, DPAPI-wrapped secrets, and AES-256-GCM portable backups. The current
  machine did not prove BitLocker or installed-root ACL readiness, so production
  authorization remains false.
- Dependabot alert 389 is a critical ChromaDB advisory with no patched upstream
  release. The locked service is the non-affected Rust binary, and the Python
  client now refuses persisted embedding functions/schema before use. The alert
  remains open and release-blocking; ChromaDB production approval remains false.
- Phase 5 CP5-A through CP5-D passed on 2026-07-13. Evidence is under
  `reports/production-readiness/2026/phase-05/`; CP5-E remains a deferred
  installed-release blocker.
- The versioned `governed.v1` contract and one backend orchestrator now own
  admission, DMRF, retrieval, deterministic DSQP, TruthCore/KA preflight,
  provider execution, validation, persistence, and trace state.
- Built-in chat, gateway/replay/stream, compatible facades, the public TruthCore
  adapter, persona/video callers, and SDK service clients use the canonical
  boundary or an explicit unavailable boundary. Simulation stops at its Phase
  10 boundary and does not fabricate execution.
- Exact trace-stage and causality tests pass for success, policy block, provider
  failure, cancellation, and internal failure. Unmeasured confidence remains
  null pending Phase 6.
- Final Phase 5 validation reports 1,895 backend tests (18 skipped), 402
  frontend tests, and 25 SDK tests passed, plus production frontend/Electron,
  route, migration, source-quality, schema, lockfile, secret, and error gates.
- Phase 6 CP6-A through CP6-E passed on 2026-07-13. Evidence is under
  `reports/production-readiness/2026/phase-06/`; CP6-F installed provider/human
  acceptance remains deferred and release-blocking.
- The canonical path now uses typed source provenance, trace-bound evidence,
  stable claim/citation offsets, persisted relationship/validator records,
  `dle-confidence.v1`, explicit Not measured state, and one-cycle bounded
  finalize/refine/abstain/block convergence.
- TruthCore publishes `truthcore-preflight.v1`; stale product-specific routing
  and hash-vector convergence were removed from the production contract.
- All 125 KAs have production classifications and category contracts. Only
  deterministic, semantically tested KAs are production enabled; experimental
  and placeholder execution requires explicit owner opt-in and cannot appear as
  a governed production validator.
- Golden corpus `2026.07.13.1`, automated thresholds, provider/model drift gate,
  human rubric, and AI system card are versioned. Deterministic local checks
  pass; OpenAI, Google, blinded review, and owner approval remain pending.
- Phase 7 CP7-A through CP7-E and CP7-G passed on 2026-07-13. Evidence is under
  `reports/production-readiness/2026/phase-07/`; CP7-F installed live-provider
  acceptance remains deferred and release-blocking.
- One generated OpenAI/Google provider manifest now controls Python, TypeScript,
  tests, product copy, and model support. Provider execution is backend-owned,
  async, deadline-bound, cancelable, circuit-broken, and has no silent
  cross-provider failover.
- Every provider attempt consumes the server call budget and writes a
  content-free egress/usage record. Session/day/month call and token ceilings,
  optional known-price spend ceilings, unknown-price truth, warning confirmation,
  and owner review/export/reset controls are implemented.
- Offline replay accepts only network/provider-outage/timeout failures, encrypts
  bounded expiring payloads, preserves idempotency, and re-runs policy. Current
  governed SSE is accurately labeled buffered pending Phase 8 native delivery.
- Final Phase 7 validation reports 1,945 backend tests (18 skipped), 402 frontend
  tests, and 25 SDK tests passed, plus frontend typecheck/lint/build, Ruff,
  compilation, generated-manifest, and 17-revision migration-head checks.
- Phase 8 CP8-A, CP8-D, CP8-E, and CP8-H passed; CP8-B, CP8-C, CP8-F, CP8-G,
  and CP8-J passed at the source/engineering boundary with their installed,
  recovery, failure/load, or visual proof retained. CP8-I remains deferred and
  release-blocking. Evidence is under
  `reports/production-readiness/2026/phase-08/`.
- The versioned `dle-gateway.v1` contract now covers strict native sync, live
  governed SSE, durable async/status/result/cancel, idempotency, capabilities,
  owned trace retrieval, stable errors, and a bounded OpenAI-compatible facade.
- PostgreSQL owns client/key lifecycle, virtual models, idempotency, durable jobs,
  and result references. Redis owns atomic minute/day/concurrency admission and
  content-free job coordination. Encrypted large job results use the seventh
  required `gateway-results` object bucket.
- The desktop separates outbound Provider Connections from inbound Client
  Gateway administration. Python SDK 0.7.0, a TypeScript SDK, examples,
  compatibility controls, API documentation, runbooks, and ADR-0005 are current.
- Final Phase 8 validation reports 1,993 backend tests (18 skipped), 403 frontend
  tests, 30 Python SDK tests, and 5 TypeScript SDK tests passed, plus frontend
  typecheck/lint/build, Ruff, compilation, contract-diff, documentation, and the
  21-revision migration head `b7c8d9e0f1a2`.
- Phase 9 reached its engineering checkpoint on 2026-07-14. Evidence is under
  `reports/production-readiness/2026/phase-09/`; rebuilt-installed causal
  retrieval and Knowledge/Graph acceptance remain explicit release gates.
- Electron-selected files and folders are acquired into a bounded app-owned
  staging area before parsing. Path, reparse/link, device/UNC, special-file,
  content-signature, archive, decompression, page, file-count, byte, and parser
  time defenses fail closed and write versioned content-defense results.
- PostgreSQL now owns durable ingestion jobs, files, chunks, and attempts;
  Redis carries content-free queue, lease, state, cancellation, and progress
  events. The registry covers 77 PostgreSQL entities and 30 logical contracts,
  with migration head `c8d9e0f1a2b3`.
- Approved original and normalized artifacts use the eighth required bucket,
  `knowledge-sources`. Completion requires the expected PostgreSQL, Neo4j,
  Chroma, original-object, and normalized-object revisions; consistency scan,
  repair, update, retry, and reference-aware deletion are implemented.
- Retrieval validates authoritative source, permission, retention, hash,
  defense, embedding, and materialization state; considered/selected/rejected
  decisions and graph context are traceable. UnifiedMemory v2 separates working
  from validated trust and adds review, export, deletion, compaction, recovery,
  integrity hashes, and v1 migration under ADR-0006.
- Knowledge, Graph, ingestion settings, memory settings, and run-detail pages
  now expose real state and navigation without synthetic compliance or status
  labels. Final Phase 9 validation reports 2,033 backend tests passed (18
  skipped) and 407 frontend tests passed, plus frontend typecheck/lint/build,
  Ruff, and Python compilation.
- Phase 10 reached its engineering checkpoint on 2026-07-14. Evidence is under
  `reports/production-readiness/2026/phase-10/`; rebuilt-installed simulation,
  live-provider, service, and artifact proof remain explicit release gates.
- ADR-0007 selects `backend/simulation/multi_agent_engine.py` as the sole
  user-triggered authority under `dle-simulation.v1`. Core/FROST and legacy
  engines are reference-only and no production entry point instantiates them.
- Quick, standard, and deep plans declare exact 4/5/7 provider-call ceilings.
  One simulation-only adapter enforces call, token, cost, timeout, cancellation,
  pause, and content-free attempt-ledger limits without recursively invoking
  `governed.v1`.
- PostgreSQL now owns sessions, steps, events, provider calls, evidence,
  checkpoints, artifacts, cancellation, and terminal state; Redis is
  content-free coordination; required transcript/result objects use the
  `simulation-artifacts` authority. Live measured summaries/relationships are
  eligible for Chroma/Neo4j materialization.
- The desktop Simulation Monitor exposes preflight provider/call/token/tool/cost
  admission, real progress, run/pause/resume/retry/cancel, artifacts, results,
  and explicit Not measured confidence. Fixed-seed output is qualification-only.
- Final Phase 10 validation reports 2,050 backend tests passed (18 skipped) and
  410 frontend tests passed, plus frontend typecheck/lint/build and Ruff.
- Phase 11 reached its engineering checkpoint on 2026-07-14. Evidence is under
  `reports/production-readiness/2026/phase-11/`; rebuilt-installed file/network,
  lifecycle, store, hostile-fixture, and Electron gates remain explicit.
- ADR-0008 selects MCP `2025-11-25` local stdio. Exact command/scope consent,
  DPAPI secrets, durable PostgreSQL/Redis/object state, named cancellation,
  Windows process-tree containment, governed untrusted results, hostile fixture
  tests, and truthful owner controls are implemented.
- Final Phase 11 validation reports 2,094 backend tests passed (18 skipped) and
  411 frontend tests passed, plus frontend typecheck/lint/build, Ruff, migration,
  schema, and documentation gates.
- Phase 12 reached its engineering checkpoint on 2026-07-14. Evidence is under
  `reports/production-readiness/2026/phase-12/`; installed workflow/store,
  packaged visual/scaling/high-contrast, and NVDA acceptance remain open.
- Phase 13 reached its engineering checkpoint on 2026-07-14. Evidence is under
  `reports/production-readiness/2026/phase-13/`; installed correlation,
  failure-injection, redaction/no-egress, diagnostics/support, and 24/72-hour
  soak acceptance remain open.
- Backend/Electron logs share `dle.log.v1`; request/background correlation,
  explicit external-telemetry opt-in, authenticated Diagnostics, and previewed,
  confirmed, re-redacted, hashed, retained, optionally encrypted support bundles
  are implemented.
- Typed failures and critical-boundary semantics are enforced. The regression
  inventory records 1,104 broad/bare catches in 321 files and zero module
  `logging.basicConfig` calls. The real import analyzer records four open cycles
  rather than emitting the former fabricated pass.
- Compliance/status/report paths are evidence-backed self-assessment/control
  maps; empty evidence is Not measured and no certification/coverage is invented.
- Final Phase 13 validation reports 2,135 backend tests passed (18 skipped), 419
  frontend tests passed, 28 axe-clean routes, and 10/10 browser
  readiness workflows; typecheck, Electron build, Next build, Ruff, and Python
  compilation pass.

## Phase 5 objective - engineering checkpoint complete

Deliver one causal, testable governed request path from built-in chat and
approved clients through policy, retrieval, routing/personas, provider/tool
execution, validation, persistence, trace, and result.

## Phase 5 work packages

- [x] Inventory every built-in chat, gateway, replay, SDK, compatible facade,
      and simulation entry into governed reasoning.
- [x] Define one versioned governed request/context/result/failure contract.
- [x] Select one backend-owned orchestrator and remove or thin duplicate paths.
- [x] Make policy, retrieval, DMRF, DSQP, KAs, provider/tool calls, validation,
      bounded refinement, persistence, and trace causally connected.
- [x] Eliminate synthetic stages, fixed durations, default confidence, and
      planned-but-unexecuted telemetry.
- [x] Prove blocked, failed, cancelled, and successful runs record only stages
      that actually executed and return one stable trace ID.
- [x] Keep installed Gemini/OpenAI proof as a later installed release gate when
      provider credentials and the rebuilt application are available.

## Phase 6 objective - engineering checkpoint complete

Replace plausible defaults, templates, and synthetic governance metrics with
typed provenance, category-valid evidence and validators, calibrated confidence,
explicit insufficiency, and executable TruthCore/KA records.

## Phase 6 work packages

- [x] Inventory all source, evidence, claim, citation, validator, confidence,
      convergence, TruthCore, and KA shapes and default values.
- [x] Define stable source identity, provenance, permissions, transformation,
      claim-offset, citation, and validator contracts.
- [x] Define category-specific evidence sufficiency and contradiction rules.
- [x] Replace default confidence/convergence with a versioned measured formula,
      local calibration baseline, and explicit unavailable state. Installed
      provider calibration remains in CP6-F.
- [x] Persist validator and KA inputs, outputs, status, duration, version, and
      causal relationship to the final decision.
- [x] Prove unsupported/high-stakes claims fail safely and trace only measured
      evidence and executed validation.

## Phase 7 objective

Make supported OpenAI and Google calls bounded, cancelable, observable,
privacy-aware, and truthfully represented across synchronous, streaming, and
offline behavior.

## Phase 7 work packages

- [x] Inventory provider/model factories, SDK call types, request-wide timeout
      gaps, retries/failover, cancellation, streaming, usage/cost, egress,
      offline queue/replay, and UI states.
- [x] Generate one supported OpenAI/Google provider/model capability manifest
      for Python, TypeScript, tests, and docs.
- [x] Remove unknown-provider fallback and unsupported production factories and
      probes; retain only explicit archived/disabled compatibility evidence.
- [x] Enforce one request-wide deadline and cancellation path through retrieval,
      provider execution, validation, persistence, and refinement.
- [x] Implement truthful streaming, retry/failover, quota/cost, privacy/egress,
      and offline/replay contracts with failure-first tests.
- [x] Preserve separate installed corpus approval for every supported
      provider/model combination; provider-disabled checks cannot approve live
      paths.

## Phase 8 objective - engineering checkpoint complete

Make DataLogicEngine usable by approved applications, agents, and chatbots as
versioned governed LLM middleware without creating a second execution path or
exposing provider credentials.

## Phase 8 work packages

- [x] Define fail-closed loopback, same-host, and qualification-gated private
      profiles, explicit principals/scopes, server-owned virtual models, and
      ADR-0005.
- [x] Implement copy-once client keys, rotation/revocation/expiry/deletion,
      per-client policy, atomic Redis admission, and durable lifecycle audit.
- [x] Publish strict native sync, live SSE, durable async/cancel/result,
      idempotency, discovery, trace, stable-error, and bounded OpenAI contracts.
- [x] Keep every external answer on `governed.v1`, with validation completed
      before provider text is released and no governance-bypass fields.
- [x] Add PostgreSQL/Redis/object-store authority, encrypted large results,
      restart-safe job disposition, and fail-closed dependency behavior.
- [x] Separate Provider Connections and Client Gateway desktop controls and add
      supported Python/TypeScript SDKs, examples, compatibility checks, and
      operational documentation.
- [x] Preserve installed same-host/private, provider, backup/restore, UI visual,
      load/soak, TLS/firewall, and two-machine proof as explicit release gates.

## Phase 9 objective - engineering checkpoint complete

Make local knowledge ingestion durable, secure, reconcilable, and causally
useful to governed responses.

## Phase 9 work packages

- [x] Acquire picker-authorized local files/folders into bounded app-owned
      staging and enforce content, path, archive, decompression, and parser
      defenses before authority is granted.
- [x] Persist jobs, files, chunks, attempts, checkpoints, and source revisions
      in PostgreSQL; use Redis only for content-free coordination and events.
- [x] Persist approved original/normalized artifacts in `knowledge-sources` and
      reconcile PostgreSQL, Neo4j, Chroma, and both required object revisions.
- [x] Implement deterministic causal retrieval with authority, permission,
      retention, defense, embedding, revision, diversity, and budget checks.
- [x] Define the memory authority/trust boundary in ADR-0006 and add review,
      export, deletion, compaction, integrity recovery, and source deletion.
- [x] Replace synthetic Knowledge/Graph state with live progress, consistency,
      provenance, graph controls, repair actions, and answer/source navigation.
- [x] Preserve rebuilt-installed CP9-D and Knowledge/Graph visual acceptance as
      release gates; source tests are not represented as installed evidence.

## Phase 10 objective - engineering checkpoint complete

Select one simulation authority and deliver bounded provider use, durable
progress, evidence-aware results, and safe lifecycle controls.

## Phase 10 work packages

- [x] Compare multi-agent debate and FROST/core implementations and select the
      backend multi-agent workflow in ADR-0007.
- [x] Define `dle-simulation.v1` scenarios, participants, plans, budgets,
      artifacts, results, events, calls, evidence, and checkpoints.
- [x] Enforce exact call/token/tool/time/cost budgets through a non-recursive
      simulation-only provider adapter and fail closed on unknown live pricing.
- [x] Persist authoritative lifecycle state in PostgreSQL, use Redis only for
      content-free coordination, and reconcile required S3 artifacts.
- [x] Implement fixed-seed and bounded live modes, real progress, pause/resume/
      cancel/retry/restart behavior, and safe ambiguous-call recovery.
- [x] Derive confidence only from explicit cited evidence and validators;
      qualification fixtures remain Not measured.
- [x] Replace the unavailable Simulation UI with supported preflight, lifecycle,
      result, artifact, and truthful confidence controls.
- [x] Preserve installed simulation, live-provider, service/materialization, and
      visual acceptance as release gates for the rebuilt application.

## Phase 11 objective - engineering checkpoint complete

Turn MCP into a real, scoped connector/tool subsystem with no caller-controlled
authority or placeholder production behavior.

## Phase 11 work packages

- [x] Select MCP `2025-11-25` local stdio in ADR-0008; keep REST/JSON-RPC as the
      authenticated app control plane and remove unsupported transport claims.
- [x] Derive identity/scope from the server, reject caller authority, and require
      exact fingerprint plus granular owner consent before start or expansion.
- [x] Validate absolute executable/arguments/cwd/file roots/environment/scopes/
      limits, reject shells/package runners and network targets, and DPAPI-wrap
      credentials without returning values to the renderer.
- [x] Add a durable stdio loop, Windows Job Object, bounded output/stderr/memory/
      deadlines, explicit execution cancellation, process-tree stop, and app-exit
      cleanup.
- [x] Remove fake default UKG/pillar/KA/graph/simulation/sampling behavior;
      unsupported features are absent rather than formatted as successful.
- [x] Persist connector/consent/lifecycle/discovery/execution authority in
      PostgreSQL, content-free live state in Redis, and large governed results in
      `mcp-results`.
- [x] Mark every connector result untrusted, hash/redact/bound it, detect prompt
      injection, omit content from history, and prevent a direct answer bypass.
- [x] Replace name-only/obsolete WebSocket UI with exact command, scope,
      credential, qualification, consent, and lifecycle controls.
- [x] Add real hostile stdio fixtures for malformed/oversized/delayed output,
      cancellation, child-process cleanup, command/path/network/scope abuse,
      secret leakage, ID binding, and prompt-injection output.
- [x] Preserve installed OS file/network, process/reboot, data-plane, hostile-
      fixture, backup/restore, and Electron workflow proof as release gates.

## Phase 3 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP3-A | Exact artifacts plus redistribution/security/support approval | Engineering candidates locked; independent reviews and final object selection open |
| CP3-B | Clean install provisions protected loopback-only services | Lab provisioning passed; clean signed-installer proof deferred |
| CP3-C | Instrumented workflows prove real read/write use of every service | Engineering qualification passed; final installed workflow proof deferred |
| CP3-D | Supervisor survives lifecycle/failure/relaunch cases | Start/restart/identity/cleanup passed; full failure matrix continues in Phases 4/15 |
| CP3-E | Installed Storage UI truthfully reports/actions the data plane | UI/backend contract implemented; installed-app proof deferred |

## Phase 4 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP4-A | Every entity has one authority and documented materializations | Passed; 70 physical entities and 28 logical contracts, zero registry errors |
| CP4-B | Every supported prior release upgrades without loss | Fresh/current migrations passed; populated 0.1.1 retained-data upgrade deferred |
| CP4-C | Installed populated coordinated backup passes | Current populated five-service engineering backup passed; signed installed proof deferred |
| CP4-D | Clean-machine restore reproduces all state | Isolated clean-root engineering restore passed; signed clean-machine proof deferred |
| CP4-E | Delete parity leaves no unapproved remnants | Live seven-surface engineering deletion passed; installed matrix retained |
| CP4-F | All retained data meets at-rest/key contract | Policy and fail-closed checks implemented; BitLocker/ACL Windows matrix deferred |

## Phase 5 deferred release gate

| Checkpoint | Required result | Status |
|---|---|---|
| CP5-E | Installed built-in chat and external boundary complete real Gemini and OpenAI runs with resolvable traces | Source/engineering path passed; rebuilt installed proof deferred and release-blocking |

## Phase 6 deferred release gate

| Checkpoint | Required result | Status |
|---|---|---|
| CP6-F | Every supported provider/model plus deterministic workflow passes the versioned corpus and signed blinded human sample | Deterministic contract row passed; OpenAI/Google installed evaluations, second reviewer, blinded sample, and owner approval deferred and release-blocking |

## Phase 7 deferred release gate

| Checkpoint | Required result | Status |
|---|---|---|
| CP7-F | Rebuilt installed app completes owner-run Google and OpenAI contract, latency, cancellation, trace, and no-secret evidence | Engineering fixtures and failure matrix passed; installed live-provider acceptance deferred and release-blocking |

## Phase 8 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP8-B | Rebuilt installed same-host/private profiles prove TLS, firewall, certificate, listener, and policy behavior | Loopback and fail-closed source contract passed; installed private profile remains disabled and release-blocking |
| CP8-C | Client lifecycle survives coordinated backup/restore and installed compromise drills | Source lifecycle and audit tests passed; installed backup/restore proof deferred |
| CP8-F | Installed desktop controls and reference client prove visible and durable parity | UI/backend contract tests passed; packaged visual and reference-client acceptance deferred |
| CP8-G | Expanded gateway state passes installed seven-bucket backup/restore/restart/deletion qualification | Source authorities and object-result contract passed; rebuilt installed lifecycle drill deferred |
| CP8-I | Same-host and private two-machine clients complete real governed Google and OpenAI requests | Deferred to the rebuilt signed application and release-blocking |
| CP8-J | Installed concurrency, failure, latency, security/privacy, restart, and soak matrix passes | Engineering adversarial coverage passed; full installed load/soak matrix deferred |

## Phase 9 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP9-A | Ingestion survives backend/Electron restart without loss or duplication | PostgreSQL/Redis restart and idempotency tests passed; rebuilt installed lifecycle drill deferred |
| CP9-B | Corpus scanner reports no unexplained PostgreSQL/Neo4j/Chroma/S3 divergence | Scanner, repair, and required-revision tests passed; installed populated-store proof deferred |
| CP9-C | Malicious path/archive/content fixtures are contained and reported | Failure-first source tests passed; packaged hostile-corpus acceptance deferred |
| CP9-D | Source changes alter citations, validation, or answer behavior | Source-level causal retrieval tests passed; rebuilt installed E2E proof remains release-blocking |
| CP9-E | Source deletion reconciles every store and memory layer | Reference-aware cross-store and memory deletion tests passed; installed lifecycle drill deferred |

## Phase 10 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP10-B | Installed live-provider run proves declared provider/token/tool/cost ceilings | Source budget and failure-first tests passed; owner-configured installed provider proof deferred |
| CP10-C | Rebuilt app restart resumes from a verified checkpoint or terminates safely without duplicate calls | Restart/checkpoint tests passed; packaged lifecycle drill deferred |
| CP10-D | Installed UI progress and controls match durable transitions and artifact state | Frontend/API contract tests passed; packaged visual/event parity deferred |
| CP10-E | Installed result, evidence, validators, trace, S3 artifacts, and approved graph/vector links reconcile | Deterministic/source contracts passed; populated five-service installed proof deferred |

## Phase 11 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP11-C | Installed child process, OS file/network isolation, output, shutdown, crash, and reboot controls pass adversarial tests | Command/path/network/output/cancellation/Job Object source tests pass; installed OS isolation and lifecycle matrix retained |
| CP11-E | Installed owner workflow passes add, discover, call, cancel, stop, restart, remove, persistence, and visible state | API/UI source contracts pass; rebuilt packaged Electron acceptance retained |

## Phase 12 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP12-C | All primary workflows pass against rebuilt installed Electron and real internal services/stores | Source/API/component/browser contracts pass; installed durable-effect matrix retained |
| CP12-E | Accessibility automation plus packaged visual/scaling/high-contrast checks pass | All 27 routes axe-clean and keyboard/app-readiness 10/10; installed display/visual matrix retained |
| CP12-F | Manual NVDA checklist completes without a release blocker | Deferred to rebuilt release-candidate UI |

## Phase 13 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP13-A | One installed run reconstructed across every participating process/store | Source request/context/trace contract passes; installed reconstruction retained |
| CP13-B | Complete installed failure-injection matrix produces approved safe states/evidence | Typed taxonomy/matrix/regression gate passes; installed matrix retained |
| CP13-C | Canary secrets/PII/content absent from every installed local/exported output and no unexpected egress | Source canary suites pass; installed all-output proof retained |
| CP13-D | Every compliance/control status resolves to evidence without certification claims | Source resolver/report/API/UI contract passes; installed wording/export review retained |
| CP13-E | Installed 24-hour stress and 72-hour idle/normal soaks stay bounded with no silent degradation | Profile/evaluator and short observation pass; full-duration runs retained |

## Phase 14 retained release gates

| Checkpoint | Source checkpoint | Open closure evidence |
|---|---|---|
| CP14-A | Version parity passes | Rebuilt/installed 4.3.0 artifact and UI/support proof |
| CP14-B | Clean/tag/lock/content gates implemented | Two isolated same-input builds |
| CP14-C | Installer policy foundations present | Full install/repair/upgrade/rollback/uninstall/Windows matrix |
| CP14-D | Signature inventory/verifiers implemented | Approved publisher and every final executable valid |
| CP14-E | SBOM/manifest/attestation pipeline implemented | Final candidate SBOM/provenance/AV/license/alert evidence |
| CP14-F | Updates fail closed | Complete adversarial signed-update matrix |
| CP14-G | Register structure passes | Ten legal/authority actions and notices approved |
| CP14-H | Legacy installer payload excluded | Full disposition and signed-runtime reachability proof |

Details: `reports/production-readiness/2026/phase-14/deferred-gates.md`.

## Phase 15 retained release gates

| Checkpoint | Engineering checkpoint evidence | Open closure evidence |
|---|---|---|
| CP15-A | Candidate inputs frozen; integrity and payload checks pass | Signed clean install, repair, upgrade, rollback, uninstall, reboot, sleep/resume, collision, and Windows matrix |
| CP15-B | Packaged backend reached the production startup gates | Real installed five-service workflows, both providers, offline mode, MCP, simulation, and durable-effect proof |
| CP15-C | Protected-storage and signature boundaries fail closed | Complete installed service/provider/gateway/content/resource fault and recovery matrix |
| CP15-D | Release build and short source-level resource checks exist | Ratified hardware budgets, concurrency/load proof, 24-hour stress, and 72-hour idle/normal-use soak |
| CP15-E | Payload leakage gate passes; unsigned state is explicit | Final RC security/privacy/network/egress/malware/license/penetration and independent review |
| CP15-F | Source accessibility and documentation gates exist | Packaged visual/scaling/high-contrast, manual keyboard/NVDA, and clean-document walkthrough |
| CP15-G | Pilot protocol exists | Named multi-day pilot on two clean non-development Windows machines with signed acceptance |
| CP15-H | Gateway contracts and source tests pass | Signed-RC same-host/private client native, SSE, async/cancel, SDK, TLS/firewall, recovery, and UI acceptance |

Details: `reports/production-readiness/2026/phase-15/deferred-gates.md`.

## Phase ledger

| Phase | Result | Status |
|---:|---|---|
| 0 | Scope, baseline, and authority lock | **Complete 2026-07-13** |
| 1 | Trust boundary and public error closure | **Complete 2026-07-13** |
| 2 | Runtime factory, startup, and capability state | **Complete 2026-07-13** |
| 3 | Full internal service delivery and supervision | **Engineering checkpoint complete 2026-07-13; installed exit gates retained** |
| 4 | Data contracts, migrations, backup, and recovery | **Engineering checkpoint complete 2026-07-13; installed exit gates retained** |
| 5 | Canonical governed reasoning path | **Engineering checkpoint complete 2026-07-13; installed CP5-E retained** |
| 6 | Evidence, confidence, convergence, TruthCore, and KA validity | **Engineering checkpoint complete 2026-07-13; installed CP6-F retained** |
| 7 | Provider execution, latency, privacy, streaming, and offline behavior | **Engineering checkpoint complete 2026-07-13; installed CP7-F retained** |
| 8 | External API Gateway and LLM middleware productization | **Engineering checkpoint complete 2026-07-13; installed gates retained** |
| 9 | Ingestion, retrieval, graph, and memory completion | **Engineering checkpoint complete 2026-07-14; installed gates retained** |
| 10 | Simulation completion | **Engineering checkpoint complete 2026-07-14; installed gates retained** |
| 11 | MCP and connector completion | **Engineering checkpoint complete 2026-07-14; installed gates retained** |
| 12 | UI workflow, Session Library, and accessibility completion | **Engineering checkpoint complete 2026-07-14; installed/manual gates retained** |
| 13 | Observability, diagnostics, compliance semantics, and support | **Engineering checkpoint complete 2026-07-14; installed gates retained** |
| 14 | Packaging, signing, updates, dependencies, and supply chain | **Engineering checkpoint complete 2026-07-14; installed/authority gates retained** |
| 15 | System qualification and release candidate | **Release-candidate engineering checkpoint complete 2026-07-14; installed/signed exit gates retained** |
| 16 | Production documentation replacement and professional review dossier | **CP16-A complete; CP16-B/CP16-C content checkpoints complete with retained exit gates; CP16-D/CP16-E content complete; CP16-F active** |
| 17 | Documentation consolidation and release lock | Blocked by prior phases |
| 18 | Production launch and maintenance | Blocked by prior phases |

## Release blockers retained across phases

- [ ] Zero open P0/P1 findings; every P2 fixed, removed, or owner-accepted with an expiration.
- [ ] One causal governed request path shared by built-in chat and approved clients.
- [ ] Full required data plane installed, supervised, secured, migrated, backed up, restored, and truthfully reported.
- [ ] Every enabled UI control performs its stated real-backend action.
- [ ] Ten legal/distribution authority actions resolved before release.
- [ ] Independent architecture, security, API, usability/accessibility, and operations reviews completed.
- [ ] Signed, timestamped, reproducible Windows artifacts and verified updates.
- [ ] Installed-system accessibility, security, failure, recovery, performance, soak, and human-acceptance evidence.
- [ ] Replace or upgrade ChromaDB when a reviewed patched release exists, rerun
      client/service adversarial qualification, and close alert 389 only from
      verified patched evidence.

## Exact next action

Begin CP16-F replacement closure: verify every merge source against its canonical
target, migrate active inbound links, prove retained requirement/decision/evidence
coverage, and generate the archive/delete proposal. Keep archive/delete authority
false until per-source content, link, retained-evidence, and technical review
pass. Do not archive immutable release evidence.

Continue to retain every CP15-A through CP15-H installed/signed/manual gate,
alert 389, legal/distribution NO-GO, automatic-update disablement, and SeaweedFS
candidate-only status until their required evidence exists.
