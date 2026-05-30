# API documentation

## Purpose

Provide the source-of-truth API contract guidance for DataLogicEngine REST endpoints and their enterprise integration patterns.

## Audience

1. API consumers and integrators
2. Backend engineers
3. Security and compliance reviewers
4. QA and test engineers

## Document control

1. Owner: API Platform Team
2. Last updated: 2026-05-22
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `docs/openapi.yaml`
2. `docs/ARCHITECTURE.md`
3. `docs/SECURITY.md`
4. `docs/TESTING.md`

The DataLogicEngine exposes a comprehensive REST API powered by Flask 3.1 blueprints. Endpoints support Knowledge Graph, Truth Engine, tracing, LLM gateway, MCP, and compliance operations.

## Base URL

**Primary application API base URL**

- Local development: `http://localhost:5000/api/v1`
- Production: `https://your-domain.com/api/v1`

Some operational namespaces remain intentionally unversioned and are documented below.

## Canonical and legacy route policy

`/api/v1/*` is the canonical application REST surface for new integrations, tests, and documentation.

Representative canonical versioned namespaces:

1. `/api/v1/auth/*`
2. `/api/v1/gateway/*`
3. `/api/v1/truth/*`
4. `/api/v1/persona/*`
5. `/api/v1/pillar/*`
6. `/api/v1/compliance/*`
7. `/api/v1/ka/*`
8. `/api/v1/mcp/*`
9. `/api/v1/simulations/*`
10. `/api/v1/{pillars,sectors,domains,knowledge,nodes,edges}`
11. `/api/v1/trace/*`
12. `/api/v1/ingestion/*`

Canonical unversioned operational namespaces currently remain supported for internal/admin workflows:

1. `/api/admin/*`
2. `/api/contextual/*`
3. `/api/honeycomb/*`
4. `/api/locations*`
5. `/api/methods*`
6. `/api/search/*`
7. `/api/docs`

The following legacy aliases remain active only for transition coverage:

1. `/api/compliance/*` -> `/api/v1/compliance/*`
2. `/api/ka/*` -> `/api/v1/ka/*`
3. `/api/mcp/*` -> `/api/v1/mcp/*`
4. `/api/persona/*` -> `/api/v1/persona/*`
5. `/api/pillar/*` -> `/api/v1/pillar/*`
6. `/api/simulations/*` -> `/api/v1/simulations/*`
7. `/api/truth/*` -> `/api/v1/truth/*`
8. `/api/ukg/*` -> `/api/v1/*`

Legacy alias responses emit transition headers so clients can migrate deterministically:

1. `Deprecation: true`
2. `Sunset: Wed, 30 Sep 2026 00:00:00 GMT`
3. `Link: </api/v1/...>; rel="successor-version"`

## Authentication and context

Most application endpoints require authentication via one of the following methods:

1. **Session Authentication**: Cookie-based (for frontend proxy)
2. **Bearer Token**: `Authorization: Bearer <jwt-token>` (for external clients)
3. **API Key**: `X-API-Key: <api-key>` (for programmatic access)
4. **SSO/OIDC**: Azure AD/Entra ID integration

Unauthenticated operational probes are explicitly limited to `/health`, `/live`, `/ready`, and `/metrics`. Unversioned operational namespaces may still have module-specific auth requirements; use the canonical route family and verify the endpoint contract before integrating.

- **Tenant Isolation**: The `tenant_id` is automatically extracted from your JWT/SSO session. All operations are strictly scoped to your tenant.
- **Traceability**: All responses include a `X-Correlation-ID` header. Use this ID for debugging and audit reconstruction.

## Standard response format

All API responses follow this structure:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2026-01-11T19:35:00Z"
}
```

**Error Response**:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {}
  },
  "timestamp": "2026-01-11T19:35:00Z"
}
```

---

## Table of Contents

