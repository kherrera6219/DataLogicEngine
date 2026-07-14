# DataLogicEngine Production TODO

## Document status

| Field | Value |
|---|---|
| Last updated | 2026-07-13 |
| Status | Canonical open-work ledger |
| Active plan | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.5.0 |
| Completed phase | Phase 6 engineering checkpoint - Evidence, confidence, convergence, TruthCore, and KA validity |
| Next phase | Phase 7 - Provider execution, latency, privacy, streaming, and offline behavior |
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

- [ ] Inventory provider/model factories, SDK call types, request-wide timeout
      gaps, retries/failover, cancellation, streaming, usage/cost, egress,
      offline queue/replay, and UI states.
- [ ] Generate one supported OpenAI/Google provider/model capability manifest
      for Python, TypeScript, tests, and docs.
- [ ] Remove unknown-provider fallback and unsupported production factories and
      probes; retain only explicit archived/disabled compatibility evidence.
- [ ] Enforce one request-wide deadline and cancellation path through retrieval,
      provider execution, validation, persistence, and refinement.
- [ ] Implement truthful streaming, retry/failover, quota/cost, privacy/egress,
      and offline/replay contracts with failure-first tests.
- [ ] Preserve separate installed corpus approval for every supported
      provider/model combination; provider-disabled checks cannot approve live
      paths.

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
| 7 | Provider execution, latency, privacy, streaming, and offline behavior | **Active** |
| 8 | External API Gateway and LLM middleware productization | Blocked by prior phases |
| 9 | Ingestion, retrieval, graph, and memory completion | Blocked by prior phases |
| 10 | Simulation completion | Blocked by prior phases |
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

Begin Phase 7 with a live inventory of supported/legacy provider factories,
model defaults, SDK calls, deadlines, retries, cancellation, streaming, cost and
quota accounting, privacy/egress, offline queue/replay, and UI state. Add
failure-first provider contract tests before consolidating the OpenAI/Google
manifest or removing unsupported paths. Preserve CP5-E, CP6-F, all Phase 3/4
installed gates, alert 389, and the SeaweedFS candidate-only boundary.
