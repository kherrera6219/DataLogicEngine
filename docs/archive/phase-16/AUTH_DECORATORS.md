# DataLogicEngine — Auth Decorator Policy

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.3.0 |
| Last updated | 2026-07-13 |
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
**Use for:** An authenticated data-plane endpoint that intentionally accepts an
external API-key principal as well as the desktop/session principal. It must not
be used for owner configuration, lifecycle, secret, backup, or administrative
operations.

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

The app has one local Windows owner. `@api_admin_required` now enforces the
owner trust boundary by accepting only a valid desktop principal or owner
session. It deliberately rejects `ExternalAPIKey` principals.

```python
from backend.auth.api_decorators import api_admin_required

@blueprint.route('/admin/action', methods=['POST'])
@api_admin_required
def admin_action():
    ...
```

Use this decorator for governance configuration, service lifecycle, destructive
storage, policy changes, MCP configuration, provider credentials, backups,
restores, and sensitive exports.

---

## Decision tree for new routes

```
Is the route HTML/redirect-only?
  Yes → @login_required
  No  → Is it owner/control-plane or secret-bearing?
          Yes → @api_admin_required
          No  → May an ExternalAPIKey call it by contract?
                  Yes → @api_login_required
                  No  → @api_session_login_required
```

## Phase 1 boundary rules

- Gateway keys never become the desktop owner.
- Signed desktop requests use timestamped HMAC plus a one-time request nonce.
- Session mutations require trusted Origin and CSRF validation where enabled.
- GraphQL context and MCP identity/scope context are built from the authenticated
  server principal; caller-supplied identity fields are rejected.

## Change notes for v1.3.0

1. Made `@api_admin_required` a real owner-session/desktop boundary that excludes external API keys.
2. Added the Phase 1 route-selection decision tree and replay/context rules.

## Change notes for v1.2.0

1. Corrected the accepted-auth descriptions to match `backend/auth/api_decorators.py`: `@api_login_required` accepts session, signed desktop loopback auth, and `ExternalAPIKey`; `@api_session_login_required` accepts session or signed desktop auth only.
2. Removed stale OAuth-flow examples from the `@login_required` guidance.

## Change notes for v1.1.0

1. Added document metadata so the policy participates in active docs governance.
2. Updated decorator usage notes against the live `backend/routes/` tree.
3. Clarified that `@login_required` is not the default for JSON API route handlers and that `@api_admin_required` remains a compatibility alias under single-owner mode.
