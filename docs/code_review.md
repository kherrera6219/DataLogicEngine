# Code Review Summary

## Executive Snapshot
- **Highest risks:** predictable session secret defaults, unauthenticated schema creation, CSRF gaps on write endpoints, and global MCP mutation without authorization boundaries.
- **Stability risks:** blocking `asyncio.run` calls inside request handlers and absent payload validation can produce 500s under malformed or concurrent traffic.
- **Deployment gaps:** schema lifecycle is unmanaged (no migrations/health checks), which can break multi-instance rollouts.

## Security and Configuration
- **Secret key fallback is hard-coded.** `app.secret_key` defaults to `"ukg-dev-secret-key-replace-in-production"` when no environment variable is set, which risks predictable session signing in production. Enforce mandatory secrets or fail fast if unset, and prefer loading from a secrets manager. 【F:app.py†L25-L34】
- **Tables are auto-created at import time.** Calling `db.create_all()` during module import runs schema creation on every app startup, bypasses migrations, and can cause race conditions in multi-instance deployments. Move schema management to explicit migration tooling (e.g., Flask-Migrate) and remove implicit creation from runtime. 【F:app.py†L55-L86】
- **Missing CSRF protections on form and JSON POST routes.** Login, registration, simulation management, and MCP APIs rely solely on `login_required`/rate limits without CSRF tokens, leaving authenticated users vulnerable to cross-site request forgery. Add Flask-WTF/CSRF protection or signed nonces on all state-changing endpoints. 【F:app.py†L93-L335】【F:backend/mcp_api.py†L45-L606】
- **MCP endpoints lack authorization scoping.** All MCP server/resource/tool/prompt operations check only for authentication (except a single admin check for `setup-default`), so any logged-in user can manipulate global MCP state. Introduce role-based access control and per-owner scoping on these models. 【F:backend/mcp_api.py†L45-L606】
- **Password policy is only enforced at registration.** Sessions and password updates do not re-validate strength; add shared validation utilities when resetting credentials or rotating secrets. 【F:app.py†L68-L169】

## Reliability and Performance
- **Blocking asyncio usage inside request handlers.** Endpoints call `asyncio.run` inside synchronous Flask routes (e.g., resource read, tool call, prompt get), which spins up a new event loop per request and can deadlock if another loop is running. Refactor to async-compatible handlers or reuse a background loop via `asyncio.get_event_loop()`/task scheduling. 【F:backend/mcp_api.py†L236-L463】
- **Unvalidated request payloads.** Several routes assume JSON bodies and access keys without null checks (`request.get_json()` results used immediately). Missing validation will raise 500s on malformed input; add schema validation and defensive defaults to return 400 responses. 【F:backend/mcp_api.py†L73-L463】
- **No request body size limits or file type checks.** Resource creation routes accept arbitrary `content` bodies; enforce size caps and MIME checks to prevent resource exhaustion or malicious uploads. 【F:backend/mcp_api.py†L73-L236】

## Observability
- **Limited audit logging for sensitive operations.** Authentication, simulation lifecycle changes, and MCP management routes only log generic errors. Add structured audit logs (user ID, IP, action, status) for login attempts, resource/tool access, and configuration changes to support security investigations. 【F:app.py†L93-L390】【F:backend/mcp_api.py†L45-L606】
- **No traceability for background operations.** Async MCP calls and database writes lack correlation IDs; add request IDs and propagate them through logs to support debugging under load. 【F:backend/mcp_api.py†L236-L606】

## Testing and Deployment
- **No automated migrations or health checks referenced.** With implicit schema creation and no migration workflow, deployments risk drift between environments. Introduce migration scripts and pre-flight health endpoints to verify database connectivity and background services before serving traffic. 【F:app.py†L55-L86】【F:backend/mcp_api.py†L45-L606】
- **Lack of automated tests for authentication and MCP flows.** There is no evidence of unit/integration coverage for login, registration, or MCP CRUD flows, increasing risk of regressions during refactors. Add tests that exercise auth flows, rate limits, and MCP CRUD/async execution paths. 

## Recommended Remediation Plan (90-day)
1. **Security foundations (Weeks 1–2):** enforce required secrets, wire CSRF protection, and implement role-based authorization for MCP endpoints.
2. **Platform stability (Weeks 3–5):** replace implicit `db.create_all()` with migrations, refactor `asyncio.run` usage, and add strict request validation/size limits.
3. **Observability and tests (Weeks 6–9):** introduce structured audit logging, correlation IDs, health/readiness probes, and automated tests across auth + MCP flows.
4. **Hardening and rollout (Weeks 10–12):** add password reset/rotation flows with policy enforcement, conduct load testing on async paths, and document operational runbooks.
