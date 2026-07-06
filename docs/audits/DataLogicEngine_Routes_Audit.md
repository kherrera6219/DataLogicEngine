# DataLogicEngine — Routes Full Audit

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.1.0 |
| Last updated | 2026-07-06 |
| Status | Historical / closed route audit |
| Owner | API Platform + Audit Governance |
| Review cadence | Reference-only; update only for archive/status clarification |

**Date:** June 7, 2026 | **Branch:** main | **Scope:** Live code read of all route files

---

## Resolution Status (updated 2026-06-07)

All RT items in the sprint plan below have been completed and merged to `main`.
Commits: `df29906b` (migration), `0eb2b0bb` (Sprint 4 audit), `cc01c15b` (notification DB).

| ID | Status | Commit | Notes |
|----|--------|--------|-------|
| RT-1 | ✅ DONE | `df29906b` | Duplicate `process_document` handlers renamed in `multimodal_routes.py` |
| RT-2 | ✅ DONE | `0eb2b0bb` | `@login_required` on `/suggest` |
| RT-3 | ✅ DONE | `0eb2b0bb` | `settings_bp` registered; `analytics_bp`/`gdpr_bp`/`retention_bp`/`privacy_bp` registered by `app.py` |
| RT-4 | ✅ DONE | `df29906b` | `analytics_bp` registered via `app.py` |
| RT-5 | ✅ DONE | `0eb2b0bb` | `@api_admin_required` on retention `/health` |
| RT-6 | ✅ DONE | `0eb2b0bb` | `user_data_routes.py` cascade-deletes `ChatSession`, `ChatMessage`, `KnowledgeGraphNode` |
| RT-7 | ✅ DONE | `0eb2b0bb` | `_controller` / `_get_controller()` lazy init in `ka_routes.py` |
| RT-8 | ✅ DONE | `0eb2b0bb` | Eager init kept — tests monkeypatch `engine` as public module attr |
| RT-9 | ✅ DONE | `0eb2b0bb` | `_get_compliance_manager()` guard; 503 on None AXIS_SYSTEM |
| RT-10 | ✅ DONE | `cc01c15b` | `UserNotificationPreference` SQL table; no more file-backed prefs |
| RT-11 | ✅ DONE | `0eb2b0bb` | Blueprint `url_prefix='/api/v1/locations'`; all tests updated |
| RT-12 | ✅ DONE | `0eb2b0bb` | Feature flag admin paths → `/api/v1/admin/feature-flags` |
| RT-13 | ✅ DONE | `0eb2b0bb` | `current_app.root_path` replaces 3× `os.path.dirname` in `mcp_routes.py` |
| RT-14 | ✅ DONE | `cc01c15b` | Full SQL migration (threading lock was partial; now complete) |
| RT-15 | ✅ DONE | `0eb2b0bb` | `docs/AUTH_DECORATORS.md` created |
| RT-16 | ✅ DONE | `0eb2b0bb` | `@require_permission(Permission.SYSTEM_ADMIN)` on `transfer_ownership` |
| RT-17 | ✅ DONE | `0eb2b0bb` | Local response helpers removed from `knowledge_routes.py` |
| RT-18 | ✅ DONE | `0eb2b0bb` | Local response helpers removed from `simulation_routes.py` |

**All 18 items closed. No open RT items remain.**

> **Current documentation-review status (2026-07-06):** This file is a closed
> historical route-audit record. The original findings below are preserved for
> traceability and should not be used as current route inventory or active
> remediation instructions. Later single-owner/auth-deprecation work superseded
> multi-user/RBAC remediation language such as ownership-transfer RBAC.

---

---

## Inventory

Two separate route directories exist. Both are in active use.

| Directory | Files | Endpoints | Status |
|---|---|---|---|
| `routes/` (root) | 11 files | ~80 endpoints | Primary — all registered in `routes/__init__.py` |
| `backend/routes/` | 11 files | ~50 endpoints | Secondary — partially registered in `routes/__init__.py` |

**Total live route files: 22.** The prior audit only touched `routes/`. `backend/routes/` was unreviewed.

---

## Part 1 — Critical Issues Found

### ISSUE-1: Three overlapping user data deletion endpoints

This is the most serious finding. Three separate routes all do "delete user data":

