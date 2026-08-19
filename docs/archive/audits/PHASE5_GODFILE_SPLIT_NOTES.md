# Phase 5 god-file split notes

| Date | 2026-08-12 |
|---|---|

## Completed in Phase 5

| Deliverable | Path |
|---|---|
| Startup contract | `backend/runtime/startup_contract.py` (wired into `app.py` / legacy factory) |
| L1–L10 layer contracts | `backend/governed_execution/layer_contracts.py` |
| Electron path/env helpers | `frontend/electron/paths.ts`, `env-flag.ts` (used by `main.ts`) |
| Helper scripts | `scripts/_phase5_package_splits.py` (historical; package approach reverted) |

## Attempted then reverted

Converting `backend/llm_gateway/api.py` and `backend/routes/mcp_routes.py` into packages broke extensive test patches that target:

- `backend.llm_gateway.api.LLMGateway`
- `backend.llm_gateway.api.AtomicGatewayLimiter`
- `backend.llm_gateway.api.get_gateway_job_runner`
- etc.

Those names must remain bound in the **module** `backend.llm_gateway.api` (not only in a subpackage) for `unittest.mock.patch` to work.

## Safe future split pattern

1. Extract **pure helpers** first (no Flask routes).
2. Extract route groups into modules that are **imported into** `api.py` so symbols remain on `api` namespace:
   ```python
   # api.py
   from backend.llm_gateway.api_admin import *  # registers on admin_bp defined in api.py
   ```
3. Or define blueprints in `api.py` and pass them into route modules:
   ```python
   # api_admin.py
   def register(admin_bp): ...
   ```
4. Re-run `tests/integration/test_gateway_api_coverage.py` after every move.

## Deferred (Phase 5 residual)

| File | Approx size | Status |
|---|---:|---|
| `backend/llm_gateway/api.py` | ~3.1k lines | Monolith retained intentionally |
| `backend/routes/mcp_routes.py` | ~1.9k lines | Monolith retained intentionally |
| `backend/governed_execution/orchestrator.py` | ~2.7k lines | Layer contracts only; body split deferred |
| `frontend/electron/main.ts` | ~1.8k lines | Partial extract (paths/env); full IPC split deferred |
