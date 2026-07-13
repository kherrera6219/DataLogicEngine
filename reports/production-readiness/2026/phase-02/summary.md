# Phase 2 Evidence Summary

## Status

| Field | Value |
|---|---|
| Phase | 2 - Runtime factory, startup, and capability state |
| Started | 2026-07-13 |
| Completed | 2026-07-13 |
| Current checkpoint | CP2-A through CP2-E pass |
| Release posture | Phase 2 GO; overall production/public release remains NO-GO pending Phases 3-18 |

## Closure results

1. `create_app()` now builds isolated Flask applications without constructing an
   application, opening a port, creating a key, starting a thread, or connecting
   to a service when `app.py` is imported.
2. Each application owns its runtime, metrics, service supervisor, WebSocket
   extension, SQLAlchemy engine, security services, stores, and lifecycle state.
3. Startup follows nine deterministic phases: configuration, paths/ACL, runtime
   lock, service supervisor, service verification, migrations, stores,
   routes/workers, and readiness. Every phase has a failure-injection test.
4. One typed supervisor publishes per-service state, dependency order, start/stop
   budgets, identity, safe reason, and per-operation results. Port occupancy is
   never treated as proof that an app-owned service is healthy.
5. Production startup refuses SQLite, automatic schema creation, missing required
   services, foreign service identity, and incompatible installation versions.
6. `/live`, `/ready`, `/health`, authenticated capabilities, and authenticated
   desktop lifecycle events publish separate, correlation-aware contracts.
7. Runtime ownership uses a per-user installation identity, OS file lock, version
   record, exclusive lifecycle operations, stale-lock recovery, and fail-closed
   cross-user behavior.
8. Electron waits for `/ready`, renders actual runtime/service degradation, sends
   signed Windows lifecycle events, and performs bounded shutdown even when an
   active request does not finish.
9. The import/startup static gate scans 59 high-risk modules with zero direct
   resource-start findings. MCP event loops are operation-local and optional
   integrations are lazy and application-owned.
10. A real development start/readiness/stop cycle returned healthy `/live`,
    `/ready`, and `/health` responses and left ports 3000/5000 closed. The
    full-data command detected foreign DevOnz listeners on the standard data
    ports, refused to reuse them with a repair action, and started no backend.
11. MinIO/Chroma production service adapters, pinned OCI delivery, protected
    per-install service credentials, and complete five-service installed use are
    intentionally the Phase 3 boundary. Their absence remains a production
    readiness blocker; no fallback is reported as production-ready.

## Validation summary

- Backend unit and integration routes: **590 passed, 17 skipped** (17 existing
  SQLAlchemy legacy warnings).
- Security and integration routes: **398 passed** (18 non-blocking warnings).
- Frontend: **81 files / 403 tests passed**.
- Focused Electron lifecycle/status tests: **10 passed**.
- Ruff, TypeScript, production Next standalone/export builds, Electron compile,
  packaged Electron security, startup-side-effect, route-manifest, public-error,
  secret-storage, and runtime-precheck gates: **pass**.
- Frontend lint: **0 errors, 1 pre-existing warning**.
- Runtime surface inventory: **426 Flask routes**, 12 GraphQL operations, 19 IPC
  channels, 6 MCP methods, 5 file capabilities, and 5 network surfaces; zero
  unclassified entries or unauthenticated mutation evidence gaps.

Phase 2 is ready for its phase commit. Phase 3 must deliver and qualify the real
five-service production data plane without weakening this ownership/readiness
contract.
