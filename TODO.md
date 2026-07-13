# DataLogicEngine Production TODO

## Document status

| Field | Value |
|---|---|
| Last updated | 2026-07-13 |
| Status | Canonical open-work ledger |
| Active plan | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.2.0 |
| Completed phase | Phase 1 - Trust boundary and public error closure |
| Next phase | Phase 2 - Runtime factory, startup, and capability state |
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

## Phase 2 objective

Make startup, shutdown, health, service ownership, concurrent launch, and
optional-feature behavior deterministic and testable without weakening Phase 1.

## Phase 2 work packages

- [ ] Replace import-time global application construction with one real app factory.
- [ ] Divide startup into explicit configuration, paths/ACL, lock, supervisor,
      version/credential, migration, store initialization, route/worker, and
      readiness phases.
- [ ] Prohibit route/optional-integration imports from starting stores, threads,
      event loops, network clients, or destructive key initialization.
- [ ] Replace per-call database lifecycle managers with one process-life service supervisor.
- [ ] Model every required service as `not_installed`, `stopped`, `starting`,
      `migrating`, `ready`, `degraded`, `failed`, `stopping`, or `blocked` with a safe reason.
- [ ] Return truthful per-service start/stop results and verify service/process identity, not just ports.
- [ ] Detect foreign port owners and fail or select an approved configured port with a repair action.
- [ ] Define dependency order and bounded budgets for PostgreSQL, Redis, Neo4j,
      MinIO, Chroma, workers, backend readiness, and shutdown.
- [ ] Implement graceful drain/checkpoint/cancellation plus bounded forced cleanup.
- [ ] Recover stale locks and orphaned child processes after crashes.
- [ ] Publish public-safe `/live` and `/ready` plus authenticated capability state with correlation IDs.
- [ ] Make Electron wait for core readiness and render capability-level degradation truthfully.
- [ ] Treat required-service failure as not ready; prohibit production fallback to SQLite, memory, or local files.
- [ ] Add deterministic failure injection for every startup phase.
- [ ] Add installation identity, exclusive lifecycle/runtime lock, stale-owner recovery, and verified supervisor ownership.
- [ ] Coordinate install, update, repair, backup, restore, and uninstall through the same exclusive lock.
- [ ] Handle sleep, hibernate, resume, logoff, shutdown, time adjustment, and forced termination.
- [ ] Enforce supported concurrent-launch and multi-Windows-user isolation behavior.
- [ ] Verify backend/child product version and Windows session before trusting health or lifecycle commands.
- [ ] Keep the API gateway listener supervised and loopback-only/disabled until Phase 8.
- [ ] Drain or reject new work during shutdown, migration, backup, restore,
      update, certificate failure, or policy-store failure and durably finalize admitted work.

## Phase 2 checkpoints

| Checkpoint | Required result | Status |
|---|---|---|
| CP2-A | Multiple isolated app instances have no shared state, ports, threads, or DB collisions | Next |
| CP2-B | One process-life supervisor owns every required service | Open |
| CP2-C | Liveness, readiness, and capabilities are truthful | Open |
| CP2-D | Graceful/forced shutdown and crash recovery leave no data loss or orphan processes | Open |
| CP2-E | Concurrent launch, lifecycle collision, Windows event, and cross-user cases follow the approved contract | Open |

## Phase 2 mandatory validation

```powershell
python -m pytest tests/unit tests/integration_routes -q
python scripts/runtime_precheck.py --strict --allow-env-from-process
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/start_local_stack.ps1 -WithDataServices
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/stop_local_stack.ps1 -WithDataServices
```

New evidence must cover startup-phase failure injection, repeated lifecycle
cycles, foreign-port ownership, backend crash cleanup, Electron close during
active work, concurrent installer/updater/backend/renderers, second-user
isolation, Windows power/session/time events, low/read-only disk, corrupt config,
and stale lock recovery.

## Phase ledger

| Phase | Result | Status |
|---:|---|---|
| 0 | Scope, baseline, and authority lock | **Complete 2026-07-13** |
| 1 | Trust boundary and public error closure | **Complete 2026-07-13** |
| 2 | Runtime factory, startup, and capability state | **Next** |
| 3 | Full internal service delivery and supervision | Blocked by Phase 2 |
| 4 | Data contracts, migrations, backup, and recovery | Blocked by prior phases |
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

Start CP2-A with a live import/startup side-effect inventory. Add a failing test
that creates two application instances and proves the current global app cannot
isolate configuration, extensions, stores, workers, or lifecycle state. Design
the app-factory/runtime-ownership boundary before moving initialization code.
