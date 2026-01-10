# API Documentation v3.0.0

<<<<<<< HEAD
The DataLogicEngine exposes a robust, RESTful API designed for high-concurrency enterprise integration.
=======
The DataLogicEngine exposes a comprehensive RESTful API powered by Flask 3.1 blueprints. These endpoints support the Knowledge Graph, Truth Engine, Tracing, LLM Gateway, MCP, and Compliance operations.
>>>>>>> 181b539dcffebeaad8a7884e5497cb6d1329c507

## 📍 Base URL

**Local Development**: `http://localhost:5000/api/v1`
**Production**: `https://your-domain.com/api/v1`

## 🔐 Authentication & Context

<<<<<<< HEAD
- **Bearer Token**: All endpoints require an `Authorization: Bearer <JWT>` header unless otherwise specified.
- **Tenant Isolation**: The `tenant_id` is automatically extracted from your JWT/SSO session. All operations are strictly scoped to your tenant.
- **Traceability**: All responses include a `X-Correlation-ID` header. Use this ID for debugging and audit reconstruction.
=======
All endpoints (except `/health`) require authentication via one of the following methods:

1. **Session Authentication**: Cookie-based (for frontend proxy)
2. **Bearer Token**: `Authorization: Bearer <jwt-token>` (for external clients)
3. **API Key**: `X-API-Key: <api-key>` (for programmatic access)
4. **SSO/OIDC**: Azure AD/Entra ID integration

