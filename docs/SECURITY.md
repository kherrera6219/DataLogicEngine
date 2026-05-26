# Enterprise Security & Compliance

## Purpose

Define security controls, identity/access patterns, data protection measures, and audit/compliance posture for DataLogicEngine.

## Audience

1. Security engineers
2. Platform engineers
3. Compliance and audit stakeholders
4. Incident response operators

## Document control

1. Owner: Security Engineering
2. Last updated: 2026-03-31
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `docs/PRODUCTION_READINESS.md`
2. `docs/OPERATIONAL_RUNBOOKS.md`
3. `docs/SDLC_SSDF_MAPPING.md`
4. `docs/AI_MANAGEMENT_SYSTEM_42001.md`

## 2026-03-31 API Authorization & Fail-Closed Update

The following controls were implemented in this remediation pass:

1. **Simulation object-level authorization**
   - `/api/v1/simulations/<session_id>` read/run/stop operations now scope by authenticated principal and persisted `session_id`.
2. **Principal consistency across session and API-key auth**
   - Updated route handling now uses the authenticated API principal resolved by `api_login_required`, rather than assuming a session-backed `current_user`.
3. **Fail-closed query behavior**
   - `/api/v1/query` now returns `503` when the gateway/provider path cannot serve the request, instead of returning canned content that could be mistaken for a real answer.
4. **Simulation engine fallback removal**
   - The backend simulation engine now raises on gateway failures instead of generating synthetic analysis text.

Verification evidence:

- `python -m pytest -q --no-cov tests/unit/test_simulation_engine_unit.py tests/unit/test_phase1_api_hardening.py`
- `python -m ruff check backend/simulation/simulation_engine.py routes/simulation_routes.py backend/routes/simulation_routes.py routes/api_routes.py tests/unit/test_simulation_engine_unit.py tests/unit/test_phase1_api_hardening.py`

## Overview

DataLogicEngine is designed with a **Security-First** philosophy, incorporating multiple layers of defense to protect sensitive enterprise data and ensure the integrity of AI reasoning.

## 2026-03-24 Security Remediation Update

The following controls were implemented as part of the production-readiness remediation sweep:

1. **Gateway session object authorization hardening**
   - `/api/v1/gateway/sessions/<session_id>/messages` now enforces session ownership by authenticated user/API-key identity.
2. **Replay protection hardening**
   - Request signing nonces now support Redis-backed persistence when `REDIS_URL` is configured, reducing cross-worker replay risk.
3. **Frontend edge hardening**
   - Frontend proxy middleware now fails closed on catastrophic errors (HTTP 503), rather than redirecting to a public page.
4. **Secret hygiene baseline**
   - Compose and sample config were updated to remove tracked static secrets and require environment-based secret injection.
5. **Upload validation hardening**
   - File upload service now validates magic signatures against declared MIME type to reduce spoofing.

---

## Identity & Access Management (IAM)

### 1. Hardened IAM & Authentication

DataLogicEngine implements an "Identity-First" security model:

- **Single Sign-On (SSO)**: Native OIDC (OpenID Connect) for **Azure AD / Microsoft Entra ID**, Okta, and Auth0.
- **Multi-Factor Authentication (MFA)**: Native TOTP support (Google Authenticator, Authy) with cryptographically secure setup and backup codes.
- **Granular RBAC**: Role-Based Access Control with specific permissions (e.g., `user:read`, `user:manage_roles`, `security:read`, `system:config`). The RBAC engine enforces **deny-on-ambiguity**: if a user object lacks a valid `role` attribute or carries an unrecognized role name, the permission check returns `False` and logs a warning — it never silently defaults to a permissive role.
- **Account Protection**:
  - **Lockout Policy**: 5 failed attempts trigger a 30-minute account lockout.
  - **Password Hygiene**: Minimum 12 characters, complexity requirements, and automatic password expiry tracking.
  - **Session Hardening**: Redis-backed session management with rotation, concurrency limits, and strict idle timeouts.

### 2. Multi-Tenancy & Isolation

DataLogicEngine uses a "Hard Isolation" strategy:

- **Tenant Context**: Every database query is scoped by `tenant_id`.
- **Cross-Tenant Safety**: It is physically impossible for a user from Tenant A to query or traverse nodes belonging to Tenant B.
- **Logic Isolation**: Circuit breakers and rate limits can be configured per tenant to prevent "Noisy Neighbor" effects.

---

## Infrastructure & network security

### 1. Rate Limiting & DoS Protection

The `API Gateway` implements multi-tiered rate limiting using **Redis**:

- **Global Limits**: Protects the infrastructure from massive bursts.
- **User/Tenant Quotas**: Ensures fair usage and cost predictability.
- **Endpoint Specific**: Critical reasoning endpoints have tighter limits than static asset routes.

**Current status**: Security remediation in progress. Controls described below should be treated as implemented only when backed by passing tests, deploy checks, and environment validation.
**Version**: 4.1.0
**Last security control review**: 2026-02-08

---

## Production Checklist

### 2. Encryption & Data Protection

