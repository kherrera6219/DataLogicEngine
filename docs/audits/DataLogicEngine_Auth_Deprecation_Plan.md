# DataLogicEngine — Multi-User Auth Deprecation Plan

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.1.0 |
| Last updated | 2026-07-06 |
| Status | Historical / completed deprecation plan |
| Owner | Security Engineering |
| Review cadence | Reference-only; update only for archive/status clarification |

**STATUS (2026-06-19): ✅ COMPLETE — Phases A–F done.** Single-mode fully realized:
no MFA, no multi-tenant RLS, no admin user-mgmt UI/routes, no roles/admin columns; all
authorization gates collapsed to a single-owner check (`current_user_is_owner()`).
`password_hash` retained (user decision); `tenant_id` columns/reads left in place (wider
than RLS — separate concern). Final commit `950eda75` (E-2c). Original status below.

**STATUS (2026-06-19, superseded): Phases A + B + C-partial + D DONE.** Clean wins done
(~1,900 LOC of dead/obsolete active auth code removed: zero_trust, token_manager,
rbac; authz decorators collapsed; stale CSRF entries dropped; plan corrected;
5 pre-existing desktop tests fixed). **Phase D done 2026-06-19** — MFA module +
tenant_rls removed (`b4c1fa69`, `c60f3daf`); see §3 Phase D. **Remaining: Phase E**
(slim `User` — drop `role/is_admin/mfa_*` columns + the `verify_totp` shim, decide
`password_hash`; remove admin user-mgmt routes ↔ `frontend/app/admin/page.tsx`) **and
Phase F** (test migration). These are cross-cutting (frontend + DB migration), so
remove as coordinated frontend+backend feature changes, not a backend sweep. See the
entanglement note in §3.

**Original status:** PROPOSAL — for review before any code changes.
**Authored:** 2026-06-13 (during A10 `backend/security/` audit).
**Trigger:** App is now **local-first, single operating mode**. Authentication is
handled at the **OS access level**; even cloud runs on a single-tenant VM. The old
multi-user model (application login, roles, access tiers) is gone — see memory
`architecture-single-mode`.

> **Current documentation-review status (2026-07-06):** This file preserves the
> auth-deprecation planning history. Do not execute the original proposal sections
> below as current instructions. The live auth model keeps Flask sessions, signed
> desktop loopback auth, and `ExternalAPIKey`/`ukg_...` programmatic access as
> documented in `docs/AUTH_DECORATORS.md`, `docs/API.md`, and `docs/SECURITY.md`.

---

## 1. Guiding principle

> **Keep the local security boundary; remove the multi-user authorization layer.**

What stays is the mechanism that proves a request came from the legitimate OS user
on this machine. What goes is everything that distinguished *one app user from
another* (roles, admin, per-user login/sessions, MFA, multi-tenant isolation, JWT).

### KEEP (this is the current single-user auth — already implemented and working)
- `backend/auth/windows_identity.py` — resolves the Windows SID identity.
- `backend/security/desktop_local_auth.py` — signed Electron loopback request
  verification (install-secret HMAC + nonce + skew window). This prevents *other
  local processes* from hitting the loopback backend; it remains a real boundary.
- `backend/auth/api_decorators.py::check_desktop_request_auth` + the
  `_get_or_create_desktop_user` SID→User resolution.
- `models.User.sid`, `username`, `email` (identity, not authorization).