1. [Authentication Routes](#1-authentication-routes-auth)
2. [LLM Gateway Routes](#2-llm-gateway-routes-gateway)
3. [Truth Engine Routes](#3-truth-engine-routes-truth)
4. [Knowledge Algorithm Routes](#4-knowledge-algorithm-routes-ka)
5. [Trace Routes](#5-trace-routes-trace)
6. [Knowledge Graph Routes](#6-knowledge-graph-routes-knowledge)
7. [Knowledge Ingestion Routes](#7-knowledge-ingestion-routes-ingestion)
8. [Location Routes](#8-location-routes-locations)
9. [MCP Routes](#9-mcp-routes-mcp)
10. [Compliance & Regulatory Routes](#10-compliance--regulatory-routes-compliance)
11. [Simulation Routes](#11-simulation-routes-simulation)
12. [Admin & System Routes](#12-admin--system-routes-system)

---

## 1. Authentication Routes (`/auth`)

Manage user authentication, sessions, and identity. Primary prefix: `/api/v1/auth`.

### Login

- **POST** `/login`
  - Standard username/password login.
  - **Body**: `{ "username": "user", "password": "pass" }`
  - **Response**: `{ "success": true, "data": { "token": "...", "user": {...} } }`

### Register

- **POST** `/api/v1/auth/register`
  - Create new user account with enterprise security policy.
  - **Body**: `{ "username": "user", "email": "user@example.com", "password": "..." }`
  - **Current UI note**: the local-first frontend route `/register` is intentionally disabled and redirects to `/dashboard`. Use the API route only when a deployment explicitly reopens web self-registration.

### SSO Login

- **GET** `/login/sso`
  - Initiate OIDC/Azure AD Single Sign-On flow.

### Logout

- **POST** `/logout`
  - Terminate current session.

### MFA Setup

- **POST** `/mfa/setup`
  - Initiate MFA setup for the logged-in user.
  - **Returns**: QR code secret, backup codes, and setup URI.

### MFA Confirm

- **POST** `/mfa/confirm`
  - Verify and enable MFA using a TOTP token.
  - **Body**: `{ "token": "123456" }`

### Check Auth

- **GET** `/check`
  - Check current authentication status and MFA verification state.
  - **Response**: `{ "authenticated": true, "user": {...}, "mfa_verified": true }`

---

## 2. LLM Gateway Routes (`/gateway`)

Unified interface for Large Language Models with UKG context injection. Prefix: `/api/v1/gateway`.

### Chat Completion

- **POST** `/chat`
  - Send chat request with automatic UKG context injection.
  - **Body**:
    ```json
    {
      "messages": [{ "role": "user", "content": "..." }],
      "model": "gpt-5.5",
      "mode": "ukg",
      "trace_enabled": true
    }
    ```
  - **Response**: Returns assistant message content, `run_id`, and `audit_trail` links when tracing is enabled.
    ```json
    {
      "response": "...",
      "model": "gpt-5.5",
      "run_id": "00000000-0000-0000-0000-000000000000",
      "audit_trail": {
        "decision_path": "/api/v1/trace/runs/00000000-0000-0000-0000-000000000000",
        "complete_trace_url": "/api/v1/trace/runs/00000000-0000-0000-0000-000000000000/bundle",
        "download_url": "/api/v1/trace/runs/00000000-0000-0000-0000-000000000000/export"
      }
    }
    ```

### Streaming Chat

- **POST** `/stream`
  - Server-Sent Events (SSE) stream for real-time response delivery.

---

## 3. Truth Engine Routes (`/truth`)

Control the 5-tier reasoning engine. Primary prefix: `/api/v1/truth`; legacy alias: `/api/truth` with deprecation headers.

### Create Session

- **POST** `/session`
  - Initialize a new reasoning session.
  - **Body**: `{ "query": "...", "context": {...} }`
  - **Response**: `{ "success": true, "session_id": "...", "tier": "high-stakes" }`

### Process Session

- **POST** `/session/<session_id>/process`
  - Execute reasoning for an existing session.

### Get Metrics & Stats

- **GET** `/metrics`
  - Retrieve real-time metrics for TruthCore, TruthGate, and TruthMemory.

### Get Audit Trail

- **GET** `/session/<session_id>/audit`
  - Retrieve the hash-linked audit trail for a specific session (EU AI Act compliant).

---

## 4. Knowledge Algorithm Routes (`/ka`)

Execute and manage Knowledge Algorithms (KA-001 to KA-116). Primary prefix: `/api/v1/ka`; legacy alias: `/api/ka` with deprecation headers.

### List Algorithms

- **GET** `/algorithms`
  - List all available algorithms with metadata and registration status.

### Execute Algorithm

- **POST** `/algorithms/<ka_id>/execute`
  - Run a specific Knowledge Algorithm.
  - **Body**: `{ "data": {...}, "context": {...} }`

### High-Stakes Workflow

- **POST** `/workflow/high-stakes`
  - Trigger the full 12-step high-stakes refinement workflow.
  - **Body**: `{ "query": "...", "context": {...} }`
  - **Response**: Returns `session_id` and the final refined result.

### Workflow Trace

- **GET** `/trace/<session_id>`
  - Retrieve the detailed execution trace for a workflow session.

---

## 5. Trace Routes (`/trace`)

Comprehensive execution traceability. Prefix: `/api/v1/trace`.

### List Trace Runs

- **GET** `/runs`
  - List recent trace runs with pagination and filtering.

### Get Run Details

- **GET** `/runs/<run_id>`
  - Comprehensive details for a specific run, including scores and timing.

### Get Complete Trace Bundle

- **GET** `/runs/<run_id>/bundle`
  - Aggregate local trace viewer payload containing `run`, `frost_layers`, `evidence_sources`, `claims`, `persona_positions`, `ka_invocations`, coordinate axes, policy decisions, memory events, and summary `metrics`.

### Get Stages

- **GET** `/runs/<run_id>/stages`
  - Step-by-step breakdown of the execution flow.

### Get Trace Subresources

- **GET** `/runs/<run_id>/evidence`
  - Evidence source serializers with viewer aliases such as `source_id`, `title`, `evidence_tier`, `claims_supported`, `layer_retrieved`, and `ka_that_invoked`.
- **GET** `/runs/<run_id>/personas`
  - Persona position serializers with `initial_position`, `critique_of_others`, `final_position`, `synthesis_weight`, and `flagged_conflicts`.
- **GET** `/runs/<run_id>/kas`
  - Knowledge Algorithm invocation records for the run.
- **GET** `/runs/<run_id>/metrics`
  - Duration, token, retrieval, confidence, entropy, and stage-count metrics.
- **POST** `/runs/<run_id>/export`
  - Downloadable JSON trace export for local evidence retention.

---

## 6. Knowledge Graph Routes (`/knowledge`)

Manage Sectors, Domains, and Knowledge Nodes. Canonical routes live under `/api/v1/*`; the legacy alias family remains under `/api/ukg/*` with deprecation headers.

### Knowledge Nodes

- **GET** `/knowledge`
  - List knowledge-node content records.
- **POST** `/knowledge`
  - Create a knowledge-node content record.
- **GET** `/nodes`
  - List graph nodes.
- **POST** `/nodes`
  - Create a graph node.
- **GET** `/edges`
  - List graph edges.
- **POST** `/edges`
  - Create a graph edge.
- **GET** `/pillars`
  - List pillar levels.
- **GET** `/sectors`
  - List sectors.
- **GET** `/domains`
  - List domains.

---

## 7. Knowledge Ingestion Routes (`/ingestion`)

Local-first corpus ingestion. Prefix: `/api/v1/ingestion`.

### Supported Local Types

- **GET** `/supported`
  - Returns supported local file extensions (text and binary formats like `.pdf`, `.docx`) and default ingestion limits for the current build.

### Local File Or Folder Ingestion

- **POST** `/local`
  - Ingest supported local files (text and binary) into chunk-level SQL `KnowledgeGraphNode` rows and Chroma `knowledge_nodes`.
  - **Body**:
    ```json
    {
      "path": "C:\\path\\to\\corpus",
      "recursive": true,
      "chunk_size": 1200,
      "source_label": "Optional corpus label",
      "metadata": {"domain": "policy"}
    }
    ```
  - **Response**: ingestion id, scanned/ingested/rejected file counts, created/indexed chunk counts, rejected-file reasons, chunk source hashes, and manifest path.
  - **Security**: outside desktop mode, paths must stay under `DATALOGIC_INGESTION_ROOT` or the process working directory.

### Async Local Ingestion

- **POST** `/local/async`
  - Starts an ingestion job in a background thread and returns an `ingestion_id` immediately. Supports optional Neo4j sync.
  - **Body**: Same as `/local`, with an additional optional `"sync_neo4j": true` boolean.
  - **Response**: `202 Accepted` with `{"ingestion_id": "...", "status": "running"}`.

### Ingestion Status

- **GET** `/status/<ingestion_id>`
  - Returns the current status of an async ingestion run.
  - **Response**: Status (`running`, `completed`, `failed`), along with the ingestion result and optional Neo4j sync outcome when completed.

### Ingestion History

- **GET** `/history?limit=20`
  - Lists recent manifest-backed local ingestion runs from the app-owned manifest directory.
  - **Response**: recent ingestion result records including source path, scanned/ingested/rejected counts, chunk/index counts, rejected-file reasons, and manifest path.

---

## 8. Location Routes (`/locations`)

Manage geospatial context and hierarchy. Current supported prefix: `/api/locations*`.

### List & Filter Locations
- **GET** `/locations`
  - List and filter locations.
  - **Query Params**:
    - `type`: Filter by location type (e.g., 'office', 'region').
    - `parent_id`: Filter by parent location ID.
    - `search`: Name search.
    - `lat`, `lng`, `radius`: Proximity filtering.

### Get Hierarchy
- **GET** `/locations/hierarchy`
  - Get hierarchical tree structure of locations.
  - **Query Params**: `root_uid` (optional)

### Find Nearest
- **GET** `/locations/nearest`
  - Find locations nearest to coordinates.
  - **Required Params**: `lat`, `lng`
  - **Optional Params**: `radius`, `limit`, `type`

### CRUD Operations
- **POST** `/locations`: Create a new location.
- **GET** `/locations/<uid>`: Get specific location.
- **PUT** `/locations/<uid>`: Update location.

---

## 9. MCP Routes (`/mcp`)

Model Context Protocol management. Primary prefix: `/api/v1/mcp`; legacy alias: `/api/mcp` with deprecation headers.

### List Tools

- **GET** `/servers/<server_id>/tools`
  - List tools exposed by a specific MCP server.

---

## 10. Compliance & Regulatory Routes (`/compliance`)

Enterprise compliance and auditing. Primary prefix: `/api/v1/compliance`; legacy alias: `/api/compliance` with deprecation headers.

### Audit Export

- **GET** `/audit/export?days=30`
  - Export system logs to CSV for compliance audits.

---

## 11. Simulation Routes (`/simulations`)

Scenario simulation and reasoning control. Primary prefix: `/api/v1/simulations`; legacy alias: `/api/simulations` with deprecation headers.

### Start Simulation

- **POST** `/simulations`
  - Create a new simulation session.

---

## 12. Admin & System Routes

Operational/admin namespaces that intentionally remain unversioned in the current contract:

1. `/api/admin/*`
2. `/api/search/*`
3. `/api/contextual/*`
4. `/api/methods*`
5. `/api/honeycomb/*`
6. `/api/locations*`

### Health Check

- **GET** `/health`
  - System status: database connectivity and session secret configuration. Also see `/live` (liveness) and `/ready` (readiness).
- **GET** `/live` — Liveness probe: confirms the process is running.
- **GET** `/ready` — Readiness probe: confirms database is reachable and `SESSION_SECRET` is set.
- **GET** `/metrics` — Prometheus-format metrics (uptime, request counts, database state, LLM latency, tenant RLS).

### Provider Management

- **GET** `/api/admin/providers`
  - List configured LLM providers and their statuses.