| File | Endpoint | Approach |
|---|---|---|
| `routes/user_data_routes.py` | `POST /api/v1/user/data/delete` | Deletes `User` + `SimulationSession` records. Requires `confirm: "DELETE"`. Full audit trail. Owner-protected. |
| `backend/routes/gdpr_routes.py` | `POST /api/v1/gdpr/delete` | Also deletes user data. Different implementation — uses `Chat`, `ChatMessage`, `KnowledgeGraphNode`. Different data scope. |
| `backend/routes/privacy_routes.py` | `POST /api/v1/privacy/purge-request` | Third deletion path. Labeled "Right to be Forgotten." Different models again. |

**Problem:** A user invoking all three gets three different deletion behaviors deleting different model sets. None of them cross-call the others. The actual total data deleted by any single endpoint is partial. The confirmation and audit logic is inconsistent across them. The frontend likely only knows about one of these.

**Verdict:** Consolidate into a single canonical deletion endpoint. `routes/user_data_routes.py` has the most complete implementation (owner protection, confirmation gate, both audit entries). The other two should be deprecated and redirected.

---

### ISSUE-2: Two overlapping user data export endpoints

| File | Endpoint | What it exports |
|---|---|---|
| `routes/user_data_routes.py` | `GET /api/v1/user/data/export` | Profile + `SimulationSession` results. JSON download. |
| `backend/routes/gdpr_routes.py` | `POST /api/v1/gdpr/export` | Also exports user data. Different HTTP method (POST vs GET). Different data scope. |

Same problem as deletion — two endpoints, different data sets, neither complete.

**Verdict:** Same consolidation: `routes/user_data_routes.py` is canonical. GDPR export should be a thin redirect or alias to it, not a separate implementation.

---

### ISSUE-3: `backend/routes/multimodal_routes.py` — 4 routes, all named `process_document`

```
@multimodal_bp.route('/audio/transcribe', methods=['POST'])
def process_document():   ← same function name

@multimodal_bp.route('/audio/synthesize', methods=['POST'])
def process_document():   ← same function name

@multimodal_bp.route('/video/analyze', methods=['POST'])
def process_document():   ← same function name

@multimodal_bp.route('/document/process', methods=['POST'])
def process_document():   ← same function name
```

Flask blueprints disallow duplicate function names within the same blueprint. In Python the last `def process_document()` definition silently overwrites all the earlier ones. This means only `/document/process` is actually wired — the audio and video routes return whatever the last definition does, regardless of which URL was called.

**Verdict:** Rename each handler: `transcribe_audio`, `synthesize_audio`, `analyze_video`, `process_document`. This is a functional bug.

---

### ISSUE-4: `backend/routes/retention_routes.py` — unauthenticated health endpoint

```python
@retention_bp.route('/health', methods=['GET'])
def health_check():
    # NONE — NO AUTH
```

Every other endpoint in `retention_routes.py` is `@api_admin_required`. The health endpoint has no decorator. This is consistent with other health checks in the codebase (storage health, KA health are also open), but retention policy configuration is admin territory — a health probe on the retention service leaks whether the service is running and its configuration state to any unauthenticated caller.

**Verdict:** Add `@api_session_login_required` minimum. Admin-level is not required for a health check but it should not be fully open.

---

### ISSUE-5: `backend/routes/search_routes.py` — unauthenticated `/suggest` endpoint

```python
@search_api.route('/suggest', methods=['GET'])
def search_suggest():
    # NONE — NO AUTH
```

All four other search endpoints require `@login_required`. The suggest endpoint doesn't. If it queries the knowledge graph for autocomplete suggestions it exposes graph content to unauthenticated users.

**Verdict:** Add `@login_required` to match the rest of the blueprint.

---

### ISSUE-6: `backend/routes/settings_routes.py` — not registered

`settings_routes.py` defines `settings_bp` at `/api/v1/settings`. It does not appear anywhere in `routes/__init__.py`. Two endpoints exist — `GET /api/v1/settings/ai` and `POST /api/v1/settings/ai`. Both are unreachable. The frontend settings panel likely calls these and silently fails.

**Verdict:** Register in `routes/__init__.py`. Check whether the frontend is showing a silent error for AI settings.

---

### ISSUE-7: `backend/routes/analytics_routes.py` — not registered

`analytics_routes.py` defines `analytics_bp` at `/api/v1/analytics` with three endpoints: `/overview`, `/activity`, `/mcp`. Not registered anywhere in `routes/__init__.py`. Completely unreachable.

**Verdict:** Register in `routes/__init__.py`, or confirm it was intentionally removed and delete the file.

---

### ISSUE-8: `backend/routes/privacy_routes.py` and `backend/routes/gdpr_routes.py` — not registered

