# API Documentation

## Document metadata

| Field | Value |
|---|---|
| Document version | v3.1.0 |
| Last updated | 2026-06-08 |
| Status | Active |
| Owner | API Platform Team |
| Review cadence | Every 30 days |

## Purpose

Provide source-of-truth API contract guidance for DataLogicEngine REST endpoints and their enterprise integration patterns. This version reflects the current architecture: local-first runtime modes, canonical `/api/v1/*` routes, DMRF control-plane execution, Truth Engine modules, trace/export integrity, MCP integration, and operational governance surfaces.

## Audience

1. API consumers and integrators
2. Backend engineers
3. Frontend engineers
4. Security and compliance reviewers
5. QA and test engineers
6. Contest or technical reviewers validating the system architecture

## Related documents

1. `docs/openapi.yaml`
2. `docs/ARCHITECTURE.md`
3. `docs/TESTING.md`
4. `docs/PRODUCTION_READINESS.md`
5. `docs/diagrams/12_end_to_end_request_lifecycle.md`
6. `docs/diagrams/09_dmrf_control_plane_deep_dive.md`
7. `docs/diagrams/05_truth_engine_architecture.md`
8. `docs/diagrams/06_local_first_security_model.md`

## API architecture summary

DataLogicEngine exposes a Flask REST API with canonical versioned routes under `/api/v1/*` and selected operational routes that remain intentionally unversioned. The current backend architecture includes these major API-facing systems:

1. Desktop local-auth (Windows identity + signed Electron loopback), session, API key, and CSRF-token flows.
2. LLM Gateway routes for provider-managed model access.
3. DMRF control-plane execution for governed AI reasoning.
4. Truth Engine routes for TruthGate, TruthCore, TruthMemory, and TruthLink operations.
5. Trace routes for run review, trace bundles, evidence, personas, metrics, and exports.
6. Knowledge graph, 17-axis, ingestion, and search routes.
7. MCP routes for connector and server management.
8. Compliance, privacy, GDPR, retention, and admin routes.
9. Health/readiness/metrics routes for operations and CI validation.

## Base URLs

Primary application API base URL:

- Local development: `http://localhost:5000/api/v1`
- Local desktop/Electron runtime: backend loopback API exposed by the desktop app.
- Production web deployment: `https://your-domain.com/api/v1`

Selected operational namespaces remain unversioned, such as `/health`, `/live`, `/ready`, `/metrics`, `/api/docs`, and some admin/internal namespaces.

## Canonical and legacy route policy

`/api/v1/*` is the canonical REST surface for new integrations, tests, and documentation.

Representative canonical versioned namespaces:

1. `/api/v1/auth/*`
2. `/api/v1/gateway/*`
3. `/api/v1/truth/*`
4. `/api/v1/trace/*`
5. `/api/v1/persona/*`
6. `/api/v1/pillar/*`
7. `/api/v1/compliance/*`
8. `/api/v1/ka/*`
9. `/api/v1/mcp/*`
10. `/api/v1/simulations/*`
11. `/api/v1/{pillars,sectors,domains,knowledge,nodes,edges}`
12. `/api/v1/ingestion/*`
13. `/api/v1/gdpr/*`
14. `/api/v1/privacy/*`
15. `/api/v1/retention/*`
16. `/api/v1/storage/*`
17. `/api/v1/analytics/*`

Canonical unversioned operational namespaces currently remain supported for internal/admin workflows:

1. `/api/admin/*`
2. `/api/contextual/*`
3. `/api/honeycomb/*`
4. `/api/locations*`
5. `/api/methods*`
6. `/api/search/*`
7. `/api/docs`
8. `/health`
9. `/live`
10. `/ready`
11. `/metrics`

The following legacy aliases remain active only for transition coverage:

1. `/api/compliance/*` -> `/api/v1/compliance/*`
2. `/api/ka/*` -> `/api/v1/ka/*`
3. `/api/mcp/*` -> `/api/v1/mcp/*`
4. `/api/persona/*` -> `/api/v1/persona/*`
5. `/api/pillar/*` -> `/api/v1/pillar/*`
6. `/api/simulations/*` -> `/api/v1/simulations/*`
7. `/api/truth/*` -> `/api/v1/truth/*`
8. `/api/ukg/*` -> `/api/v1/*`

Legacy alias responses should emit transition headers so clients can migrate deterministically:

1. `Deprecation: true`
2. `Sunset: Wed, 30 Sep 2026 00:00:00 GMT`
3. `Link: </api/v1/...>; rel="successor-version"`