## Standard Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "timestamp": "2026-01-09T12:00:00Z"
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
  "timestamp": "2026-01-09T12:00:00Z"
}
```
>>>>>>> 181b539dcffebeaad8a7884e5497cb6d1329c507

---

## Table of Contents

1. [Authentication Routes](#1-authentication-routes-auth)
2. [LLM Gateway Routes](#2-llm-gateway-routes-gateway)
3. [Knowledge Routes](#3-knowledge-routes-knowledge)
4. [Trace Routes](#4-trace-routes-trace)
5. [MCP Routes](#5-mcp-routes-mcp)
6. [Knowledge Algorithm Routes](#6-knowledge-algorithm-routes-ka)
7. [Compliance Routes](#7-compliance-routes-compliance)
8. [Simulation Routes](#8-simulation-routes-simulation)
9. [Admin Routes](#9-admin-routes-admin)
10. [System Routes](#10-system-routes-system)

---

## 1. Authentication Routes (`/auth`)

Manage user authentication and sessions.

### Login

- **POST** `/api/v1/auth/login`
  - Standard username/password login
  - **Body**: `{ "username": "user", "password": "pass" }`
  - **Response**: `{ "success": true, "data": { "user_id": "...", "token": "..." } }`

### Register

- **POST** `/api/v1/auth/register`
  - Create new user account
  - **Body**: `{ "username": "user", "email": "user@example.com", "password": "SecurePass123!" }`
  - **Response**: `{ "success": true, "data": { "user_id": "..." } }`

### SSO Login

- **GET** `/api/v1/auth/login/sso`
  - Initiate OIDC/Azure AD Single Sign-On flow
  - Redirects to SSO provider

### Logout

- **POST** `/api/v1/auth/logout`
  - End current session
  - **Response**: `{ "success": true }`

### Check Session

- **GET** `/api/v1/auth/check`
  - Check current authentication status
  - **Response**: `{ "success": true, "data": { "authenticated": true, "user": {...} } }`

---

## 2. LLM Gateway Routes (`/gateway`)

Universal interface for Large Language Models with UKG context injection. This is the primary **"API In / API Out"** entry point.

### Chat Completion

- **POST** `/api/v1/gateway/chat`
  - Send chat request with automatic UKG context injection
  - **Headers**: `Authorization: Bearer <token>` or `X-API-Key: <key>`
  - **Body**:
    ```json
    {
      "messages": [
        {"role": "user", "content": "What are AI compliance risks in healthcare?"}
      ],
      "model": "gpt-4o",
      "provider": "openai",
      "mode": "ukg",
      "run_ukg_pipeline": true,
      "trace_enabled": true,
      "mcp_tools": ["query_knowledge_graph", "check_compliance"]
    }
    ```
  - **Response**:
    ```json
    {
      "success": true,
      "data": {
        "id": "chatcmpl-123",
        "choices": [{
          "message": {
            "role": "assistant",
            "content": "Based on the UKG analysis (Trace #abc-123)..."
          },
          "finish_reason": "stop"
        }],
        "ukg_trace": {
          "trace_id": "abc-123",
          "steps_executed": 14,
          "confidence": 0.92,
          "data_sources": ["HIPAA KB", "FDA Guidance DB"]
        },
        "usage": {
          "prompt_tokens": 245,
          "completion_tokens": 128,
          "total_tokens": 373
        }
      }
    }
    ```

### Streaming Chat

- **POST** `/api/v1/gateway/stream`
  - Stream chat responses in real-time
  - **Body**: Same as `/chat` endpoint
  - **Response**: Server-Sent Events (SSE) stream
    ```
    data: {"delta": "Based", "trace_id": "abc-123"}
    data: {"delta": " on", "trace_id": "abc-123"}
    data: {"delta": " the", "trace_id": "abc-123"}
    ...
    data: [DONE]
    ```

### List Providers (Admin)

- **GET** `/api/v1/admin/providers`
  - List configured LLM providers
  - **Response**:
    ```json
    {
      "success": true,
      "data": {
        "providers": [
          {
            "provider_id": "openai-1",
            "name": "OpenAI GPT-4",
            "provider_type": "openai",
            "status": "active",
            "rate_limit_rpm": 500,
            "rate_limit_tpm": 150000
          }
        ]
      }
    }
    ```

### Add Provider (Admin)

- **POST** `/api/v1/admin/providers`
  - Add new LLM provider configuration
  - **Body**:
    ```json
    {
      "name": "Azure OpenAI",
      "provider_type": "azure_openai",
      "api_key": "encrypted-key",
      "endpoint": "https://your-resource.openai.azure.com",
      "deployment_name": "gpt-4",
      "rate_limit_rpm": 300
    }
    ```

---

## 3. Knowledge Routes (`/knowledge`)

Manage the Universal Knowledge Graph (nodes, edges, 17-Axis framework entities).

### Sectors

- **GET** `/sectors`
  - List all industry sectors.
- **GET** `/sectors/<code_or_id>`
  - Get details for a specific sector.
- **POST** `/sectors`
  - Create a new sector.
  - _Body_: `{ "sector_code": "TECH", "name": "Technology" }`

### Domains

- **GET** `/domains`
  - List all knowledge domains.
- **GET** `/domains/<code_or_id>`
  - Get details for a specific domain.
- **POST** `/domains`
  - Create a new domain.
  - _Body_: `{ "domain_code": "AI", "name": "Artificial Intelligence", "sector_id": "..." }`

### Knowledge Nodes

- **GET** `/knowledge-nodes`
  - List all knowledge graph nodes.
- **GET** `/knowledge-nodes/<uid>`
  - Get a specific node.
- **POST** `/knowledge-nodes`
  - Create a new node.
  - _Body_: `{ "title": "Transformer Architecture", "content": "...", "content_type": "text" }`

---

## 4. Trace Routes (`/trace`)

Comprehensive execution traceability and observability. Every AI reasoning step is captured with full audit trails.

### List Trace Runs

- **GET** `/api/v1/trace/runs`
  - List recent trace runs with pagination and filtering
  - **Query Parameters**:
    - `status`: Filter by status (`pass`, `fail`, `pending`)
    - `page`: Page number (default: 1)
    - `per_page`: Items per page (default: 20, max: 100)
    - `start_date`: Filter by start date (ISO 8601)
    - `end_date`: Filter by end date (ISO 8601)
  - **Response**:
    ```json
    {
      "success": true,
      "data": {
        "runs": [
          {
            "run_id": "abc-123-def-456",
            "status": "pass",
            "created_at": "2026-01-09T12:00:00Z",
            "completed_at": "2026-01-09T12:00:15Z",
            "duration_seconds": 15.3,
            "scores": {
              "confidence": 0.92,
              "entropy": 0.15,
              "bias_risk": 0.08
            },
            "stages_count": 14,
            "evidence_count": 23
          }
        ],
        "pagination": {
          "page": 1,
          "per_page": 20,
          "total": 156
        }
      }
    }
    ```

### Get Trace Run Details

- **GET** `/api/v1/trace/runs/:run_id`
  - Get comprehensive details for a specific trace run
  - **Response**:
    ```json
    {
      "success": true,
      "data": {
        "run_id": "abc-123",
        "status": "pass",
        "input_message": "What are AI compliance risks?",
        "final_answer": "Based on analysis...",
        "created_at": "2026-01-09T12:00:00Z",
        "completed_at": "2026-01-09T12:00:15Z",
        "scores": {
          "confidence": 0.92,
          "entropy": 0.15,
          "bias_risk": 0.08
        },
        "model_version": "gpt-4o-2024-11-20",
        "policy_pack_version": "v2.5",
        "correlation_id": "req-xyz-789"
      }
    }
    ```

### Get Trace Stages

- **GET** `/api/v1/trace/runs/:run_id/stages`
  - Get execution stages with timing for a trace run
  - **Response**:
    ```json
    {
      "success": true,
      "data": {
        "stages": [
          {
            "stage_id": "stage-1",
            "name": "axis_resolution",
            "status": "completed",
            "started_at": "2026-01-09T12:00:00Z",
            "completed_at": "2026-01-09T12:00:02Z",
            "duration_seconds": 2.1,
            "output_summary": "Resolved to Healthcare/AI/Compliance axes"
          },
          {
            "stage_id": "stage-2",
            "name": "knowledge_retrieval",
            "status": "completed",
            "started_at": "2026-01-09T12:00:02Z",
            "completed_at": "2026-01-09T12:00:08Z",
            "duration_seconds": 6.3,
            "output_summary": "Retrieved 23 relevant knowledge nodes"
          }
        ]
      }
    }
    ```

### Get Trace Evidence

- **GET** `/api/v1/trace/runs/:run_id/evidence`
  - Get all evidence items supporting the trace run
  - **Response**:
    ```json
    {
      "success": true,
      "data": {
        "evidence": [
          {
            "evidence_id": "ev-1",
            "source": {
              "type": "knowledge_graph",
              "uri": "ukg://nodes/hipaa-ai-requirements"
            },
            "snippet": "AI systems in healthcare must...",
            "confidence": 0.95,
            "timestamp": "2026-01-09T12:00:05Z"
          }
        ]
      }
    }
    ```

### Get Trace Claims

- **GET** `/api/v1/trace/runs/:run_id/claims`
  - Get factual claims made during reasoning
  - **Response**:
    ```json
    {
      "success": true,
      "data": {
        "claims": [
          {
            "claim_id": "cl-1",
            "claim_text": "HIPAA requires AI systems to maintain audit logs",
            "confidence": 0.93,
            "evidence_ids": ["ev-1", "ev-2"],
            "verification_status": "verified"
          }
        ]
      }
    }
    ```

### Get Personas Involved

- **GET** `/api/v1/trace/runs/:run_id/personas`
  - Get personas used during reasoning

### Get KA Invocations

- **GET** `/api/v1/trace/runs/:run_id/kas`
  - Get Knowledge Algorithm invocations

### Get Policy Decisions

- **GET** `/api/v1/trace/runs/:run_id/policy`
  - Get policy enforcement decisions

### Export Trace Run

- **POST** `/api/v1/trace/runs/:run_id/export`
  - Export trace run to JSON or CSV
  - **Body**: `{ "format": "json" }`
  - **Response**: Downloadable file

---

## 5. Simulation Routes (`/simulation`)

Control the scenario simulation and reasoning engine.

### Sessions

- **GET** `/simulations`
  - List all active and past simulations for the user.
- **POST** `/simulations`
  - Start a new simulation session.
  - _Body_: `{ "name": "Market Analysis", "parameters": { "query": "Trends in 2026", "depth": 5 } }`

### Execution

- **POST** `/simulations/<uid>/step`
  - Execute the next step in the reasoning chain.
- **POST** `/simulations/<uid>/stop`
  - Halt a running simulation.

---

## 3. LLM Gateway Routes (`/gateway`)

Unified interface for Large Language Models. This is the primary **"API In / API Out"** entry point for external applications.

### Chat Completions

- **POST** `/gateway/chat`
  - **Description**: Proxy request to backend LLM (GPT-4/Claude) with automatic Context Injection.
  - **Headers**: `Authorization: Bearer <your_token>`

#### API In (Request)

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Analyze the impact of interest rates on tech stocks."
    }
  ],
  "model": "gpt-4",
  "run_ukg_pipeline": true,
  "mcp_tools": ["search_financial_data", "simulate_market_impact"]
}
```