Neither `privacy_bp` nor `gdpr_bp` appears in `routes/__init__.py`. Both files have real implementations (not stubs). The GDPR export and deletion, consent management, and access request endpoints are all unreachable.

**Verdict:** Either register them or consolidate their logic into the already-registered `user_data_routes.py`. Given the overlap with ISSUE-1 and ISSUE-2, consolidation is the right path — don't register more duplicate endpoints.

---

### ISSUE-9: `backend/routes/retention_routes.py` — not registered

`retention_bp` is not in `routes/__init__.py`. Five endpoints including retention policy management and cleanup are unreachable.

**Verdict:** Register it. This is a real admin feature that should be accessible.

---

### ISSUE-10: `api_routes.py` — duplicate `/api/v1/query` and `/api/v1/simulation/run` vs `simulation_routes.py`

`api_routes.py` (`api_bp`) contains:
- `POST /api/v1/query` — full UKG pipeline query, creates a `SimulationSession`, calls gateway
- `POST /api/v1/simulation/run` — starts a simulation, creates a `SimulationSession`

`simulation_routes.py` (`simulation_bp`) contains:
- `POST /api/v1/simulations` — creates a `SimulationSession`
- `POST /api/v1/simulations/<id>/run` — runs a simulation step via the production engine

These partially overlap. `api_routes.py` creates `SimulationSession` records but through a different code path than `simulation_routes.py`. A client can create and run simulations from either surface with different behavior.

**Verdict:** `POST /api/v1/query` in `api_routes.py` is the primary chat/query entry point and should stay. `POST /api/v1/simulation/run` in `api_routes.py` is redundant with `simulation_routes.py` — remove or redirect it. Document clearly which simulation path is canonical.

---

### ISSUE-11: `location_routes.py` — hardcoded URL prefix collision

```python
location_api = Blueprint('location_api', __name__)  # no url_prefix

@location_api.route('/api/locations', methods=['GET'])
```

The prefix `/api` is hardcoded into each route decorator rather than set on the blueprint. This means if registration ever adds a prefix it doubles up. Every other blueprint in the codebase uses `url_prefix` on the Blueprint object. This is also a different URL namespace — `/api/locations` rather than `/api/v1/locations`.

**Verdict:** Move prefix to `Blueprint('location_api', __name__, url_prefix='/api/v1/locations')` and shorten each route decorator to just the path suffix. This also normalizes it to the `/api/v1/` convention used everywhere else.

---

## Part 2 — Moderate Issues

### ISSUE-12: Inconsistent auth decorator usage across blueprints

Three different auth decorators are in use with no documented policy for when to use which:

| Decorator | Used in |
|---|---|
| `@login_required` | `search_routes.py`, `mcp_routes.py`, `settings_routes.py`, `feature_flag_routes.py` |
| `@api_login_required` | `ka_routes.py`, `multimodal_routes.py`, `simulation_routes.py` |
| `@api_session_login_required` | `analytics_routes.py`, `gdpr_routes.py`, `ingestion_routes.py`, `location_routes.py`, `storage_routes.py` |

All three do authentication but with different behavior (session vs desktop token vs either). There is no documented rule for which one a new route should use.

**Verdict:** Document the three tiers explicitly in `routes/__init__.py` or a `docs/AUTH_DECORATORS.md` file. For new routes, the rule should be `@api_login_required` (accepts both session and desktop token) as the default.

---

### ISSUE-13: `compliance_routes.py` — pulls `AXIS_SYSTEM` from `current_app.config`

```python
axis_system = current_app.config.get('AXIS_SYSTEM')
compliance_manager = axis_system.axis_managers.get(7)
```

Every compliance endpoint does this pattern with no guard for the case where `AXIS_SYSTEM` is `None` or `axis_managers` doesn't have key `7`. On a fresh install where the axis system hasn't initialized yet, every compliance endpoint will raise `AttributeError: 'NoneType' object has no attribute 'axis_managers'` and return a raw 500.

**Verdict:** Add a guard: if `not axis_system or 7 not in axis_system.axis_managers` return a proper 503 with message "Compliance manager not yet initialized."

---

### ISSUE-14: `ka_routes.py` — `controller` initialized at module level

```python
controller = get_controller()  # module-level, at import time
```

This runs `get_controller()` at import time, before the Flask app context is available. If `get_controller()` accesses the database or config it will fail on import, crashing the entire app startup.

**Verdict:** Lazy-initialize via `get_controller()` inside each route handler, or use a module-level `None` + `get_or_init_controller()` pattern. Check whether `get_controller()` actually uses app context at import time — if it's pure Python it may be fine, but it's a fragile pattern.

