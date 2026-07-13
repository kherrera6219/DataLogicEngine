# DataLogicEngine Production TODO

## Document status

| Field | Value |
|---|---|
| Last updated | 2026-07-13 |
| Status | Canonical open-work ledger |
| Active plan | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.2.1 |
| Completed phase | Phase 3 engineering checkpoint - Full internal service delivery and supervision |
| Next phase | Phase 4 - Data contracts, migrations, backup, and recovery |
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

## Phase 4 objective

Protect user data across schema changes, service upgrades, backup, restore,
repair, uninstall, and rollback for every required store.

## Phase 4 work packages

- [ ] Publish one ownership matrix for every relational row, Redis key/stream,
      graph node/edge, vector collection/chunk, object, and materialized cache.
- [ ] Define globally stable identifiers and cross-store reference/integrity
      rules; prohibit silent conflict resolution between stores.
- [ ] Inventory all existing schemas and data formats, establish migration
      ordering, and implement versioned forward/rollback migrations.
- [ ] Implement a coordinated backup manifest with store versions, checkpoints,
      hashes, object counts, encryption state, and completion status.
- [ ] Implement clean-root restore, partial-failure recovery, point-in-time
      policy where supported, repair, and rollback without mixed-version state.
- [ ] Define retention, deletion, tombstone, rebuild, and uninstall data-keep/
      data-remove behavior for every store.
- [ ] Prove corruption, disk-full, interrupted migration, backup failure, restore
      failure, and cross-store reconciliation behavior.
- [ ] Keep managed backup/restore actions fail-closed until the complete
      coordinated recovery contract is implemented and verified.

## Phase 3 deferred release gates

| Checkpoint | Required result | Status |
|---|---|---|
| CP3-A | Exact artifacts plus redistribution/security/support approval | Engineering candidates locked; independent reviews and final object selection open |
| CP3-B | Clean install provisions protected loopback-only services | Lab provisioning passed; clean signed-installer proof deferred |
| CP3-C | Instrumented workflows prove real read/write use of every service | Engineering qualification passed; final installed workflow proof deferred |
| CP3-D | Supervisor survives lifecycle/failure/relaunch cases | Start/restart/identity/cleanup passed; full failure matrix continues in Phases 4/15 |
| CP3-E | Installed Storage UI truthfully reports/actions the data plane | UI/backend contract implemented; installed-app proof deferred |

## Phase ledger

| Phase | Result | Status |
|---:|---|---|
| 0 | Scope, baseline, and authority lock | **Complete 2026-07-13** |
| 1 | Trust boundary and public error closure | **Complete 2026-07-13** |
| 2 | Runtime factory, startup, and capability state | **Complete 2026-07-13** |
| 3 | Full internal service delivery and supervision | **Engineering checkpoint complete 2026-07-13; installed exit gates retained** |
| 4 | Data contracts, migrations, backup, and recovery | **Next** |
| 5 | Canonical governed reasoning path | Blocked by prior phases |
| 6 | Evidence, confidence, convergence, TruthCore, and KA validity | Blocked by prior phases |
| 7 | Provider execution, latency, privacy, streaming, and offline behavior | Blocked by prior phases |
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

## Exact next action

Begin Phase 4 by creating the cross-store ownership/identifier matrix and
migration inventory, then implement the coordinated backup manifest and
clean-root restore contract. Keep the managed backup endpoint fail-closed until
all required stores participate in one verified recovery set. Preserve the
SeaweedFS candidate-only boundary and all deferred Phase 3 release gates.
