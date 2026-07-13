# DataLogicEngine Production TODO

## Document status

| Field | Value |
|---|---|
| Last updated | 2026-07-13 |
| Status | Canonical open-work ledger |
| Active plan | `PRODUCTION_COMPLETION_PLAN_2026.md` v1.2.0 |
| Completed phase | Phase 2 - Runtime factory, startup, and capability state |
| Next phase | Phase 3 - Full internal service delivery and supervision |
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

## Phase 3 objective

Make PostgreSQL, Redis, Neo4j, ChromaDB, and MinIO a supported, app-owned
production data plane installed and controlled through the Phase 2 supervisor.

## Phase 3 work packages

- [ ] Pin immutable PostgreSQL, Redis, Neo4j/JRE, ChromaDB, and MinIO versions/
      digests and complete the redistribution/license matrix.
- [ ] Provision the OCI data plane through the app supervisor with per-install
      names, loopback-only ports, resource limits, and verified image identity.
- [ ] Generate unique service credentials, protect them with DPAPI/ACLs, and
      remove known/default secrets and plaintext production `.env` dependency.
- [ ] Make PostgreSQL the production SQLAlchemy authority with explicit roles,
      SCRAM, migrations, connection budgets, and PostgreSQL-specific tests.
- [ ] Make Redis the production cache/session/rate-limit/queue/stream service with
      auth, persistence, eviction, replay, retry, and dead-letter contracts.
- [ ] Make Neo4j the durable graph authority with schema/version, conflict,
      reconciliation, reconstruction, restart, and traversal tests.
- [ ] Define and qualify the Chroma collection registry, embedding compatibility,
      rebuild/migration, source reconciliation, health, backup, and restore.
- [ ] Restore MinIO as the production object backend with least privilege,
      required buckets, metadata/integrity, lifecycle, and real operation tests.
- [ ] Route start/stop/restart/repair/verify/backup/restore through the singleton
      supervisor and show installed version, identity, status, size, migration,
      backup, and safe reason in the Storage UI.

## Phase 3 checkpoints

| Checkpoint | Required result | Status |
|---|---|---|
| CP3-A | Versions, digests, licenses, hardware, and delivery mechanism locked | Next |
| CP3-B | Clean install provisions unique protected credentials and loopback-only services | Open |
| CP3-C | Instrumented workflows prove real read/write use of every required service | Open |
| CP3-D | Supervisor survives start/stop/restart/crash/port conflict/app relaunch | Open |
| CP3-E | Installed Storage UI truthfully reports/actions the five-service data plane | Open |

## Phase 3 mandatory validation

```powershell
python scripts/setup_local_databases.py --verify
python scripts/verify_local_data_stack.py
python scripts/validate_schema_parity.py --report reports/schema_parity_report_local.json
python -m pytest tests/integration tests/integration_routes -q
```

Create `scripts/verify_internal_data_plane.py --profile production --require-all
--json <report>`. A skipped required service is a production failure.

## Phase ledger

| Phase | Result | Status |
|---:|---|---|
| 0 | Scope, baseline, and authority lock | **Complete 2026-07-13** |
| 1 | Trust boundary and public error closure | **Complete 2026-07-13** |
| 2 | Runtime factory, startup, and capability state | **Complete 2026-07-13** |
| 3 | Full internal service delivery and supervision | **Next** |
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

Start CP3-A by inventorying the live container/image/binary/JRE versions,
digests, floating tags, licenses, and redistribution obligations. Replace
`minio/minio:latest` and every other floating/unqualified production service
input before provisioning or changing data contracts.