- **In Transit**:
  - Forced **Strict TLS 1.3** for all production traffic.
  - **HSTS (HTTP Strict Transport Security)** with preloading support (max-age: 1 year).
  - Hardened security headers: `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- **At Rest**:
  - **Field-Level Encryption**: Sensitive PII (emails, simulation metadata) is encrypted in the database using a **KEK/DEK (Key Encryption Key / Data Encryption Key)** pattern with AES-256-GCM.
  - **Provider Keys**:
    - **Cloud**: LLM API keys are encrypted via Fernet using rotating keys stored in secured environment variables.
    - **Desktop**: LLM API keys are encrypted via **Windows DPAPI**, tying secrets to the local user profile and machine hardware.
- **Database Volumes**: Application databases run on app-owned local/Windows VM storage. Use OS volume encryption and restricted ACLs for those internal data directories; do not move runtime databases to externally hosted database services.

### 3. Session Secret & CSRF Origin Policy

**Session secret (`SESSION_SECRET`)**

- In production (`FLASK_ENV=production`) the app will **refuse to start** (`RuntimeError`) if `SESSION_SECRET` is not set or is not resolvable from the configured vault/env source. This prevents Flask operating with a `None` secret key, which would allow session forgery.
- In development the app generates an ephemeral random secret and logs a warning. Sessions are invalidated on restart. Always set `SESSION_SECRET` in `.env` for persistent developer sessions.
- Generate a production-grade secret with: `python scripts/generate_secrets.py`

**CSRF trusted origins**

- Electron `app://` origins are always trusted (the scheme is not reachable from web browsers).
- Loopback origins (`http://localhost:*`, `http://127.0.0.1:*`) are only included in the trusted set in **non-production** environments. This prevents CSRF bypass via locally-running attacker pages in deployed environments.

---

## Compliance & auditability

### 1. Hash-Chained Audit Logs

The UKG SDK implements a compliance-grade audit store. Every reasoning step (KA execution, LLM call, Policy decision) is recorded in an **append-only, hash-chained** ledger.

- **Tamper Evidence**: Any modification to a previous log entry invalidates the hash chain.
- **Compliance Alignment**: Designed to meet the stringent requirements of **SOC2 Type II** and **HIPAA**.

### 3. AI Safety Fortress (2026 Standard)

We implement a 3-Layer Defense Strategy to protect against generative attacks:

- **Layer 1: The Gatekeeper (Input/Output Middleware)**
  - Blocks structural attacks (Base64, Leetspeak). Base64 detection decodes the token and checks the decoded text against the prohibited phrase list — it does not block all base64-encoded content, only payloads containing injected instructions.
  - Rejects prohibited intent phrases ("Ignore instructions", "DAN mode").
  - Filters output for System Prompt Leakage and PII (email, phone, SSN, credit card patterns).
- **Layer 2: The Watchtower (Context Drift Detection)**
  - Analyzes the trajectory of the last 5 conversation turns.
  - Detects "Crescendo" attacks (Incremental Context Poisoning) by tracking Risk Velocity.
- **Layer 3: The Sieve (RAG Sanitization)**
  - Strips imperative commands from ingested documents to prevent Indirect Prompt Injection.
  - Enforces XML isolation (`<document>`) for trusted data.
- **Layer 4: The Sentinel (L9 Meta-Cognitive Guardrails)**
  - Performs final "Belief Drift" analysis to ensure the solution hasn't strayed from the user's safety constraints.
  - Audits "Persona Agreement" to identify internal model dissent or safety-vs-utility conflicts.
  - Implements a mandatory **FINALIZE/REFINE** gate that defaults to fail-closed (REFINE) on any meta-cognitive uncertainty.
- **Layer 5: KA-61 Adversarial Shield (v2.4.0)**
  - Proactive rejection of "System Override" attempts- **Adversarial Hardening**: Enhanced KA-61 shield with 5-point adversarial check.

## Phase 9: Distributable Installer & Lifecycle [x]

- [x] **Setup.exe (WiX)**: Professional installer UI with programmable installation directory.
- [x] **Silent Dependencies**: Automated MSI delivery of PostgreSQL and Redis.
- [x] **Automated Lifecycle**: Nightly backup task registration and interactive uninstallation.
- [x] **Store Packaging**: Optimized artifacts for Microsoft Store submission.
- [x] **Atomic Rollback**: Ensures clean system state on installation failure.
- [x] **Binary Integrity**: SHA-256 verification of all core application executables.
- [x] **Identity Validation**: SID-anchored local profiles with format validation.

---

### Medium Priority (Complete Within First Month)

### 4. Active Defense Isolation (Supervisor Mode)

The "Supervisor AI" operates on a **strictly isolated infrastructure**:

- **Separate Credentials**: Uses a distinct API Key from the primary model, managed via the **Admin Settings Panel**.
- **Isolation Goal**: Prevents "Starvation Attacks" (DoS) where an attacker exhausts the primary model's quota to disable security checks.

### 2. Traceability (The "Why" Behind the AI)

Every AI response includes a `X-Correlation-ID`. This ID allows auditors to reconstruct the entire "Reasoning Tree":

- What evidence was retrieved?
- Which Knowledge Algorithm processed it?
- What were the confidence scores at each layer?

---

## 🚨 Security Incident Response

Incident reports and vulnerability disclosures should be sent to `security@datalogicengine.com`. We support PGP-encrypted communications for sensitive disclosures.

---

© 2026 DataLogicEngine. Security & Compliance Division.
