# Repository Audit Log

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-06-04 |
| Status | Active |
| Owner | Platform Architecture |
| Review cadence | Per audit session |

## Purpose

Track structural/architectural audits of the DataLogicEngine repository: what was
reviewed, what was changed, why, and what remains open. This lets future audit
sessions resume with full context instead of re-deriving findings.

The audit philosophy is **local-first / desktop-only**: the product is a licensed,
BYOK Windows desktop application (not multi-tenant SaaS). Code, tests, and docs are
expected to reflect that. Legacy web-app and external-SaaS assumptions are removed
when found.

---

## Session — 2026-06-04

### Scope

Whole-application review (backend, core, frontend wiring, routes, scripts, tests,
docs) with an emphasis on layering correctness, dead/legacy code, and failing CI.

### Changes landed

#### 1. Layering fix — integrity helpers moved to `core/`

- Moved the pure, dependency-free hashing/HMAC helpers from
  `backend/security/integrity.py` to `core/security/integrity.py` (byte-identical
  content).
- Added `core/security/__init__.py` re-exporting the helpers.
- `backend/security/integrity.py` is now a backwards-compatible re-export shim.
- Updated the two core importers (`core/simulation/trace_system.py`,
  `core/system/frost_service.py`) to import from `core.security.integrity`.
- **Why:** removed two `core -> backend` import inversions, restoring the
  documented `backend -> core` dependency direction (see `ARCHITECTURE.md`,
  `FILE_STRUCTURE.md`). No behavior change.

#### 2. Test suite — desktop-only auth model

The public web `/api/v1/auth/register`, `/login`, `/logout`, `/mfa/*`, and
`/step-up` routes were intentionally removed in a prior commit
(`refactor(auth): remove dead web-app auth routes; keep desktop-only endpoints`).
The supported auth entry point is the desktop auto-login flow
(`/api/v1/auth/desktop/*`), which ends by calling `flask_login.login_user(user)`.
Many tests still authenticated via the removed web routes, causing a large
`401`/`404` failure cascade.

- Added a shared, route-independent `seed_login_session(...)` helper in
  `tests/conftest.py` that provisions a local user and seeds the Flask-Login
  session directly (reproducing a successful desktop auto-login).
- Rewrote `authenticated_client` and refactored per-file login helpers/fixtures in
  `tests/integration_routes/test_admin_routes.py`,
  `tests/integration_routes/test_route_coverage_expansion.py`,
  `tests/integration/test_api_endpoints.py`,
  `tests/compliance/test_gdpr_comprehensive.py` to use it.
- Removed the obsolete `TestAuthenticationEndpoints` class (tested deleted web
  register/login/logout) from `tests/integration/test_api_endpoints.py`.
- Updated `tests/contract/test_canonical_v1_route_contracts.py` to drop the removed
  auth endpoints from the canonical authenticated-failure contract.
- Repointed contradictory assertions (e.g. a test asserting `/api/v1/auth/login`
  must exist) to assert the route is removed.

#### 3. Removed legacy external SaaS connectors (Jira, Salesforce)

These are not part of a local-first desktop product.

- Deleted `backend/mcp_server/tools/jira.py` and
  `backend/mcp_server/tools/salesforce.py`.
- Emptied the tool imports in `backend/mcp_server/tools/__init__.py`.
- Removed `salesforce`/`jira` from `KNOWN_CONNECTORS` in
  `backend/mcp_server/connector_metrics.py`.
- Removed the Jira webhook secret and processor from
  `backend/webhook_server/webhook_server.py`.
- Deleted the connector-specific tests; repointed generic connector-framework
  tests (`test_latency_slo_alerts.py`, `test_phase1_scope_ssrf_controls.py`) to use
  the still-supported `github` connector label.

#### 4. Security scan — Bandit MD5 hardening

- Added `usedforsecurity=False` to non-security MD5 content fingerprints in
  `core/simulation/pov_delta.py`, `core/simulation/query_analysis_system.py`, and
  `core/simulation/coordinate_system.py`. Cleared the 3 high-severity/high-
  confidence Bandit findings in the delta gate.

#### 5. RAG embedding failover tests

- `RAGService._default_embedding` fails closed in production and only returns a
  mock embedding when `ALLOW_MOCK_EMBEDDINGS=true` or `FLASK_ENV` is
  development/testing. Updated `tests/unit/test_services.py` and
  `tests/integration/test_rag_service_coverage.py` to set that flag when exercising
  the mock-fallback path.

#### 6. Documentation reference fixes

- `docs/MCP_INTEGRATION.md`: corrected stale paths
  (`backend/mcp_api.py` -> `routes/mcp_routes.py`,
  `frontend/src/pages/MCPConsolePage.js` -> `frontend/app/mcp/page.tsx`).

### Verification

- Full local suite: **1806 passed, 27 skipped, 0 failed** (`pytest tests/ --no-cov`).
- `ruff check .`: clean.
- Bandit: 0 high-severity issues in `backend/ core/`.
- `scripts/verify_docs_references.py`: 0 errors.

---

## Open items / recommendations (not yet actioned)

These were identified but deliberately left for future sessions to keep changes
low-risk and reviewable.

### Layering

- **~26 remaining `core -> backend` import lines** across ~10 core modules
  (beyond the integrity helpers fixed this session). Each needs either a Protocol/
  interface extraction, a lazy import to break a cycle, or relocation of the
  symbol into `core/`. Recommend tackling in small, per-subsystem PRs with tests at
  each step.

### `core/simulation/` cleanup

- The `legacy_*` simulation modules (`legacy_simulation_engine.py`,
  `layer2_legacy_knowledge.py`, `layer5_legacy_integration.py`,
  `layer1_legacy_entry.py`) are **load-bearing** (live importers), not dead code.
  Any rename/retire requires migrating importers first — a real refactor, not a
  file move.
- The apparent "duplicate" layer files are an intentional two-tier split:
  the smaller files (`layer8_quantum.py`, `layer9_recursive.py`,
  `layer10_synthesis.py`) are the runtime path imported by `simulation_engine.py`;
  the larger files (`*_computer.py`, `*_agi.py`, `layer10_self_awareness.py`) are
  demo/research-only. Keep both; do not merge.
- `core/simulation/truth_engine.py` appears orphaned (no importers). Decide:
  keep as a deliberate domain-scoring API surface, or remove as dead code. It is
  distinct from the backend `truth_engine/` enterprise gateway (no overlap).

### Encryption posture

- `EncryptionManager` uses Fernet (AES-128-CBC). Several docs reference AES-256-GCM
  as target state. Either upgrade the implementation or clarify the docs as
  roadmap, but do not assert AES-256-GCM as implemented.

### Doc drift (lower priority)

- `docs/archive/*` is explicitly NOT source of truth; archived references (e.g.
  `backend/auth/dpapi_store.py`, now `backend/security/dpapi_store.py`) were left
  untouched by design.

## Change notes for v2.6.0

- 2026-06-04: Initial audit log created. Recorded the 2026-06-04 session
  (layering fix, desktop-only auth test alignment, legacy connector removal,
  Bandit MD5 hardening, RAG test fixes, MCP doc path corrections) and the open
  items backlog for future audits.