#### API Out (Response)

```json
{
  "id": "chatcmpl-123...",
  "object": "chat.completion",
  "created": 1677652288,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Based on the simulation (Trace #XYZ), rising interest rates negatively correlate..."
      },
      "finish_reason": "stop"
    }
  ],
  "ukg_trace": {
    "trace_id": "8a7b9c-...",
    "steps_executed": 14,
    "data_sources": ["Federal Reserve API", "Market History DB"]
  }
}
```

---

## 4. Trace Routes (`/trace`)

Observability and debugging.

- **GET** `/trace/runs`
  - List recent trace runs.
- **GET** `/trace/runs/<id>`
  - Get full execution tree for a specific run.

---

## 5. System Routes

- **GET** `/health`
  - Returns system status (API, Database, Redis).

---

## 6. Knowledge Algorithm Routes (`/ka`)

Execute and manage recursive planning algorithms (KA-56+).

### Algorithms

- **GET** `/ka/algorithms`
  - List available knowledge algorithms.
- **GET** `/ka/algorithms/<ka_id>`
  - Get details of a specific algorithm (inputs, outputs).
- **POST** `/ka/algorithms/<ka_id>/execute`
  - Trigger an algorithm execution.
  - _Body_: `{ "params": { "goal": "Analyze..." } }`

---

## 7. MCP Routes (`/mcp`)

Manage Multi-Agent Coordination Platform resources and tools.

### Servers

- **GET** `/mcp/servers`
  - List connected MCP servers.
- **POST** `/mcp/servers`
  - Connect a new MCP server.

### Tools & Resources

- **GET** `/mcp/servers/<server_id>/tools`
  - List tools provided by a server.
  - Execute an MCP tool.
  - _Body_: `{ "server_name": "...", "tool_name": "...", "arguments": {} }`

---

## 8. Authentication Routes (`/auth`)

Manage user sessions and identity.

- **GET** `/auth/check`
  - Check current session status.
- **POST** `/auth/login`
  - Standard username/password login.
- **GET** `/auth/login/sso`
  - Initiate OIDC/Azure AD Single Sign-On.
- **POST** `/auth/logout`
  - End the current session.

---

## 9. Compliance Routes (`/compliance`)

Enterprise compliance and auditing features.

- **GET** `/compliance/standards`
  - List active compliance standards (SOC2, ISO27001, etc).
- **GET** `/compliance/audit/export?days=30`
  - **Export System Logs**: Returns a CSV file containing all audit events for the specified range.
  - _Permissions_: Admin only.