---

### ISSUE-15: `mcp_routes.py` — config file written with hardcoded relative path

```python
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(base_dir, 'config', 'mcp_servers.json')
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump({"mcpServers": new_config}, f, indent=2)
```

Three levels of `os.path.dirname` from the route file to find the config dir. This is brittle — it depends on the exact directory nesting never changing. If the route file moves, the path breaks silently and the config is written to the wrong location.

**Verdict:** Use `current_app.config.get('BASE_DIR')` or an equivalent app-level constant. Do not compute the project root via path traversal from a route file.

---

### ISSUE-16: `simulation_routes.py` — production engine initialized at module level

```python
engine = create_multi_agent_simulation_engine()  # module-level
```

Same pattern as ISSUE-14. Runs at import time. The note says `backend/simulation/simulation_engine.py` was renamed to `multi_agent_engine.py` (from the DUP-3 task) — this import confirms the rename was done correctly. But lazy initialization is still better practice.

---

### ISSUE-17: `notification_routes.py` — preferences stored in `runtime_settings` JSON file, not DB

```python
from backend.storage.runtime_settings import load_storage_settings, save_storage_settings
```

Notification preferences for all users are stored in a single JSON file via `runtime_settings`. This is a flat file keyed by user ID string. In a multi-user local install with concurrent requests this is a read-modify-write race condition — two simultaneous preference saves will corrupt each other's data. Additionally the file grows without bound as users are added.

**Verdict:** Move notification preferences to the `User` model or a `UserPreference` table. This is a simple migration.

---

## Part 3 — Minor Issues / Housekeeping

### ISSUE-18: `knowledge_routes.py` — local `error_response` and `success_response` helpers shadow the shared utils

```python
# In knowledge_routes.py:
def error_response(message, status_code=400):
    return jsonify({"error": message, "success": False}), status_code

def success_response(data, message="Operation successful", status_code=200):
    ...
```

The shared `backend.utils.responses` module provides these with a consistent schema. `knowledge_routes.py` defines its own local versions with a slightly different response shape (`{"error": ..., "success": False}` vs the standard envelope). Same pattern appears in `auth_routes.py` and `simulation_routes.py`.

**Verdict:** Import from `backend.utils.responses` and remove the local definitions. Consistent response shape matters for the frontend.

---

### ISSUE-19: `admin_routes.py` — `ownership_transfer` endpoint has no RBAC guard beyond role check

> **Superseded current-state note (2026-07-06):** This finding is historical.
> The later auth-deprecation work removed the multi-user/RBAC model in favor of
> single-owner authorization. Do not reintroduce RBAC based on this old verdict.

The `transfer-ownership` endpoint checks `current_user.role != 'owner'` directly rather than going through `require_permission`. This means it bypasses the RBAC audit path. It works correctly today because the role check is accurate, but it's inconsistent with the rest of the admin blueprint.

**Historical verdict, superseded:** The original route-audit recommendation was to add `@require_permission(Permission.SYSTEM_ADMIN)` in addition to the role check. Later single-owner/auth-deprecation work removed that RBAC model; do not apply this old verdict to the current codebase.

---

### ISSUE-20: `feature_flag_routes.py` — URLs hardcoded in route decorators, not using blueprint `url_prefix`

```python
feature_flag_bp = Blueprint('feature_flags', __name__)  # no url_prefix

@feature_flag_bp.route('/api/v1/feature-flags', methods=['GET'])
@feature_flag_bp.route('/api/admin/feature-flags/<string:flag_key>', methods=['PATCH'])
@feature_flag_bp.route('/api/admin/feature-flags/audit', methods=['GET'])
```

Same pattern as `location_routes.py` (ISSUE-11). Full paths hardcoded in decorators instead of using `url_prefix`. The admin endpoints use `/api/admin/` prefix while all other admin routes use `/api/v1/admin/`. This inconsistency means the feature flag admin routes are in a different URL namespace from `admin_routes.py`.

**Verdict:** Split into two blueprints: `feature_flag_bp` at `/api/v1/feature-flags` for the user endpoint, and register the admin endpoints under `admin_bp` in `admin_routes.py` where they logically belong.

---

## Part 4 — Files in `backend/routes/` vs Registration Status

