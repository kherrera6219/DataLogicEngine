# API Documentation v3.0.0

The DataLogicEngine exposes a robust, comprehensive RESTful API powered by Flask 3.1 blueprints, designed for high-concurrency enterprise integration. These endpoints support the Knowledge Graph, Truth Engine, Tracing, LLM Gateway, MCP, and Compliance operations.

## 📍 Base URL

**Local Development**: `http://localhost:5000/api/v1`
**Production**: `https://your-domain.com/api/v1`

## 🔐 Authentication & Context

All endpoints (except `/health`) require authentication via one of the following methods:

1. **Session Authentication**: Cookie-based (for frontend proxy)
2. **Bearer Token**: `Authorization: Bearer <jwt-token>` (for external clients)
3. **API Key**: `X-API-Key: <api-key>` (for programmatic access)
4. **SSO/OIDC**: Azure AD/Entra ID integration

- **Tenant Isolation**: The `tenant_id` is automatically extracted from your JWT/SSO session. All operations are strictly scoped to your tenant.
- **Traceability**: All responses include a `X-Correlation-ID` header. Use this ID for debugging and audit reconstruction.

## Standard Response Format

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
7. [MCP Routes](#7-mcp-routes-mcp)
8. [Compliance & Regulatory Routes](#8-compliance--regulatory-routes-compliance)
9. [Simulation Routes](#9-simulation-routes-simulation)
10. [Admin & System Routes](#10-admin--system-routes-system)

---

## 1. Authentication Routes (`/auth`)

Manage user authentication, sessions, and identity. Valid for both `/api/v1/auth` and `/api/auth`.

### Login

- **POST** `/login`
  - Standard username/password login.
  - **Body**: `{ "username": "user", "password": "pass" }`
  - **Response**: `{ "success": true, "data": { "token": "...", "user": {...} } }`

### Register

- **POST** `/register`
  - Create new user account with enterprise security policy.
  - **Body**: `{ "username": "user", "email": "user@example.com", "password": "..." }`

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
      "model": "gpt-4o",
      "mode": "ukg",
      "trace_enabled": true
    }
    ```
  - **Response**: Returns assistant message plus `ukg_trace` section containing `trace_id`.

### Streaming Chat

- **POST** `/stream`
  - Server-Sent Events (SSE) stream for real-time response delivery.

---

## 3. Truth Engine Routes (`/truth`)

Control the 5-tier reasoning engine. Prefix: `/api/v1/truth` or `/api/truth`.

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

Execute and manage Knowledge Algorithms (KA-001 to KA-114). Prefix: `/api/ka`.

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

### Get Stages

- **GET** `/runs/<run_id>/stages`
  - Step-by-step breakdown of the execution flow.

---

## 6. Knowledge Graph Routes (`/knowledge`)

Manage Sectors, Domains, and Knowledge Nodes. Prefix: `/api/v1` or `/api`.

### Knowledge Nodes

- **GET** `/knowledge-nodes`
  - List all nodes.
- **POST** `/knowledge-nodes`
  - Create a new node with axis coordinates.

---

## 7. MCP Routes (`/mcp`)

Model Context Protocol management. Prefix: `/api/mcp`.

### List Tools

- **GET** `/servers/<server_id>/tools`
  - List tools exposed by a specific MCP server.

---

## 8. Compliance & Regulatory Routes (`/compliance`)

Enterprise compliance and auditing. Prefix: `/api/v1/compliance`.

### Audit Export

- **GET** `/audit/export?days=30`
  - Export system logs to CSV for compliance audits.

---

## 9. Simulation Routes (`/simulation`)

Scenario simulation and reasoning control. Prefix: `/api/v1/simulation`.

### Start Simulation

- **POST** `/simulations`
  - Create a new simulation session.

---

## 10. Admin & System Routes

### Health Check

- **GET** `/health`
  - System status across API, Database, and Redis.

### Provider Management

- **GET** `/api/admin/providers`
  - List configured LLM providers and their statuses.