## Authentication and runtime context

Most application endpoints require authentication via one of the following methods:

1. **Session authentication**: Cookie-based frontend sessions.
2. **Bearer token**: `Authorization: Bearer <jwt-token>` for external clients.
3. **API key**: `X-API-Key: <api-key>` for programmatic access where enabled.
4. **Desktop local auth**: loopback challenge/response and signed desktop requests in local/hybrid desktop mode (the primary single-mode path).

Single-mode / OS-level auth: one owner per machine; the former SSO/OIDC (Azure AD/Entra) and MFA surfaces were removed in the auth deprecation.

Unauthenticated operational probes are explicitly limited to `/health`, `/live`, `/ready`, and `/metrics`.

Security and runtime context:

- Auth context is extracted from the authenticated session/JWT where applicable.
- Responses include correlation metadata for debugging and audit reconstruction.
- Desktop local auth is only valid when runtime policy permits local or hybrid mode.
- Cloud mode must not rely on desktop loopback trust.
- CSRF, origin, CORS, trusted-host, session, and rate-limit controls are enforced in the backend envelope.

## Standard response format

Most JSON API responses follow this structure or a module-specific extension of it:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2026-05-30T00:00:00Z",
  "correlation_id": "optional-correlation-id"
}
```

Error response:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {}
  },
  "timestamp": "2026-05-30T00:00:00Z",
  "correlation_id": "optional-correlation-id"
}
```

## End-to-end AI request lifecycle

The current AI request lifecycle is:

```text
frontend prompt
  -> API client + CSRF/session handling
  -> Flask API/security envelope
  -> DMRF injection defense
  -> TruthGate
  -> tier classification
  -> 17-axis routing
  -> DSQP persona construction
  -> TruthCore workflow planning/execution
  -> LLM Gateway or MCP/tool execution where needed
  -> evidence freshness and convergence policy
  -> TruthMemory / UnifiedMemory persistence
  -> TruthLink event publication
  -> trace/run review
  -> optional integrity-protected export
```

See `docs/diagrams/12_end_to_end_request_lifecycle.md` for the full lifecycle diagram.

---

## Table of contents