| File | Blueprint name | Registered in `routes/__init__.py`? | Verdict |
|---|---|---|---|
| `analytics_routes.py` | `analytics_bp` | ❌ NO | **Register or delete** |
| `gdpr_routes.py` | `gdpr_bp` | ❌ NO | Consolidate into `user_data_routes.py` (see ISSUE-1/2) |
| `ingestion_routes.py` | `ingestion_api` | ✅ YES | OK |
| `location_routes.py` | `location_api` | ✅ YES (try/except) | Fix URL prefix (ISSUE-11) |
| `multimodal_routes.py` | `multimodal_bp` | ✅ YES | Fix duplicate function names (ISSUE-3) |
| `privacy_routes.py` | `privacy_bp` | ❌ NO | Consolidate into `user_data_routes.py` |
| `retention_routes.py` | `retention_bp` | ❌ NO | **Register** |
| `search_routes.py` | `search_api` | ✅ YES | Fix unauthenticated suggest (ISSUE-5) |
| `settings_routes.py` | `settings_bp` | ❌ NO | **Register** |
| `simulation_routes.py` | shim → `routes/simulation_routes.py` | — | OK (shim works) |
| `storage_routes.py` | `storage_api` | ✅ YES | OK |

---

## Sprint Plan — Routes

All tasks in priority order. Tasks marked **BUG** are functional defects today.

| ID | Issue | Task | File(s) | Exit Gate |
|---|---|---|---|---|
| RT-1 | ISSUE-3 **BUG** | Rename 4 duplicate `process_document` functions | `backend/routes/multimodal_routes.py` | Each route has a unique function name; `flask routes` shows 4 distinct endpoints; pytest integration tests pass |
| RT-2 | ISSUE-5 **BUG** | Add `@login_required` to `/suggest` | `backend/routes/search_routes.py` | Unauthenticated GET `/api/search/suggest` returns 401; authenticated returns results |
| RT-3 | ISSUE-6 | Register `settings_bp` | `routes/__init__.py` | `GET /api/v1/settings/ai` returns 200 for authenticated user; frontend settings panel loads |
| RT-4 | ISSUE-7 | Register `analytics_bp` or delete the file | `routes/__init__.py` + `backend/routes/analytics_routes.py` | Either `GET /api/v1/analytics/overview` returns 200, or file is deleted and no test references it |
| RT-5 | ISSUE-9 | Register `retention_bp` | `routes/__init__.py` | `GET /api/v1/retention/policies` returns 200 for admin user |
| RT-6 | ISSUE-1 + ISSUE-2 | Consolidate deletion and export endpoints | `routes/user_data_routes.py` (keep), `backend/routes/gdpr_routes.py` (consolidate), `backend/routes/privacy_routes.py` (consolidate) | Single canonical `POST /api/v1/user/data/delete` deletes all data models (User, SimulationSession, Chat, KnowledgeGraphNode). Single canonical `GET /api/v1/user/data/export` exports all. gdpr and privacy blueprints become thin redirect shims or are removed. |
| RT-7 | ISSUE-14 | Lazy-init `controller` in `ka_routes.py` | `routes/ka_routes.py` | App starts with `controller = None`; first request calls `get_controller()`; no import-time DB access |
| RT-8 | ISSUE-16 | Lazy-init engine in `simulation_routes.py` | `routes/simulation_routes.py` | Same pattern as RT-7 |
| RT-9 | ISSUE-13 | Guard `AXIS_SYSTEM` None case in compliance routes | `routes/compliance_routes.py` | All 6 compliance endpoints return proper 503 JSON (not raw 500) when axis system is uninitialized |
| RT-10 | ISSUE-17 | Move notification prefs to DB | `routes/notification_routes.py` + `models.py` | Preferences stored in `UserPreference` table; concurrent writes do not corrupt; old flat-file data migrated |
| RT-11 | ISSUE-11 | Fix `location_routes.py` URL prefix | `backend/routes/location_routes.py` | Blueprint uses `url_prefix='/api/v1/locations'`; routes use short paths; `/api/v1/locations` responds correctly |
| RT-12 | ISSUE-20 | Fix `feature_flag_routes.py` URL hardcoding | `routes/feature_flag_routes.py` | Blueprint uses `url_prefix`; admin endpoints moved to `/api/v1/admin/feature-flags/` namespace |
| RT-13 | ISSUE-15 | Fix `mcp_routes.py` config path | `routes/mcp_routes.py` | Config path derived from `current_app.config['BASE_DIR']` or equivalent |
| RT-14 | ISSUE-18 | Remove local response helpers from 3 route files | `routes/knowledge_routes.py`, `routes/auth_routes.py`, `routes/simulation_routes.py` | All import from `backend.utils.responses`; response shapes are consistent |
| RT-15 | ISSUE-12 | Document auth decorator policy | `routes/__init__.py` (header comment) or `docs/AUTH_DECORATORS.md` | Document: which decorator for which scenario; new routes default to `@api_login_required` |
| RT-16 | ISSUE-4 | Add auth to retention health endpoint | `backend/routes/retention_routes.py` | `GET /api/v1/retention/health` returns 401 for unauthenticated requests |
| RT-17 | ISSUE-10 | Remove redundant simulation endpoint from `api_routes.py` | `routes/api_routes.py` | `POST /api/v1/simulation/run` removed; `POST /api/v1/simulations` in `simulation_routes.py` is the canonical path |
| RT-18 | ISSUE-19 | Historical: add RBAC to ownership transfer | `routes/admin_routes.py` | Superseded by later single-owner/auth-deprecation work; do not reintroduce RBAC based on this row. |

