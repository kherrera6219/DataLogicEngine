# API Documentation v2.0.0

The DataLogicEngine exposes a RESTful API powered by Flask blueprints. These endpoints support the Knowledge Graph, Simulation Engine, and AI Gateway operations.

## Base URL

`http://localhost:5000/api/v1`

## Authentication

All endpoints (except `/health`) require authentication via `Session` (frontend proxy) or `Authorization: Bearer <token>` header (external).

---

## 1. Knowledge Routes (`/knowledge`)

Manage the 17-Axis framework entities.

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

## 2. Simulation Routes (`/simulation`)

Control the recursive simulation engine.

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
- **POST** `/mcp/tools/call`
  - Execute an MCP tool.
  - _Body_: `{ "server_name": "...", "tool_name": "...", "arguments": {} }`
