# API Documentation

## Document metadata

| Field | Value |
|---|---|
| Document version | v4.3.0 |
| Last updated | 2026-07-14 |
| Status | Active |
| Owner | API Platform Team |
| Review cadence | Every 30 days |

## Purpose

Provide source-of-truth API contract guidance for DataLogicEngine REST
endpoints. This version records the Phase 5 `governed.v1` answer contract, one
backend-owned causal orchestrator, Phase 6 evidence-quality records, and Phase 7
provider manifest, deadline/cancellation, failure, budget, egress-ledger, and
offline-replay contracts.

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
2. LLM Gateway routes that adapt authenticated requests into `governed.v1`.
3. One backend-owned governed orchestrator for DMRF, retrieval, DSQP,
   TruthCore/KA, provider, validation, and trace execution.
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
- Production web deployment: configured deployment origin plus `/api/v1`

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

1. `/api/v1/admin/*`
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
2. **Bearer-form API key**: `Authorization: Bearer ukg_...` for external API-key clients.
3. **API key header**: `X-API-Key: ukg_...` for programmatic access where enabled.
4. **Desktop local auth**: loopback challenge/response and signed desktop requests in local/hybrid desktop mode (the primary single-mode path).

Single-mode / OS-level auth: one owner per machine; the former SSO/OIDC (Azure AD/Entra) and MFA surfaces were removed in the auth deprecation.

Unauthenticated operational probes are explicitly limited to `/health`, `/live`,
`/ready`, and `/api/v1/gateway/health`. `/metrics`, `/health/cache`, and
`/api/v1/system/diagnostics/health` require the desktop/session principal.

Security and runtime context:

- Auth context is extracted from the authenticated session, signed desktop request, or API-key principal where applicable.
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

The implemented AI request lifecycle is:

