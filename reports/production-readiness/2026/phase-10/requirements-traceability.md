# Phase 10 Requirements Traceability

Date: 2026-07-14

| Requirement | Primary implementation | Primary evidence |
|---|---|---|
| One authoritative engine | `docs/adr/ADR-0007-authoritative-simulation-engine.md`, production entry-point removals | `test_no_production_entry_point_imports_legacy_simulation_engines` |
| Versioned scenario/plan/budget/artifact/result | `backend/simulation/contracts.py` | Phase 10 contract tests |
| Non-recursive bounded provider | `provider_adapter.py`, `providers.py` | call-cap, content-free ledger, no-recursion, cost-preflight tests |
| Durable lifecycle and restart | `jobs.py`, `job_coordination.py`, Phase 10 migration | persistence, pause/resume, restart-safe/unsafe tests |
| Evidence and confidence truth | `validation.py`, canonical output controls in `jobs.py` | evidence-coverage and qualification-only tests |
| S3/graph/vector materialization | `jobs.py`, `materialization_dispatcher.py` | artifact state, outbox, cross-store tests |
| Truthful API and UI | `simulation_routes.py`, `frontend/app/simulations/page.tsx` | canonical route, legacy alias, page, and API client tests |
| Runtime worker ownership | `app.py`, `tests/conftest.py` | full regression and Windows worker-drain rerun |