1. [Authentication Routes](#1-authentication-routes-auth)
2. [LLM Gateway Routes](#2-llm-gateway-routes-gateway)
3. [DMRF Control-Plane Routes](#3-dmrf-control-plane-routes)
4. [Truth Engine Routes](#4-truth-engine-routes-truth)
5. [Knowledge Algorithm Routes](#5-knowledge-algorithm-routes-ka)
6. [Trace Routes](#6-trace-routes-trace)
7. [Knowledge Graph Routes](#7-knowledge-graph-routes-knowledge)
8. [Knowledge Ingestion Routes](#8-knowledge-ingestion-routes-ingestion)
9. [Location Routes](#9-location-routes-locations)
10. [MCP Routes](#10-mcp-routes-mcp)
11. [Compliance, Privacy, GDPR, and Retention Routes](#11-compliance-privacy-gdpr-and-retention-routes)
12. [Simulation Routes](#12-simulation-routes-simulations)
13. [Admin and System Routes](#13-admin-and-system-routes)
14. [Operational Health, Readiness, and Metrics](#14-operational-health-readiness-and-metrics)
15. [Trace Export Integrity](#15-trace-export-integrity)
16. [Reviewer verification path](#16-reviewer-verification-path)

---

## 1. Authentication Routes (`/auth`)

Establish and check the single owner's session via Windows identity and signed
Electron loopback. The app runs in **single operating mode with OS-level auth**:
whoever has OS access to the machine is the owner. Multi-user web-app auth
patterns (username/password login, registration, MFA, SSO) have been removed —
see `backend/routes/auth_routes.py` and the memory of the single-mode architecture.

Primary prefix: `/api/v1/auth`.

### Check auth

- **GET** `/check`
  - Return the current authentication status for the owner session.

### CSRF token

- **GET** `/csrf-token`
  - Issue (or return) the API CSRF token for state-changing requests.

### Desktop challenge / auto-login

- **POST** `/desktop/challenge`
  - Issue a one-time nonce challenge for the desktop local-auth handshake
    (loopback + Windows desktop host only).
- **POST** `/desktop/auto-login`
  - Complete the signed handshake (per-install secret + HMAC over the nonce,
    timestamp-skew checked) and establish the owner's Flask-Login session.

### Desktop local auth

Desktop auth is a local/hybrid runtime capability, not a public cloud trust mechanism. It uses a per-install secret, one-time nonce challenge, HMAC signatures, timestamp skew checks, and loopback/Electron runtime policy.

Relevant implementation:

- `backend/security/desktop_local_auth.py`
- `frontend/contexts/AuthContext.tsx`
- `frontend/lib/runtime/policy.ts`

---

## 2. LLM Gateway Routes (`/gateway`)

Unified interface for model/provider calls with governance, telemetry, provider configuration, and optional UKG/trace integration.

Primary prefix: `/api/v1/gateway`.

### Chat completion

- **POST** `/chat`
  - Send a chat request. The `provider` and `model` fields are **optional** — when omitted the backend reads the configured `LLMProvider.model_id` from the database.
  - Body:
    ```json
    {
      "messages": [
        {"role": "user", "content": "..."}
      ],
      "run_ukg_pipeline": false,
      "mode": "ukg",
      "provider": "openai",
      "model": "gpt-5.5"
    }
    ```
    `provider` and `model` may be omitted; the backend falls back to the stored provider record.
  - **200 OK** — successful response:
    ```json
    {
      "response": "assistant reply text",
      "run_id": "optional-run-uuid",
      "provider_used": "openai",
      "model_used": "gpt-5.5"
    }
    ```
    `provider_used` / `model_used` report the user-selected cloud model that served the request (OpenAI `gpt-5.5` or Google `gemini-3.5-flash`).
  - **202 Accepted** — request queued to the offline replay queue (only when `OFFLINE_QUEUE_ENABLED=true` and all providers are unavailable):
    ```json
    {
      "queued": true,
      "run_id": "optional-run-uuid"
    }
    ```
  - **429 Too Many Requests** — provider is rate-limited; the request was NOT queued (Sprint 5f):
    ```json
    {
      "error": "Provider rate limited — please wait a moment and try again.",
      "code": "RATE_LIMITED",
      "run_id": null,
      "provider_used": null,
      "model_used": null
    }
    ```
    The frontend displays a "rate limited" message and does not retry automatically.
  - **503 Service Unavailable** — all providers failed and offline queue is disabled.

  Implementation: `backend/llm_gateway/api.py` → `gateway_chat()`.

### Streaming chat

- **POST** `/stream`
  - Server-Sent Events or streaming response path where supported by the gateway.

### Provider key management

- **POST** `/keys`
  - Save (or update) an API key for a provider. Creates or updates the `llm_provider` record.
  - Body:
    ```json
    {
      "provider": "openai",
      "key": "sk-...",
      "model": "gpt-5.5"
    }
    ```
  - The key is stored Fernet-encrypted using a key derived from `SESSION_SECRET`. The session secret is stable across restarts in the packaged app.
  - **200 OK** — key saved.
  - **400 Bad Request** — missing provider or key.

- **GET** `/keys`
  - List configured providers (key values are never returned, only metadata).

### Provider connection test

- **POST** `/providers/{provider_id}/test`
  - Test connectivity for a stored provider configuration.
  - **200 OK** — provider connected; may include latency metadata.
  - **401 Unauthorized** — invalid or expired API key (does NOT trigger session expiry redirect in the frontend).
  - **422 Unprocessable** — key format invalid.
  - **429 Too Many Requests** — provider rate-limited.
  - **504 Gateway Timeout** — provider did not respond in time.

  Implementation: `backend/llm_gateway/api.py`. Frontend: `frontend/components/settings/ApiOverlayConfig.tsx` → `mapProviderTestError()` maps these codes to human-readable toast messages.

---

## 3. DMRF Control-Plane Routes

DMRF is the governed AI reasoning control plane. It is not merely a model wrapper. It coordinates:

1. injection defense;
2. TruthGate;
3. tier classification;
4. 17-axis routing;
5. DSQP persona construction;
6. TruthCore workflow planning;
7. evidence freshness scoring;
8. convergence/refinement policy;
9. TruthMemory persistence;
10. MLflow-style tracking;
11. TruthLink publication;
12. observability.

Primary implementation:

- `backend/dmrf/orchestrator.py`
- `backend/dmrf/models.py`
- `backend/dmrf/router.py`
- `backend/dmrf/tier_classifier.py`
- `backend/dmrf/truth_integration/`

DMRF may be invoked through chat/system routes, gateway-integrated flows, or internal service calls depending on deployment wiring. See `docs/diagrams/09_dmrf_control_plane_deep_dive.md`.

---

## 4. Truth Engine Routes (`/truth`)

Control and inspect the Truth Engine subsystem.

Primary prefix: `/api/v1/truth`.
Legacy alias: `/api/truth` with deprecation headers.

Truth Engine modules:

1. **TruthGate** — security, budget, priority, compliance, and trust entry gate.
2. **TruthCore** — tiered reasoning workflow engine.
3. **TruthMemory** — audit, cache, artifacts, metrics, explainability, and MLflow-style tracking.
4. **TruthLink** — event bus, priority queue, optional Redis streams, SSE, and dead-letter handling.

### Health

- **GET** `/health`
  - Truth Engine component initialization state and subsystem health.

### Create session

- **POST** `/core/session`
  - Create a TruthCore processing session after TruthGate evaluation.
  - Body:
    ```json
    {
      "query": "...",
      "context": {},
      "user_id": "optional-user-id",
      "tenant_id": "optional-tenant-id"
    }
    ```

### Process session

- **POST** `/core/session/<session_id>/process`
  - Process a TruthCore session through the selected workflow steps.

### Get session

- **GET** `/core/session/<session_id>`
  - Read session status and result metadata.

### Tiers

- **GET** `/core/tiers`
  - Retrieve available TruthCore tier information.

### Gate evaluation

- **POST** `/gate/evaluate`
  - Run a direct TruthGate evaluation.

### Gate stats and budget

- **GET** `/gate/stats`
- **GET** `/gate/budget/<tenant_id>`

### Memory and explainability

- **GET** `/memory/session/<session_id>`
- **GET** `/memory/artifacts/<session_id>`
- **POST** `/memory/artifacts/<session_id>`
- **GET** `/memory/explain/<session_id>`
- **GET** `/memory/stats`
- **GET** `/memory/metrics/<metric_name>`

### TruthLink

- **POST** `/link/publish`
- **GET** `/link/stats`
- **GET** `/link/pending`
- **GET** `/link/dead-letter`
- **GET** `/link/stream/<client_id>`

### Compliance report and audit

- **GET** `/compliance/report`
- **GET** `/compliance/audit/<session_id>`

---

## 5. Knowledge Algorithm Routes (`/ka`)

Execute and manage Knowledge Algorithms.

Primary prefix: `/api/v1/ka`.
Legacy alias: `/api/ka` with deprecation headers.

### List algorithms

- **GET** `/algorithms`
  - List available algorithms with metadata and registration status.

### Execute algorithm

- **POST** `/algorithms/<ka_id>/execute`
  - Run a specific Knowledge Algorithm.
  - Body:
    ```json
    {
      "data": {},
      "context": {}
    }
    ```

### High-stakes workflow

- **POST** `/workflow/high-stakes`
  - Trigger the high-stakes refinement workflow where supported by the KA route layer.

### Workflow trace

- **GET** `/trace/<session_id>`
  - Retrieve execution trace for a KA workflow session where available.

---

## 6. Trace Routes (`/trace`)

Comprehensive execution traceability.

Primary prefix: `/api/v1/trace`.

### List trace runs

- **GET** `/runs`
  - List recent trace runs with pagination and filtering.

### Get run details

- **GET** `/runs/<run_id>`
  - Detailed run metadata, scores, timings, and status.

### Get complete trace bundle

- **GET** `/runs/<run_id>/bundle`
  - Aggregate trace viewer payload containing run, FROST layers, evidence sources, claims, persona positions, KA invocations, coordinate axes, policy decisions, memory events, and summary metrics where available.

### Get stages

- **GET** `/runs/<run_id>/stages`
  - Step-by-step execution flow.

### Get trace subresources

- **GET** `/runs/<run_id>/evidence`
- **GET** `/runs/<run_id>/personas`
- **GET** `/runs/<run_id>/kas`
- **GET** `/runs/<run_id>/metrics`

### Export trace

- **POST** `/runs/<run_id>/export`
  - Downloadable JSON trace export for local evidence retention.
  - Export envelopes may include section hashes, bundle hash, optional HMAC signature, optional encrypted payload, and manifest metadata.

---

## 7. Knowledge Graph Routes (`/knowledge`)

Manage sectors, domains, pillars, graph nodes, graph edges, and knowledge-node content.

Canonical routes live under `/api/v1/*`; the legacy alias family remains under `/api/ukg/*` with deprecation headers.

Representative routes:

- **GET** `/knowledge`
- **POST** `/knowledge`
- **GET** `/nodes`
- **POST** `/nodes`
- **GET** `/edges`
- **POST** `/edges`
- **GET** `/pillars`
- **GET** `/sectors`
- **GET** `/domains`

Current architecture note:

- Durable graph records can live in SQL.
- Neo4j is used for graph-store operations where configured.
- `backend/storage/uskd_memory_graph.py` provides a RAM-resident NetworkX graph for reasoning-layer traversal.
- 17-axis routing is implemented under `core/axes/` and `backend/dmrf/router.py`.

---

## 8. Knowledge Ingestion Routes (`/ingestion`)

Local-first corpus ingestion.

Primary prefix: `/api/v1/ingestion`.

### Supported local types

- **GET** `/supported`
  - Return supported file extensions and ingestion limits.

### Local file or folder ingestion

- **POST** `/local`
  - Ingest supported local files into chunk-level SQL `KnowledgeGraphNode` records and Chroma `knowledge_nodes` vectors where configured.
  - Body:
    ```json
    {
      "path": "C:\\path\\to\\corpus",
      "recursive": true,
      "chunk_size": 1200,
      "source_label": "Optional corpus label",
      "metadata": {"domain": "policy"}
    }
    ```
  - Security: outside desktop mode, paths must remain under `DATALOGIC_INGESTION_ROOT` or the process working directory.

### Async local ingestion

- **POST** `/local/async`
  - Start ingestion in a background thread and return an `ingestion_id`.

### Ingestion status

- **GET** `/status/<ingestion_id>`

### Ingestion history

- **GET** `/history?limit=20`

---

## 9. Location Routes (`/locations`)

Manage geospatial context and hierarchy.

Current supported prefix: `/api/locations*`.

Representative routes:

- **GET** `/locations`
- **GET** `/locations/hierarchy`
- **GET** `/locations/nearest`
- **POST** `/locations`
- **GET** `/locations/<uid>`
- **PUT** `/locations/<uid>`

---

## 10. MCP Routes (`/mcp`)

Model Context Protocol management.

Primary prefix: `/api/v1/mcp`.
Legacy alias: `/api/mcp` with deprecation headers.

Representative capabilities:

1. MCP connector registry.
2. OAuth token management.
3. MCP server configuration.
4. MCP analytics per connector/server.
5. Tool listing and execution metadata.

Representative route:

- **GET** `/servers/<server_id>/tools`
  - List tools exposed by a specific MCP server.

---

## 11. Compliance, Privacy, GDPR, and Retention Routes

Primary prefixes include:

1. `/api/v1/compliance/*`
2. `/api/v1/gdpr/*`
3. `/api/v1/privacy/*`
4. `/api/v1/retention/*`

Legacy alias:

- `/api/compliance/*` -> `/api/v1/compliance/*`

Representative capabilities:

- audit export;
- privacy settings;
- GDPR request handling;
- retention policy management;
- compliance status surfaces;
- audit log extraction.

Representative route:

- **GET** `/audit/export?days=30`
  - Export system logs for compliance review where enabled.

---

## 12. Simulation Routes (`/simulations`)

Scenario simulation and reasoning control.

Primary prefix: `/api/v1/simulations`.
Legacy alias: `/api/simulations` with deprecation headers.

Representative routes:

- **POST** `/simulations`
  - Create a new simulation session.
- **GET** `/simulations`
  - List simulation sessions where enabled.
- **POST** `/simulation/run`
  - Run a simulation path where supported by canonical route wiring.

---

## 13. User Preference Routes

Per-user preferences stored in the database (one row per user).

### Notification preferences

Prefix: `/api/v1/user/notifications`

- **GET** `/api/v1/user/notifications`
  - Returns the current user's notification preferences. Creates a default row
    on first access. Authentication required.
  - Response: `{ "success": true, "preferences": { ... } }`

- **POST** `/api/v1/user/notifications`
  - Updates one or more notification preferences. Unknown keys are ignored.
    Authentication required.
  - Body (all fields optional):

    ```json
    {
      "email_on_run_complete": true,
      "email_on_run_failed": true,
      "email_on_simulation_complete": false,
      "inapp_run_complete": true,
      "inapp_run_failed": true,
      "inapp_simulation_complete": true,
      "inapp_system_alerts": true,
      "digest_frequency": "none"
    }
    ```

  - `digest_frequency` must be one of `none`, `daily`, or `weekly` — returns 400 otherwise.
  - Boolean fields must be `true`/`false` (not strings) — returns 400 otherwise.
  - Response: `{ "success": true, "preferences": { ... } }` with updated values.

---

## 14. Admin and System Routes

Operational/admin namespaces:

1. `/api/v1/admin/*`
2. `/api/search/*`
3. `/api/contextual/*`
4. `/api/methods*`
5. `/api/honeycomb/*`
6. `/api/v1/locations/*` (migrated from `/api/locations*` in Sprint 4)

Representative admin capabilities (single owner — no multi-user/role management
under single-mode OS-level auth):

- provider configuration;
- operational admin (cache clear, admin health);
- compliance dashboard;
- MCP server management;
- audit export;
- system configuration and status.

Representative route:

- **GET** `/api/admin/providers`
  - List configured LLM providers and their statuses.

---

## 15. Operational health, readiness, and metrics

### Health check

- **GET** `/health`
  - System status such as database connectivity and session secret configuration.

### Liveness

- **GET** `/live`
  - Confirms the process is running.

### Readiness

- **GET** `/ready`
  - Confirms required startup dependencies are ready.

### Metrics

- **GET** `/metrics`
  - Prometheus-format metrics including uptime, request counters, database state, LLM latency, and DMRF observability where available.

---

## 16. Trace export integrity

Trace exports are protected by `backend/security/export_integrity.py`.

Export document structure:

```json
{
  "manifest": {
    "exported_at": "2026-05-30T00:00:00Z",
    "exported_by": "user-or-system",
    "version": "1.1",
    "hash_algorithm": "sha256",
    "bundle_hash": "...",
    "section_hashes": {},
    "signature_algorithm": "hmac-sha256-or-none",
    "encrypted": false
  },
  "bundle": {}
}
```

Optional encrypted exports return `payload_encrypted` and an envelope hash/signature.

---

## 17. Reviewer verification path

A technical reviewer should validate this document against these files:

1. `app.py` — route registration, middleware, health, metrics, security envelope.
2. `backend/dmrf/orchestrator.py` — DMRF control-plane lifecycle.
3. `backend/truth_engine/api.py` — Truth Engine API surface.
4. `backend/truth_engine/truth_gate/gateway.py` — TruthGate behavior.
5. `backend/truth_engine/truth_core/engine.py` — TruthCore sessions and workflows.
6. `backend/truth_engine/truth_memory/manager.py` — audit, artifacts, metrics, explainability.
7. `backend/truth_engine/truth_link/bus.py` — event bus and streaming.
8. `backend/security/desktop_local_auth.py` — local desktop auth.
9. `backend/security/export_integrity.py` — trace export integrity.
10. `backend/storage/` — SQL, graph, vector, object, and memory storage surfaces.
11. `frontend/lib/api/` — frontend API clients and CSRF handling.
12. `tests/contract/` — canonical API contract tests.
13. `.github/workflows/ci.yml` — CI enforcement of contract, parity, security, and readiness gates.

## Change notes for v3.1.0

1. Expanded Section 2 (LLM Gateway) with full response contract for `POST /chat`: 200, 202 queued, 429 RATE_LIMITED (Sprint 5f), and 503 responses documented.
2. Added provider key management (`POST /keys`, `GET /keys`) and provider connection test (`POST /providers/{id}/test`) with all error codes and `mapProviderTestError` frontend mapping.
3. Documented that `provider` and `model` are optional in the chat body — backend reads `LLMProvider.model_id` from DB when not supplied (Sprint 5f hardcoded-model removal).
4. Updated document version to v3.1.0 and last-updated date to 2026-06-08.

## Change notes for v3.0.0

1. Added Section 13 — User Preference Routes — documenting `GET` and `POST`
   `/api/v1/user/notifications` with request/response shapes and validation rules.
2. Updated Section 14 (formerly 13) Admin and System Routes: corrected
   `/api/locations*` → `/api/v1/locations/*` to reflect the Sprint 4 URL prefix
   migration; corrected `/api/admin/*` → `/api/v1/admin/*`.
3. Renumbered Sections 14→15 (health), 15→16 (trace export), 16→17 (reviewer path).
4. Updated document version to v3.0.0 and last-updated date.

## Change notes for v2.6.0

1. Added explicit document metadata table with version and update date.
2. Updated API architecture summary for current DMRF, Truth Engine, local-first, trace/export, and MCP architecture.
3. Added DMRF control-plane section.
4. Updated Truth Engine section to reflect TruthGate, TruthCore, TruthMemory, and TruthLink route families.
5. Updated trace export integrity section.
6. Added reviewer verification path tied to actual implementation files.
7. Reframed stale wrapper-style language to current governed reasoning lifecycle.