---

## Route Coverage Summary — All Registered Endpoints

### `routes/` (root)

| Blueprint | Prefix | Endpoints |
|---|---|---|
| `auth_bp` | `/api/v1/auth` | `GET /check`, `GET /csrf-token`, `POST /desktop/challenge`, `POST /desktop/auto-login` |
| `api_bp` | `/api/v1` | `GET /health`, `GET /graph`, `POST /query`, `POST /simulation/run` ← (ISSUE-10: remove last one) |
| `admin_bp` | `/api/v1/admin` | `GET /dashboard`, `GET /users`, `GET /users/<id>`, `PUT /users/<id>/role`, `DELETE /users/<id>`, `POST /users/transfer-ownership`, `POST /cache/clear`, `GET /health` |
| `knowledge_bp` | `/api/v1` | Pillar CRUD, Sector CRUD, Domain CRUD, KnowledgeNode CRUD |
| `ka_bp` | `/api/v1/ka` + `/api/ka` | history, algorithms, execute, categories, workflow, trace, layers, batch, search, dependencies, stats, health |
| `simulation_bp` | `/api/v1` + `/api` | simulations CRUD + step/run/stop |
| `mcp_bp` | `/api/v1/mcp` + `/api/mcp` | servers CRUD, resources, tools, prompts, clients, stats, setup, console, config, start/stop |
| `compliance_bp` | `/api/v1/compliance` | standards CRUD, sector, map-regulatory, audit/export, report/pdf |
| `user_data_bp` | `/api/v1/user/data` | export, delete, summary |
| `notification_bp` | `/api/v1/user/notifications` | GET + POST preferences |
| `feature_flag_bp` | (hardcoded) | GET flags, PATCH flag, GET audit |

### `backend/routes/` (partially registered)

| Blueprint | Prefix | Registered? | Endpoints |
|---|---|---|---|
| `multimodal_bp` | `/api/v1/multimodal` | ✅ | transcribe, synthesize, video, document (all `process_document` — ISSUE-3) |
| `storage_api` | `/api/v1/storage` | ✅ | 13 endpoints — health, metrics, backup, flags, connections, DB management |
| `ingestion_api` | `/api/v1/ingestion` | ✅ | supported types, history, local ingest (sync + async), status |
| `search_api` | `/api/search` | ✅ | nodes, ukg, algorithms, global, suggest (ISSUE-5) |
| `location_api` | `/api/locations` | ✅ (try/except) | CRUD + hierarchy + nearest |
| `analytics_bp` | `/api/v1/analytics` | ❌ | overview, activity, mcp stats — **unreachable** |
| `gdpr_bp` | `/api/v1/gdpr` | ❌ | export, delete, consent (x2), access-request — **unreachable, overlaps user_data** |
| `privacy_bp` | `/api/v1/privacy` | ❌ | purge, tenant-cleanup — **unreachable, overlaps user_data** |
| `retention_bp` | `/api/v1/retention` | ❌ | policies CRUD, cleanup, health — **unreachable** |
| `settings_bp` | `/api/v1/settings` | ❌ | AI settings GET + POST — **unreachable** |
| `simulation_routes.py` | shim | — | Re-exports `simulation_bp` from `routes/` — OK |

---

*DataLogicEngine Routes Full Audit — June 7, 2026 — built from live file reads*

## Change notes for v1.1.0

1. Added metadata and a current-status banner marking this as a closed historical route audit.
2. Added a supersession note to the old ownership-transfer RBAC finding so it is not mistaken for current single-owner auth guidance.
