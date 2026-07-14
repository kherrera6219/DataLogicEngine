# DataLogicEngine Production TODO

## Document status

| Field | Value |
|---|---|
| Last updated | 2026-07-14 |
| Status | Canonical open-work ledger |
| Active plan | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.7.0 |
| Completed phase | Phase 9 engineering checkpoint - Ingestion, retrieval, graph, and memory completion |
| Next phase | Phase 10 - Simulation completion |
| Release decision | Production/public release: **NO-GO** |
| Historical backlog | `docs/archive/session-history/TODO_through_2026-07-12.md` |

This file contains current open work only. Detailed requirements, stop
conditions, and exit gates remain authoritative in the active root plan.

## Completed checkpoints

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
| 10 | Simulation completion | **Active** |
| 11 | MCP and connector completion | Blocked by prior phases |
| 12 | UI workflow, project model, and accessibility completion | Blocked by prior phases |
| 13 | Observability, diagnostics, compliance semantics, and support | Blocked by prior phases |
| 14 | Packaging, signing, updates, dependencies, and supply chain | Blocked by prior phases |
| 15 | System qualification and release candidate | Blocked by prior phases |
| 16 | Production documentation replacement and professional review dossier | Blocked by prior phases |
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

Begin Phase 10 with a live comparison of the multi-agent debate and FROST
simulation implementations, every simulation route/caller/UI control, provider
recursion and budget path, PostgreSQL/Redis/Neo4j/Chroma/S3 persistence, and
pause/resume/cancel/retry/restart behavior. Add failure-first authority,
recursion, budget, cancellation, persistence, and deterministic-seed tests;
then select one engine in an ADR before extending runtime behavior. Preserve
`governed.v1`, every installed Phase 3-9 gate, alert 389, and the SeaweedFS
candidate-only Replacement Control boundary.