### REMOVE / COLLAPSE (obsolete under single-mode)
| Concern | Module(s) | Current wiring | Action |
|---|---|---|---|
| Zero-trust engine | `backend/security/zero_trust.py` | **0 live importers** (2 tests only) | ✅ **REMOVED (Phase A, `57b912da`)** |
| JWT/token manager | `backend/security/token_manager.py` | **0 live importers** (1 test only) | ✅ **REMOVED (Phase A, `57b912da`)** |
| RBAC / permissions | `backend/security/rbac.py` | 5 refs: `admin_routes`, `mcp_routes`, `privacy_routes`, `extensions.py`, `scripts/scan_backend_routes.py` | ✅ **REMOVED (Phase B, `e710aeb3`)** |
| Multi-session mgr | `backend/security/session_manager.py` | 1 ref: `app.py` | ⚠️ **KEEP (correction)** — it's session-cookie *security* hardening (rotation/invalidation/secure storage) for the owner's session, not a multi-user login. `MAX_CONCURRENT_SESSIONS=3` is vestigial but harmless. |
| Per-user MFA | `backend/security/mfa.py` | `extensions.py`, `models.py` (`User.verify_totp`) | De-wire, delete; drop `User.mfa_enabled`/`mfa_secret` (Phase D — confirmed vestigial: `auth_routes` docstring says MFA was removed from the flow). |
| Multi-tenant RLS | `backend/security/tenant_rls.py` | 1 ref: `app.py` | De-wire, delete (Phase D) — verify it's not providing per-row security still relied on. |
| ~~Web login flow~~ | `backend/routes/auth_routes.py`, `LoginManager` | registered | ⚠️ **KEEP (correction)** — `auth_routes.py` is the **desktop Windows-identity auth** (its docstring: "Web-app patterns … have been removed"), and `LoginManager`/`current_user` back the owner's session across 25 live files. NOT removable. |
| API-key branch | `check_api_auth` `ukg_`/`ExternalAPIKey` path | many consumers (`api_gateway`, `unified_middleware`, `chat`, …) | ⚠️ **KEEP (correction)** — live, not dead. |
| **Admin/user-mgmt routes** | `backend/routes/admin_routes.py` (16 decorators) | registered | **Vestigial** — user CRUD / role update / `transfer-ownership` / role-gated dashboard. No users/roles/owner under single-mode. Remove the user-mgmt + ownership routes; retain operational endpoints (cache clear, health) ungated. (Phase C — **verify frontend has no admin/user pages calling them first.**) |
| Stale CSRF-exempt entries | `app.py` `CSRF_API_EXEMPT_PATH_PREFIXES` | `/auth/login`, `/auth/register`, `/auth/mfa/verify`, `/auth/callback/sso` | Remove — these reference routes that **no longer exist** (auth_routes only has `/check`, `/csrf-token`, `/desktop/*`). |
| Admin/permission decorators | `api_admin_required`, `require_permission` | part of the 147 decorator usages | Collapse to single-owner pass-through |
| User authz fields | `models.User.role`, `is_admin`, `mfa_*`, possibly `password_hash` | columns + indexes | Drop after de-wiring (migration) |

---

## 2. The 147-decorator question (the main entanglement)

> Historical note: the proposal language in this section is superseded by the
> completed implementation and later route-hardening slices. Current
> `@api_login_required` behavior accepts Flask session auth, signed desktop
> loopback auth, and valid `ExternalAPIKey` principals. Current
> `@api_session_login_required` accepts Flask session auth or signed desktop
> loopback auth. Do not remove those paths based on this historical plan.

`@api_login_required` / `@api_session_login_required` / `@require_permission` /
`@api_admin_required` appear **147 times** across `backend/routes/*.py` + `app.py`
(heaviest: `mcp_routes` 31, `admin_routes` 16, `storage_routes` 13, `knowledge_routes`
12, `ka_routes` 12).

**Do NOT delete the 147 call sites.** Instead, redefine the decorators centrally in
`backend/auth/api_decorators.py`:

- Historical proposal, superseded: `api_login_required` / `api_session_login_required`
  were originally proposed for simplification to desktop-loopback only. The
  completed implementation did **not** remove the current Flask session or
  `ukg_` ExternalAPIKey paths. Current behavior is documented in
  `docs/AUTH_DECORATORS.md`.
- `api_admin_required` → **alias to `api_login_required`** (no admin vs. non-admin
  distinction when there is one owner). Keep the name as a thin shim so the 16
  `admin_routes` call sites don't churn, or sed-replace them in one pass.
- `require_permission(...)` (from `rbac.py`) → replace with a no-op decorator factory
  that just calls `api_login_required`, then remove once the 3 route files are updated.

This keeps the diff concentrated in **one file** plus ~3 route files, instead of 147 edits.

---

