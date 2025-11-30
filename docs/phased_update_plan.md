# Phased Update Plan for SaaS Readiness

This plan sequences the remediation items from the design review into focused phases. Each phase contains goals, scope, deliverables, and owners can track completion by checking the acceptance criteria.

## Phase 1: Security & Session Foundations (In Progress)
**Goals:** Reduce account takeover and brute-force risk while laying guardrails for authenticated sessions.

**Deliverables**
- Enforce strong password policy during registration (min 12 chars with upper/lower/digit/symbol).
- Harden session cookies (HttpOnly, SameSite=Lax by default, optional Secure flag) and explicit session lifetime controls.
- Add rate limiting to authentication and simulation mutation endpoints with configurable global defaults.
- Document operational knobs for rate limiting and session configuration.

**Status:**
- ✅ Password complexity and validation added to the registration flow.
- ✅ Session cookie hardening and lifetime controls enforced via environment variables.
- ✅ Rate limiting enabled globally with stricter limits on login/register and simulation mutation routes.
- ⏳ Next: Add MFA/Azure AD hooks, audit logging for auth events, and consistent request validation schemas.

## Phase 2: AuthZ, Identity, and Auditability
**Goals:** Establish enterprise-grade access control and traceability.

**Deliverables**
- Role-based access control mapped to protected routes and services.
- MFA/SSO enforcement for privileged roles (Azure AD/OpenID) with session timeout policies.
- Audit log stream for authentication, profile updates, and role changes (structured with correlation IDs).

**Status:** Planned (pending Phase 1 completion).

## Phase 3: API Contracts, Validation, and Testing
**Goals:** Stabilize public interfaces and prevent schema drift.

**Deliverables**
- Marshmallow/Pydantic request/response schemas applied to public APIs and simulation inputs.
- Contract tests for the Flask gateway and UKG services with consistent error handling.
- Rate-limit aware E2E tests for authentication and simulation CRUD paths.

**Status:** Planned.

## Phase 4: Observability, Performance, and Resilience
**Goals:** Make the platform measurable and resilient under load.

**Deliverables**
- Distributed tracing across gateway/core/webhook/model-context services with shared correlation IDs.
- SLOs for login, graph queries, and simulation submissions plus dashboards/alerts.
- Load testing and tuning for rate limits, DB pool size, and webhook/model-context concurrency.

**Status:** Planned.

## Phase 5: UI/UX Consistency and Documentation
**Goals:** Align the user experience with the design system and improve discoverability.

**Deliverables**
- High-fidelity wireframes for login, dashboard, simulation setup, MCP console, and profile flows.
- Component usage guidelines to reconcile Chakra/Fluent/Bootstrap usage and reduce drift.
- Updated onboarding docs and architecture decision records linked from `docs/ARCHITECTURE.md`.

**Status:** Planned.
