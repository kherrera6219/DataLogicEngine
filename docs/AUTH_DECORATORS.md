# DataLogicEngine — Auth Decorator Policy

Defines the three authentication decorator tiers used across Flask route blueprints.
All new routes must use one of these tiers. Using the wrong tier is a security defect.

---

## Tiers

### Tier 1 — `@api_login_required` ✅ Default for new routes

```python
from backend.auth.api_decorators import api_login_required
```

**Accepts:** Session-based login (Flask-Login) OR desktop bearer token.  
**Use for:** Any authenticated API endpoint reachable from both the web UI and the
Electron desktop app. This is the correct default for all new `backend/routes/` handlers.

**Currently used in:** `ka_routes.py`, `multimodal_routes.py`, `simulation_routes.py`

---

### Tier 2 — `@login_required` (Flask-Login)

```python
from flask_login import login_required
```

**Accepts:** Session-based login only. Desktop bearer tokens are NOT accepted.  
**Use for:** Routes that are explicitly web-session-only — for example, OAuth flows,
browser-redirect handlers, or legacy UI routes in `backend/__init__.py`.

**Currently used in:** `search_routes.py`, `mcp_routes.py`, `settings_routes.py`,
`feature_flag_routes.py`, `admin_routes.py` (partial)

> **Note:** Prefer `@api_login_required` for new routes. `@login_required` here is
> a legacy holdover from before the desktop auth path existed. These will be migrated
> incrementally.

---

### Tier 3 — `@api_session_login_required`

```python
from backend.auth.api_decorators import api_session_login_required
```

**Accepts:** Session-based login only (same as `@login_required` but returns JSON
errors instead of HTML redirects).  
**Use for:** API endpoints where the caller is always a browser session and a JSON
`401` response is preferable to an HTML redirect.

**Currently used in:** `analytics_routes.py`, `gdpr_routes.py`, `ingestion_routes.py`,
`location_routes.py`, `storage_routes.py`, `privacy_routes.py`

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

Last updated: 2026-06-21 (single-mode: RBAC removed; `@api_admin_required` is an alias of `@api_login_required`)