## 3. Phased execution (each phase independently shippable + green)

**Phase A — Remove already-dead modules (zero risk). ✅ DONE 2026-06-13 (`57b912da`).**
Deleted `zero_trust.py` (792 LOC) + `token_manager.py` (390 LOC) and their vanity
tests: removed `tests/security/test_zero_trust_coverage.py` + the `TestZeroTrust`
class/import in `tests/unit/test_core_infrastructure.py`; split
`test_token_and_vulnerability_coverage.py` → token tests dropped,
`vulnerability_scanner` tests preserved in new `test_vulnerability_coverage.py`.
379 security+core-infra tests pass, ruff clean, no remaining references.

**Phase B — Collapse authorization decorators. ✅ DONE 2026-06-13 (`e710aeb3`).**
`api_admin_required` is now an alias of `api_login_required`; `mcp_routes`
execution context grants full owner scopes (was RBAC-derived); de-wired `rbac`
from `admin_routes` (8 `@require_permission`), `privacy_routes`, `mcp_routes`,
`extensions.py` (dead `rbac_manager` singleton), `scan_backend_routes.py`; deleted
`rbac.py` (613 LOC) + `test_rbac_comprehensive.py` + the `TestRBACManager` class.
Migrated 3 tests asserting the obsolete admin-403 model → single-mode 200 (admin
dashboard, `/api/security/scan/recent`, `/api/v1/retention/policies`). 302 security
+ 120 route tests pass; ruff clean.
> **Discovered (pre-existing, NOT Phase B):** 5 failures in
> `tests/integration_routes/test_desktop_auto_login_security.py` — stale
> `monkeypatch.setattr("routes.auth_routes...")` referencing the pre-migration
> `routes` module (now `backend.routes`). Reproduce on clean HEAD. **Fix in Phase C**
> when `auth_routes` is handled (these test the desktop auto-login KEEP path, so fix
> the path — don't delete them).

**Phase C — CORRECTED SCOPE (2026-06-13).** Investigation found the original Phase C
was written from a stale multi-user-web-app model. The live reality: the single-mode
**desktop auth is already built** (`auth_routes.py` = Windows-identity + signed
loopback; `LoginManager`/`current_user` back the owner's session). So the planned
removals (`auth_routes`, `LoginManager`, `session_manager`, API-key branch, the
`check_api_auth` session branch) are all the **keep-path** — NOT removable. The
genuinely-valid Phase C work is:
- ✅ **Fix the 5 `test_desktop_auto_login_security.py` failures** — done (`routes.auth_routes`
  → `backend.routes.auth_routes`; pre-existing, not from this deprecation).
- ✅ **Removed stale `CSRF_API_EXEMPT_PATH_PREFIXES`** entries (`faaf10f7`) for the
  non-existent `/auth/login|register|mfa/verify|callback/sso` routes.
- ⏸ **Gut `admin_routes.py`** — **DEFERRED (entangled).** `frontend/app/admin/page.tsx`
  (268 lines) is a live admin UI that calls `/admin/dashboard` + `/admin/users`, gates
  on `is_admin`, and renders user/role lists. Removing the backend routes is a
  *coordinated frontend+backend feature removal* (also depends on `User.role`/`is_admin`
  dropped in Phase E) — not a backend-only edit. Do as one feature-removal during the
  frontend audit (A15/A16), together with Phase E.

### Entanglement note (discovered 2026-06-13)

Phases A+B removed genuinely-dead/obsolete **active** code (zero_trust, token_manager,
rbac — ~1,800 LOC, clean wins). The remaining vestigial scaffolding is **wired in**,
so each removal is cross-cutting, not a clean delete:
- **admin user-mgmt** ↔ `frontend/app/admin/page.tsx` + `User.role/is_admin`.
- **MFA** (`mfa.py`, `User.mfa_*`, `User.verify_totp`, `extensions.mfa_manager`,
  `privacy_routes` reset) ↔ 3 frontend files (`AuthContext.tsx`, `lib/api/auth.ts`,
  `lib/api/client.ts`).
- **tenant_rls.py** = Postgres **Row-Level Security** wired into app startup
  (`configure_tenant_rls`) + Prometheus metrics (`tenant_rls_prometheus_lines`).
  Moot in single-tenant but provides DB-level defense-in-depth; removal touches
  startup + metrics.

**Implication:** the high-value, low-risk deprecation is done. The rest is
lower-value (the vestigial code is harmless — it works) and higher-risk
(frontend + startup + metrics + DB migration). Recommend doing it as deliberate,
frontend-coordinated changes (or folding into the A15/A16 frontend audit), not a
rushed backend sweep.

**Phase D — Remove MFA + tenancy. ✅ DONE 2026-06-19.**
- MFA: `mfa.py` deleted (`b4c1fa69`); de-wired from `extensions.py`; `User.verify_totp`
  rewired to a direct `pyotp.TOTP` shim (no `MFAManager`). The `mfa_enabled`/`mfa_secret`
  columns + `verify_totp` shim + `privacy_routes` `mfa_enabled = False` remain until the
  Phase E migration drops the columns.
- Tenancy: `tenant_rls.py` removed (`c60f3daf`) — module + `app.py` wiring (import,
  `configure_tenant_rls` startup call, `tenant_rls_prometheus_lines` /metrics emission) +
  `test_tenant_rls_controls.py` + the `tenant_rls_enabled` metric assertion. Was a no-op on
  SQLite desktop and provides no isolation benefit under single-mode.
  **Left in place (wider than RLS, → Phase E+):** `tenant_id` columns on several models and
  `current_user.tenant_id` reads in `node_repository`/`analytics_service`/`ukg_db`/`scope_enforcement`.

**Phase E — Slim the User model (DB migration). 🔶 IN PROGRESS (2026-06-19).**
- ✅ **E-1** (`c60aee15`): MFA columns (`mfa_enabled`/`mfa_secret`/`backup_codes`) dropped +
  `verify_totp` removed + Alembic migration `b4c5d6e7f8a9` (validated upgrade/downgrade/idempotent).
- ✅ **E-2a** (`e2994349`): admin user-mgmt UI + routes removed (`backend/admin.py` deleted;
  `admin_routes.py` slimmed to cache/health; `/dashboard` + `/users/transfer-ownership` gone;
  `frontend/app/admin/page.tsx` + Admin nav links removed). Cleared 13 pre-existing test failures.
- ✅ **E-2b** (`deb6a656`): all ~50 `is_admin` authorization gates collapsed to single-owner via
  `current_user_is_owner()` (`backend/auth/api_decorators.py`) + `_user_is_owner()` (`tracing/api.py`);
  dead `backend/decorators.py` deleted. `role`/`is_admin` columns are now INERT (no gate reads them).
- ✅ **E-2c** (`950eda75`): dropped `role`/`is_admin` columns + indexes (migration `c5d6e7f8a9b0`,
  validated). to_dict/GraphQL return single-mode constants `is_admin:True`/`role:'owner'` so the
  frontend admin-nav contract is unchanged. `conftest.py` keeps role/is_admin params but no longer
  persists them; ~10 test files + 3 scripts updated; 2 obsolete `windows/verify_*` scripts deleted.
  **Phase E (and the whole plan) is complete.** Discovered during E-2c: a severe pre-existing
  `tests/integration_routes` shared-DB isolation bug (A18 scope) — see REPO_AUDIT_LOG / memory.

Original E scope (for E-2c):
Drop `role`, `is_admin`, `mfa_enabled`, `mfa_secret` columns + their indexes
(`ix_users_role`, `ix_users_role_active`). Decide on `password_hash`: with OS-level
auth there is no app password — likely droppable, but confirm nothing seeds an
initial admin via `set_password` first (`scripts/create_admin_user.py`). Alembic
migration + downgrade.

**Phase F — Test migration.**
~29 of 172 test files touch auth/rbac/session/mfa/login. Rewrite the ones asserting
multi-user behavior (login flows, role gating, permission denials) to the single-owner
model; delete tests that only exercised removed modules. This is the largest effort
slice — budget a dedicated pass.

---

## 4. Risks & call-outs

- **Electron contract:** Phase C must preserve the `X-DataLogic-Desktop` +
  `X-Desktop-Auth-*` signed-request headers the Electron shell sends. Verify against
  `frontend/electron/main.ts` request signing before removing the session branch.
- **`password_hash` removal is one-way** (data). Keep it until Phase E is confirmed;
  the werkzeug `scrypt` hashing itself is fine (SC-2) — it's just unused under OS auth.
- **External API keys (`ExternalAPIKey`, `ukg_` keys):** confirm no headless/automation
  consumer depends on them before removing that branch in Phase C. If any does, that
  consumer is itself part of the deprecated multi-user surface.
- **Compliance posture:** `compliance_manager.py` SC-1..SC-5 reference access controls;
  update its "access control" check to describe OS-level auth rather than RBAC.
- **Order matters:** do A→F in sequence; each leaves the suite green. Do not start E
  (migration) until B–D have removed all readers of the dropped columns.

---

## 5. Out of scope (stays live — not auth)
Injection defenses (A5-2 five-layer union), `encryption_manager` (AES-256-GCM,
SC-2), `pii_redaction`, `sanitizer`, `ssrf`, `secret_resolver`, `audit_logger`,
`honeypot` (as a defensive primitive), `data_classification`, `security_headers`,
`api_csrf`, `vulnerability_scanner`. These protect data/input and are independent of
the user model.

---

## 6. Single-mode reconciliation of past audits (done 2026-06-13, before code)

Checked whether the single-mode reframe invalidates earlier audit conclusions.
**Result: bounded.** ~80% of the audit work (truth engine, DSQP, DMRF, simulation
layers, KAs, quad personas, axes, local models) never touches the user model and is
**unaffected**. Exposure is confined to the auth/compliance/routes perimeter:

| Past audit | Finding | Disposition |
|---|---|---|
| **A3** (4 desktop status endpoints secured) | They use `@api_session_login_required` = session **or** signed desktop loopback. The loopback path is what we keep. | ✅ **Stands** — Phase C simplifies the decorator (drops the session branch); the intent (no unauthenticated status endpoints) is preserved. Not a reversal. |
| **Routes RT-2 / RT-5** (added auth to `/suggest`, `/health`) | Added session/admin gating. | ✅ **Stands** — collapses to owner pass-through in Phase B/C. |
| **Routes RT-16** (hardened `transfer-ownership` with `SYSTEM_ADMIN`) | Audited a **now-obsolete feature** — there is no ownership transfer with one OS user. | ⚠️ **Superseded** — the route is removed in Phase C, taking the RT-16 hardening with it. |
| **`admin_routes.py`** (whole file) | 16 routes of user CRUD / role update / ownership / role-gated dashboard. | ⚠️ **Wholesale obsolete** — newly added to Phase C scope above. |
| **Sprint 3 SOC 2 `compliance_manager`** (SC-1..SC-5 = Security/Availability/Processing-Integrity/Confidentiality/Privacy) | SC-1 Security check references access controls/RBAC. (Naming note: this SC-2 = *Availability*, unrelated to the audit plan's encryption "SC-2".) | 🔧 **Minor reframe** — update SC-1's access-control narrative to OS-level auth; encryption/audit/PII/retention criteria stand. |
| All other audits (A1a, A1b, A2/A2-2, A4, A5, A6a/b, A7/A8, A9, Sprint 0) | No user-model surface. | ✅ **Unaffected.** |

**Net:** the only *superseded* conclusions are the ones that hardened multi-user
features (RT-16 + the `admin_routes` surface) — and the deprecation plan already
removes those, so executing the plan IS the reconciliation. One small follow-up:
reword `compliance_manager` SC-1 access-control to OS-auth.

---

*Review this plan, then approve a starting phase. Recommended first step: Phase A
(delete the two already-dead modules) — it is risk-free and shrinks the surface
before the structural phases.*

## Change notes for v1.1.0

1. Added metadata and a current-status banner marking this as a completed historical plan.
2. Added an explicit supersession note for the original decorator proposal so it cannot be mistaken for current auth implementation guidance.