```text
authenticated prompt
  -> GovernedRequest(governed.v1)
  -> admission/cancellation/mode boundary
  -> DMRF defense + TruthGate + tier + axes
  -> bounded source-identified retrieval
  -> deterministic DSQP + TruthCore/KA preflight
  -> one approved provider request
  -> output/claim/citation/policy validation
  -> transactional trace persistence
  -> GovernedResult or GovernedFailure with stable trace_id
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

Unified governed-answer interface plus provider configuration and diagnostics.
Governance and trace execution are mandatory for accepted answer requests.

Primary prefix: `/api/v1/gateway`.

External applications authenticate with a copy-once DataLogicEngine client key
in `Authorization: Bearer ukg_...` or `X-API-Key`. Desktop owner routes use the
session/CSRF boundary. External keys never authorize `/api/v1/admin/*`, provider
configuration, storage administration, or any direct internal-service access.

The public contract version is `dle-gateway.v1`. Three server-owned virtual
models are published: `dle-standard`, `dle-enhanced`, and `dle-local-review`.
PostgreSQL owns the active policies; a caller cannot disable governance,
validation, trace persistence, or required evidence controls.

### Chat completion

- **POST** `/chat`
  - Send a chat request. The `provider` and `model` fields are optional; when
    omitted the backend selects the active stored provider record. Exactly one
    supported provider/model is selected and there is no cross-provider
    failover.
  - Body:
    ```json
    {
      "messages": [
        {"role": "user", "content": "..."}
      ],
      "virtual_model": "dle-standard",
      "constraints": {},
      "request_id": "client-generated-uuid",
      "idempotency_key": "client-generated-retry-key",
      "meta": {
        "budget_warning_confirmed": false
      }
    }
    ```
    Direct `provider` and `model` overrides require `routing:override` plus exact
    server-owned allowlists; normal clients use virtual models. Supported native
    modes are `standard`, `enhanced`, `local_review`, and `simulation` where the
    selected client policy permits them. The deprecated
    `run_ukg_pipeline` field is accepted for compatibility but cannot bypass
    governance.
  - **200 OK** — successful response:
    ```json
    {
      "success": true,
      "message": "Operation successful",
      "data": {
        "response": "assistant reply text",
        "run_id": "stable-run-uuid",
        "audit_trail": "/api/v1/trace/runs/stable-run-uuid",
        "provider_used": "openai",
        "model_used": "gpt-5.5",
        "contract_version": "governed.v1",
        "status": "completed",
        "trace_summary": [],
        "source_ids": [],
        "claims": [],
        "citations": [],
        "validators": [],
        "confidence_score": null,
        "confidence_measurement": {
          "formula_version": "dle-confidence.v1",
          "value": null,
          "status": "not_measured",
          "components": {},
          "missing_components": ["source_quality"],
          "explanation": "Required evidence-quality inputs were unavailable."
        },
        "convergence": {
          "decision_version": "dle-convergence.v1",
          "action": "finalize",
          "terminal": true
        },
        "warnings": [],
        "failure": null
      },
      "timestamp": "2026-07-13T00:00:00+00:00"
    }
    ```
    `confidence_score` is evidence-support coverage, not correctness
    probability. It is null unless every named `dle-confidence.v1` component is
    measured. Clients must display `confidence_measurement.explanation` and must
    not replace null with a default.
  - **202 Accepted** — a failed request was stored for replay only when the
    queue is enabled and the classified failure is `network`,
    `provider_outage`, or `timeout`:
    ```json
    {
      "queued": true,
      "run_id": "optional-run-uuid"
    }
    ```
  - Typed failures use the following stable HTTP mapping. Non-replayable failures
    are never queued: invalid key `401`, billing suspended `402`, unauthorized
    model or policy block `403`, warning confirmation/cancellation `409`, invalid
    model `422`, quota/rate/hard-budget limit `429`, malformed provider response
    `502`, network/outage `503`, timeout `504`, and persistence/internal failure
    `500`.
  - Example **429 Too Many Requests** — provider is rate-limited and not queued:
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
  - Failure bodies include `contract_version`, `status`, typed `failure`, and
    `run_id` when the request was admitted. Renderers must not infer retry or
    replay from HTTP status alone; use the typed failure contract.

  Implementation: `backend/llm_gateway/api.py` → `gateway_chat()`.

### Streaming chat

- **POST** `/chat/stream`
  - Uses the same governed orchestrator and stable run ID.
  - Emits live typed admission/stage, heartbeat, backpressure, evidence,
    validation, completion, cancellation, and safe-failure events.
  - Provider answer text is withheld until validation succeeds, then emitted as
    `delivery_mode: "validated_output"` chunks. This is not raw provider-token
    streaming.
  - Disconnect cancels the active governed request. Stream resume/replay is not
    supported in v1; streaming rejects idempotency until resume semantics pass.

### Cancellation

- **POST** `/requests/{request_id}/cancel`
  - Requires `run:cancel` for an external client or the desktop owner session.
  - Returns **202** with `CANCELLATION_REQUESTED`, or **404** with
    `REQUEST_NOT_ACTIVE`. The backend finalizes the governed trace as cancelled;
    the renderer cannot extend the server deadline.

### Durable asynchronous runs

- **POST** `/runs` requires `run:create` and `idempotency_key`; returns **202**
  plus status, result, and cancellation URLs.
- **GET** `/runs` and **GET** `/runs/{job_id}` require `run:read` and return only
  jobs owned by that client principal.
- **GET** `/runs/{job_id}/result` returns **202** while execution or required
  object materialization is pending, then the governed result.
- **POST** `/runs/{job_id}/cancel` requires `run:cancel`.
- PostgreSQL owns encrypted requests/job references; Redis owns expiring job
  leases, cancellation, and content-free state. Small encrypted results remain
  in PostgreSQL and large retained encrypted results use the hash-verified
  `gateway-results` S3 bucket.
- Interrupted running work is not automatically replayed because doing so could
  duplicate provider spend.

### Discovery and trace retrieval

- **GET** `/capabilities` requires `models:read` for external clients and returns
  only allowed scopes, profile, and virtual models. Provider credentials are
  never returned.
- **GET** `/health` is authenticated, invokes no provider, and omits provider
  topology from external-client responses.
- **GET** `/traces/{run_id}` requires `trace:read`, verifies ownership through
  the durable gateway audit record, and returns content-safe stage metadata.
  Evidence references require `evidence:read`; snippets are not returned.

### Client-key owner administration

Canonical owner routes are under `/api/v1/admin`:

- **GET/POST** `/api-keys` — list redacted metadata or create a copy-once key;
- **POST** `/api-keys/{key_id}/rotate` — rotate with bounded overlap;
- **POST** `/api-keys/{key_id}/revoke` — immediate revocation and job cancel;
- **POST** `/api-keys/{key_id}/expire` — immediate expiry and job cancel;
- **DELETE** `/api-keys/{key_id}` — destroy verification/policy material only
  after the key is inactive while retaining an audit tombstone;
- **GET** `/api-keys/audit` — redacted lifecycle evidence; and
- **GET** `/gateway/status` — profile, bind, TLS/mTLS, firewall, CORS, and
  required-service state.

Client scopes are explicit: `chat`, `stream`, `run:create`, `run:read`,
`run:cancel`, `trace:read`, `evidence:read`, `models:read`, and the separately
approved `routing:override`. Legacy read permission never grants model execution.
Production rate/day/concurrency enforcement is atomic and Redis-backed; the
gateway fails closed when that required state is unavailable.

### Bounded OpenAI compatibility

- **GET** `/v1/models` and **POST** `/v1/chat/completions` use the unprefixed
  OpenAI path shape but still require a DataLogicEngine client key.
- Only the three governed virtual models, one completion, messages, streaming,
  temperature, one output-token limit, and optional user/session identity are
  supported.
- Unsupported and unknown OpenAI fields are rejected with **422**, never ignored.
- The facade adapts shapes into the native contract and cannot bypass the
  canonical orchestrator. See `docs/GATEWAY_COMPATIBILITY.md`.

### Offline queue

- **GET** `/offline-queue` lists redacted queue metadata.
- **POST** `/offline-queue` accepts a chat payload only with failure class
  `network`, `provider_outage`, or `timeout` and returns **202** after durable
  encrypted storage. Disabled/oversized queues return **409**.
- **DELETE** `/offline-queue/{item_id}` removes one item.
- **POST** `/offline-queue/replay` re-runs current policy and budget checks before
  execution. Auth, validation, policy, persistence, cancellation, and internal
  failures are not replayable.

### Provider usage ledger

- **GET** `/usage-ledger?days=30&session_id=...` returns
  `provider-usage-ledger.v1`, configured limits, remaining allowance, daily and
  monthly totals, pricing status, provider aggregates, and up to 100 recent
  content-free attempt records.
- **GET** `/usage-ledger/export` exports the redacted owner review document.
- **DELETE** `/usage-ledger` is owner/admin-only and requires exact JSON
  confirmation `RESET_PROVIDER_USAGE_LEDGER`.
- The ledger excludes credentials and prompt/response content. Unknown prices
  remain unknown and are still controlled by call/token ceilings.

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
  - On supported Windows desktop builds the key is stored as a DPAPI-protected value. Legacy Fernet values remain readable for migration but all new provider-key writes prefer DPAPI.
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

DMRF is a participating control plane inside the canonical governed
orchestrator. It does not independently own provider execution. The orchestrator
coordinates:

1. injection defense;
2. TruthGate;
3. tier classification;
4. 17-axis routing;
5. bounded retrieval;
6. deterministic DSQP context;
7. TruthCore workflow selection and required KA preflight;
8. one approved provider prompt/call;
9. output/claim/citation/policy validation;
10. transactional executed-stage/evidence/claim persistence.

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
  - Query parameters: `page` (minimum `1`), `per_page` (minimum `1`, maximum `300`), `category`, `status`, `risk_class`, and `layer`.

### Execution history

- **GET** `/history`
  - Return recent persisted KA executions for the tool execution history page.
  - Query parameters: `limit` (minimum `1`, maximum `200`).
  - Response records normalize KA ids/names, risk tier (`read_only`, `write`, `destructive`), UI status (`success`, `failure`, `blocked`), nullable duration/timestamp fields, error text, and trace-run links only when a `run_id` or `trace_run_id` is present in the persisted execution payload.

### Execute algorithm

- **POST** `/algorithms/<ka_id>/execute`
  - Run a specific Knowledge Algorithm.
  - Experimental, presentation-only, and placeholder entries return
    `409 KA_NONPRODUCTION_OPT_IN_REQUIRED` unless the owner explicitly sends
    top-level `allow_nonproduction: true`. They cannot serve as governed
    production validators.
  - Preferred body:
    ```json
    {
      "input": {}
    }
    ```
  - Compatibility body:
    ```json
    {
      "data": {},
      "context": {}
    }
    ```

### Batch execute

- **POST** `/batch`
  - Run up to 20 Knowledge Algorithms with the same input payload.
  - Body:
    ```json
    {
      "algorithms": ["KA-001"],
      "input": {}
    }
    ```
  - The compatibility `data` plus optional `context` payload shape is also accepted.

### Search algorithms

- **GET** `/search?q=<query>`
  - Search algorithm name, short name, purpose, and notes. Query must be at least 2 characters.

### Categories, layers, dependencies, and stats

- **GET** `/categories`
  - List KA categories and their algorithms.
- **GET** `/layers`
  - List simulation layers and associated primary/allowed algorithms.
- **GET** `/dependencies/<ka_id>`
  - List direct KA dependencies and dependents.
- **GET** `/stats`
  - Return counts by category, risk class, status, implementation mode, and math metadata.
- **GET** `/health`
  - Public KA route-layer health check.

### High-stakes workflow

- **POST** `/workflow/high-stakes`
  - Trigger the TruthCore high-stakes refinement workflow where supported by the KA route layer.
  - Body:
    ```json
    {
      "query": "Question or task",
      "context": {}
    }
    ```

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
  - Query parameters: `page` (minimum `1`), `per_page` (minimum `1`, maximum `100`), and optional `status`.
  - Response shape: `{ "runs": [...], "total", "page", "per_page", "pages" }`. Trace row fields such as `created_at`, `ka_id`, provider/model metadata, and scores can be absent or null during partial runs and startup recovery.

### Get run details

- **GET** `/runs/<run_id>`
  - Detailed run metadata, scores, timings, and status.

### Get complete trace bundle

- **GET** `/runs/<run_id>/bundle`
  - Aggregate trace viewer payload containing run, FROST layers, evidence sources, claims, persona positions, KA invocations, coordinate axes, policy decisions, memory events, and summary metrics where available.
  - Consumers must tolerate nullable or missing timestamps, metrics, persona drafts, stage outputs, and coordinate axes while a run is still being assembled or after partial trace persistence.

### Get stages

- **GET** `/runs/<run_id>/stages`
  - Step-by-step execution flow.

### KA execution feed

- **GET** `/ka-execution-feed`
  - Return recent persisted KA execution rows for the Live Trace panel and desktop IPC.
  - Query parameters: `limit` (minimum `1`, maximum `100`).
  - Response shape: `{ "items": [{ "id", "uid", "ka_id", "status", "execution_time_ms", "started_at", "completed_at" }], "limit", "updated_at" }`. The frontend treats this feed as independent of trace-run list state, so KA activity can render even before a trace run exists.

### Get trace subresources

- **GET** `/runs/<run_id>/evidence`
- **GET** `/runs/<run_id>/personas`
- **GET** `/runs/<run_id>/kas`
- **GET** `/runs/<run_id>/axes`
- **GET** `/runs/<run_id>/metrics`

### Export trace

- **POST** `/runs/<run_id>/export`
  - Downloadable JSON trace export for local evidence retention.
  - Export envelopes may include section hashes, bundle hash, optional HMAC signature, optional encrypted payload, and manifest metadata.
  - Request body is optional. `sign_bundle` defaults to `true`; `encrypt_bundle` defaults to `false` and requires the configured export encryption key. The response is streamed as `application/json` with an attachment filename.

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

In the Electron desktop, the renderer cannot submit a filesystem path. The OS
picker returns a single-use expiring capability token; Electron main retains
the canonical path and submits it with a purpose-bound IPC signature. Direct
renderer requests to the path-bearing desktop operation fail closed.

- **POST** `/local`
  - Acquire supported local files/folders into bounded app-owned staging, then
    create durable PostgreSQL job/file/chunk/attempt authority and required
    Neo4j/Chroma/original-object/normalized-object revisions.
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
  - Security: desktop picker authority is preferred. Headless development input
    must be local and within the configured acquisition boundary; UNC/network,
    device/reserved, link/reparse, special-file, traversal, signature mismatch,
    archive/decompression, and parser-budget violations fail closed.

### Async local ingestion

- **POST** `/local/async`
  - Acquire the source before returning, persist the durable job, enqueue a
    content-free Redis coordination record, and return an `ingestion_id`.

### Ingestion status

- **GET** `/status/<ingestion_id>`

### Ingestion history

- **GET** `/history?limit=20`

### Durable lifecycle and reconciliation

- **POST** `/jobs/<ingestion_id>/pause`
- **POST** `/jobs/<ingestion_id>/resume`
- **POST** `/jobs/<ingestion_id>/cancel`
- **POST** `/jobs/<ingestion_id>/retry`
- **POST** `/jobs/<ingestion_id>/repair`
- **POST** `/jobs/<ingestion_id>/delete`
- **GET** `/corpus/consistency`

Status/history responses include per-file parser and defense results, required
original/normalized artifacts, vector/graph/embedding state, expected revision,
last retrieval, and consistency/repair information.

### Owner memory lifecycle (`/api/v1/memory`)

- **GET** `/review?include_working=false`
- **GET** `/export`
- **POST** `/compact`
- **POST** `/recover`
- **DELETE** `/<vertex_id>`

All memory routes require owner/admin authority. Working memory is excluded by
default and is never represented as validated trust.

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
2. connector/server credential and scope configuration.
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
  - Enters `governed.v1` simulation mode and currently returns an explicit
    capability-unavailable result after admission. It does not run retrieval,
    DSQP, KAs, provider, or tools until Phase 10 implements the bounded workflow.

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

- **GET** `/api/v1/admin/providers`
  - List configured LLM providers and their statuses.

---

## 15. Operational health, readiness, and metrics

### Health check

- **GET** `/health`
  - Public-safe status, service name, correlation ID, and timestamp only.
  - Returns `503` when the primary database check fails; configuration and
    service details remain private.
  - Detailed database/configuration state is available only at authenticated
    `GET /api/v1/system/diagnostics/health`.

### Liveness

- **GET** `/live`
  - Confirms only that the process can answer.
  - Returns `status`, `service`, `correlation_id`, and `timestamp`.
  - Liveness does not imply migrations, stores, or required services are ready.

### Readiness

- **GET** `/ready`
  - Confirms runtime phase, primary database, session secret, and every required
    supervised service are ready.
  - Returns `200` with `status: ready`, or `503` with `status: not_ready`, safe
    blocker names/details, correlation ID, and timestamp.

Representative response:

```json
{
  "status": "not_ready",
  "checks": {
    "runtime": "failed",
    "database": "error",
    "secret_key": "set"
  },
  "blockers": ["runtime:failed", "minio", "database"],
  "blocker_details": {
    "runtime:failed": "required_services_not_ready",
    "minio": "service_not_installed",
    "database": "unavailable"
  },
  "correlation_id": "...",
  "timestamp": "..."
}
```

### Authenticated runtime capabilities

- **GET** `/api/v1/system/capabilities`
  - Requires the desktop/session principal.
  - Returns the runtime/installation instance, startup phase, active exclusive
    operation, recent Windows lifecycle events, ready flag, and every supervised
    service.
  - Service state is one of `not_installed`, `stopped`, `starting`, `migrating`,
    `ready`, `degraded`, `failed`, `stopping`, or `blocked`.
  - Each service record can include required flag, safe reason, endpoint,
    expected/observed identity, dependency list, and start/stop budgets.

### Desktop lifecycle events and drain

- **POST** `/api/v1/system/lifecycle/event`
  - Requires an authenticated, signed Electron desktop request; a normal web
    session receives `DESKTOP_LIFECYCLE_AUTH_REQUIRED`.
  - Body: `{ "event": "suspend|hibernate|resume|logoff|shutdown|time_changed|forced_termination" }`.
  - Returns `202` after the runtime accepts the event. Unsupported events return
    `400` with `UNSUPPORTED_LIFECYCLE_EVENT`.
  - Suspend/hibernate enter drain, resume re-probes required services, and
    terminal events stop the runtime.

During startup, drain, migration, backup, restore, update, or shutdown, new
mutation requests return `503` with `RUNTIME_NOT_ACCEPTING_WORK` and the current
runtime phase. Public probes, reads, and the signed lifecycle endpoint remain
available according to their normal authorization contract.

### Metrics

- **GET** `/metrics`
  - Requires desktop/session authentication.
  - Returns Prometheus text for local diagnostics; it is not a public probe.

## Phase 1 public error contract

Public REST, GraphQL, SSE, and IPC-facing failures must use stable messages and
codes. Raw exception strings, provider bodies, credentials, filesystem paths,
and stack traces are not response contracts. The mandatory static and sentinel
gates are recorded in the Phase 1 evidence folder.

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
2. `backend/runtime/` — application phases, service states, installation
   ownership, readiness, drain, and supervision.
3. `backend/dmrf/orchestrator.py` — DMRF control-plane lifecycle.
4. `backend/truth_engine/api.py` — Truth Engine API surface.
5. `backend/truth_engine/truth_gate/gateway.py` — TruthGate behavior.
6. `backend/truth_engine/truth_core/engine.py` — TruthCore sessions and workflows.
7. `backend/truth_engine/truth_memory/manager.py` — audit, artifacts, metrics, explainability.
8. `backend/truth_engine/truth_link/bus.py` — event bus and streaming.
9. `backend/security/desktop_local_auth.py` — local desktop auth.
10. `backend/security/export_integrity.py` — trace export integrity.
11. `backend/storage/` — SQL, graph, vector, object, and memory storage surfaces.
12. `frontend/lib/api/` — frontend API clients and CSRF handling.
13. `tests/contract/` — canonical API contract tests.
14. `.github/workflows/ci.yml` — CI enforcement of contract, parity, security, and readiness gates.

## Change notes for v4.2.0

1. Added the Phase 7 request ID/cancellation, explicit failure-to-HTTP mapping,
   transient-only encrypted replay, buffered SSE label, and local usage-ledger
   contracts.
2. Documented one selected supported provider without silent cross-provider
   failover and server-owned warning/hard-budget behavior.

## Change notes for v4.0.0

1. Documented `governed.v1`, supported modes, non-bypass compatibility behavior,
   stable trace/failure fields, null confidence, and exact chat response shape.
2. Aligned stream, DMRF, and simulation routes with the single canonical
   orchestrator and explicit later-phase boundaries.

## Change notes for v3.4.0

1. Documented the distinct liveness, health, readiness, authenticated
   capabilities, signed lifecycle-event, and runtime-drain response contracts.
2. Added the typed service-state and safe-blocker model used by Electron and
   operational diagnostics.

## Change notes for v3.3.0

1. Added DPAPI provider storage, capability-token ingestion/backup, authenticated diagnostics, and stable public-error rules.
2. Clarified that gateway keys cannot reach owner/admin or secret-management surfaces.

## Change notes for v3.2.0

1. Updated MCP route capabilities to remove stale OAuth token-management wording and align with the live connector registry, credential/scope configuration, analytics, and tool metadata surfaces.
2. Replaced stale JWT bearer guidance with the current session, signed desktop, and `ukg_...` API-key principal model.
3. Updated document metadata for the production top-level documentation review.

## Change notes for v3.1.0

1. Expanded Section 2 (LLM Gateway) with full response contract for `POST /chat`: 200, 202 queued, 429 RATE_LIMITED (Sprint 5f), and 503 responses documented.
2. Added provider key management (`POST /keys`, `GET /keys`) and provider connection test (`POST /providers/{id}/test`) with all error codes and `mapProviderTestError` frontend mapping.
3. Documented that `provider` and `model` are optional in the chat body — backend reads `LLMProvider.model_id` from DB when not supplied (Sprint 5f hardcoded-model removal).
4. Updated document version to v3.1.0 and last-updated date to 2026-06-08.
5. Documentation audit refresh on 2026-07-04: aligned the documented Google model with the live `gemini-3.1-pro-preview` default and refreshed `docs/openapi.yaml` to remove retired login/register auth routes.

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
