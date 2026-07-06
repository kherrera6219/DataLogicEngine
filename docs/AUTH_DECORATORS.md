# DataLogicEngine — Auth Decorator Policy

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.2.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Security Engineering |
| Review cadence | Every 30 days |

Defines the three authentication decorator tiers used across Flask route blueprints.
All new routes must use one of these tiers. Using the wrong tier is a security defect.

---

## Tiers

### Tier 1 — `@api_login_required` ✅ Default for new routes

```python
from backend.auth.api_decorators import api_login_required
```

**Accepts:** Flask-Login session, signed desktop loopback auth, or an `ExternalAPIKey` supplied by `X-API-Key` or bearer-form `ukg_...` token.
**Use for:** Any authenticated API endpoint reachable from both the web UI and the
Electron desktop app. This is the correct default for all new `backend/routes/` handlers.

**Currently used for:** canonical API routes and desktop-compatible route families such as API gateway, compliance, knowledge, KA, MCP tool calls, multimodal, and simulation endpoints.

---

### Tier 2 — `@login_required` (Flask-Login)

```python
from flask_login import login_required
```

**Accepts:** Flask-Login session only. Signed desktop loopback auth and API-key principals are not accepted.
**Use for:** Routes that are explicitly browser-session/HTML-rendered only, such as redirect handlers or legacy UI routes outside JSON API handling.

**Current route status:** no top-level `backend/routes/` route file should use this as the default API protection mechanism. Keep it only for true browser-session/HTML redirect paths outside JSON API handling.

> **Note:** Prefer `@api_login_required` for new routes. `@login_required` here is
> a legacy holdover from before the desktop auth path existed.

---

### Tier 3 — `@api_session_login_required`

```python
from backend.auth.api_decorators import api_session_login_required
```

**Accepts:** Flask-Login session or valid signed desktop loopback auth. It does not accept `ExternalAPIKey` principals.
**Use for:** API endpoints where the caller is session/desktop authenticated and a JSON `401` response is preferable to an HTML redirect.

**Currently used for:** browser-session JSON API endpoints such as analytics, admin telemetry, feature flags, GDPR/privacy/user-data, ingestion, location, MCP inventory/configuration, notifications, search, settings, and storage routes.

---

## Admin / owner-only routes

> **Single-mode note.** The app now runs in **single operating mode with
> OS-level auth** — there is one owner and no multi-user roles. The RBAC layer
> (`backend.security.rbac`, `require_permission`, `Permission`) has been
> **removed** (auth deprecation Phase B). `@api_admin_required` is retained only
> as an **alias of `@api_login_required`** for source compatibility; it grants no
> extra privilege. Do not import `require_permission` — it no longer exists.

For the few endpoints that should be owner-only, gate on the owner helper inside
the handler rather than stacking a privilege decorator:

```python
from backend.auth.api_decorators import api_login_required, current_user_is_owner

@blueprint.route('/admin/action', methods=['POST'])
@api_login_required
def admin_action():
    if not current_user_is_owner():
        return jsonify({"error": "forbidden"}), 403
    ...
```

Under single-mode `current_user_is_owner()` is effectively always true for the
authenticated owner; the check is kept so the gate is explicit and survives any
future re-introduction of multiple identities.

---

## Decision tree for new routes

```
Is the route web-UI-only (browser session, HTML redirect on 401)?
  Yes → @login_required
  No  → Is JSON 401 needed for session-only callers?
          Yes → @api_session_login_required
          No  → @api_login_required  ← DEFAULT
```

## Change notes for v1.2.0

1. Corrected the accepted-auth descriptions to match `backend/auth/api_decorators.py`: `@api_login_required` accepts session, signed desktop loopback auth, and `ExternalAPIKey`; `@api_session_login_required` accepts session or signed desktop auth only.
2. Removed stale OAuth-flow examples from the `@login_required` guidance.

## Change notes for v1.1.0

1. Added document metadata so the policy participates in active docs governance.
2. Updated decorator usage notes against the live `backend/routes/` tree.
3. Clarified that `@login_required` is not the default for JSON API route handlers and that `@api_admin_required` remains a compatibility alias under single-owner mode.
