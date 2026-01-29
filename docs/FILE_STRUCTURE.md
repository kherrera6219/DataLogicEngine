# Application File Structure & Naming Conventions

## 1. Naming Conventions

The project adheres to strict naming conventions to ensure consistency across the split-stack architecture.

### 1.1. Backend (Python/Flask)

- **Modules/Files**: `snake_case.py` (e.g., `knowledge_graph.py`, `api_gateway.py`)
- **Classes**: `PascalCase` (e.g., `KnowledgeGraph`, `TraceEngine`)
- **Functions/Variables**: `snake_case` (e.g., `get_trace_by_id`, `current_user`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`, `DEFAULT_MODEL`)
- **Directories**: `snake_case` (e.g., `llm_gateway/`, `knowledge_algorithms/`)

### 1.2. Frontend (Next.js 16 / React 19)

- **Directories (Routes)**: `kebab-case` or plain names (e.g., `dashboard/`, `chat/`, `knowledge/`)
- **Files (Pages/Layouts)**: Reserved names (e.g., `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`)
- **Components**: `PascalCase.tsx` (e.g., `ChatInterface.tsx`, `TraceCard.tsx`, `NavBar.tsx`)
- **Hooks**: `camelCase` with `use` prefix (e.g., `useTraceData.ts`, `useAuth.ts`)
- **Utilities**: `camelCase` (e.g., `apiClient.ts`, `formatDate.ts`, `utils.ts`)
- **API Clients**: `camelCase` in `lib/api/` (e.g., `trace.ts`, `auth.ts`, `mcp.ts`)

---

## 2. Directory Structure Overview

```
DataLogicEngine/
├── backend/                  # Flask Backend & API Logic
├── sdk/                      # UKG Python SDK (Core Logic Engine)
├── frontend/                 # Next.js Frontend Application
├── docs/                     # Project Documentation
├── tests/                    # Test Suites
├── scripts/                  # Utility & DevOps Scripts
├── migrations/               # Database Migrations (Alembic)
├── wsgi.py                   # Production Entry Point
├── Dockerfile                # Backend Docker Configuration
└── README.md                 # Project Overview
```

---

## 3. Detailed Structure

### 3.1. Frontend (`/frontend`)

This directory contains the **Next.js 16** (React 19) App Router application, packaged for desktop via **Electron**.

```text
frontend/
├── app/                        # Application Routes (App Router)
├── components/                 # React Components
│   ├── Chat/                   # Chat-specific (DetailedResponseView, TraceVisualizer)
│   ├── ui/                     # Base UI components (ScrollArea, Button, etc.)
│   ├── mcp/                    # MCP Analytics & Management
│   └── Graph/                  # 3D Axis Visualization
├── lib/                        # Utilities & API Clients
├── electron/                   # Desktop process logic (main.ts, preload.ts)
├── electron-builder.yml        # Desktop build configuration
├── next.config.ts              # Next.js configuration
└── package.json                # Dependencies & Build Scripts
```

### 3.2. Backend (`/backend`)

Flask 3.1 application logic, including the high-fidelity graduation engines.

```text
backend/
├── app.py                      # Main entry point & Flask instance
├── mcp_server/                 # MCP Implementation (Router/Registry)
├── services/                   # Multimodal (Audio/Video/DocProcessor)
├── security/                   # Hardening (PII/Injection Shield)
├── quad_persona/               # QuadPersonaEngine
├── simulation/                 # SimulationEngine (10-Layer)
├── truth_engine/               # TruthEngine & Blockchain Adapter
├── tracing/                    # Tracing models & Logic
├── llm_gateway/                # Model orchestration
└── routes/                     # Blueprint registration
```

### 3.3. Core (`/core`)

This folder houses the "Business Logic" of the Universal Knowledge Graph, independent of the HTTP API layer.

```text
core/
├── axes/                               # 17-Axis Framework (30+ KB files)
│   ├── __init__.py
│   ├── axis_system.py                  # Framework orchestrator (35 KB)
│   ├── axis1_identity.py               # Identity context (32 KB)
│   ├── axis2_sector.py                 # Sector expertise (34 KB)
│   ├── axis3_domain.py                 # Domain expertise (33 KB)
│   ├── axis4_knowledge.py              # Knowledge types (31 KB)
│   ├── axis5_temporal.py               # Temporal context
│   ├── axis6_regulatory.py             # Regulatory frameworks (38 KB)
│   ├── axis7_compliance.py             # Compliance rules (36 KB)
│   ├── axis8_expert_knowledge.py       # Knowledge expert profiles
│   ├── axis9_expert_sector.py          # Sector experts
│   ├── axis10_expert_regulatory.py     # Regulatory experts
│   ├── axis11_expert_compliance.py     # Compliance experts
│   ├── axis12_location.py              # Geolocation (34 KB)
│   ├── axis13_time.py                  # Time reasoning (32 KB)
│   ├── axis14_federated.py             # Federated learning
│   ├── axis15_time_arrows.py           # Directional time
│   ├── axis16_reserved.py              # Future expansion
│   └── axis17_observability.py         # Tracing & metrics (33 KB)
│
├── mcp/                                # Model Context Protocol
│   ├── __init__.py
│   ├── mcp_protocol.py                 # JSON-RPC 2.0 protocol (25 KB)
│   ├── mcp_server.py                   # MCP server (28 KB)
│   ├── mcp_client.py                   # MCP client (22 KB)
│   ├── mcp_manager.py                  # Server/client orchestration (24 KB)
│   ├── servers/                        # MCP server implementations
│   │   └── default_server.py
│   └── README.md                       # MCP documentation
│
├── simulation/                         # Scenario Simulation Engine
│   ├── __init__.py
│   ├── app_orchestrator.py             # Master orchestrator (42 KB)
│   ├── layer4_reasoning.py             # Multi-step reasoning (38 KB)
│   ├── layer5_integration.py           # Result synthesis (35 KB)
│   ├── memory_simulation.py            # Memory-based reasoning (29 KB)
│   ├── query_persona_engine.py         # Persona-based queries (34 KB)
│   └── refinement_orchestrator.py      # Iterative refinement (78 KB!)
│
├── knowledge_algorithm/                # Knowledge Algorithm System
│   ├── __init__.py
│   ├── ka_base.py                      # Base algorithm class
│   ├── ka_loader.py                    # Algorithm loader
│   └── implementations/                # 100+ algorithm implementations
│       ├── ka001_basic_query.py
│       ├── ka002_advanced_search.py
│       ├── ka056_recursive_planning.py
│       └── ... (100+ files)
│
├── graph/                              # Graph Operations
│   ├── __init__.py
│   ├── graph_manager.py                # Graph management
│   └── traversal.py                    # Graph traversal algorithms
│
├── memory/                             # Memory Management
│   ├── __init__.py
│   ├── memory_manager.py               # Memory operations
│   └── structured_memory.py            # Structured memory entries
│
├── engine/                             # Engine Utilities
│   ├── __init__.py
│   └── engine_utils.py
│
├── persona/                            # Persona System
│   ├── __init__.py
│   ├── persona_manager.py              # Persona management
│   └── expert_profiles.py              # Expert persona profiles
│
├── nlp/                                # NLP Utilities
│   ├── __init__.py
│   └── text_processing.py
│
└── data/                               # Data Utilities
    ├── __init__.py
    └── data_utils.py
```

### 3.4. Models (`/models`)

Database models using **SQLAlchemy 2.0**.

```text
models/
├── __init__.py                         # Model exports
├── user.py                             # User, APIKey, OAuthAccount, PasswordHistory
├── knowledge.py                        # KnowledgeGraphNode, KnowledgeGraphEdge (legacy)
├── ukg.py                              # Node, Edge, Chat, Message, UkgSession, MemoryEntry
├── truth_engine.py                     # TruthSession, TruthAuditEvent, TruthArtifact, TruthBudget
├── tracing.py                          # TraceRun, TraceStage, TraceEvidence, TraceClaim, etc.
├── mcp.py                              # MCPServer, MCPResource, MCPTool, MCPPrompt
├── simulation.py                       # SimulationSession, SimulationStep, SimulationOutcome
├── ka.py                               # KnowledgeAlgorithm, KAExecution
├── llm.py                              # LLMProvider, LLMProviderUsage, ExternalAPIKey
└── compliance.py                       # AuditLog, ComplianceEvent, PolicyRecord
```

**Total: 40+ database tables** organized across 10 model files.

### 3.5. Routes (`/routes`)

API route blueprints returning standardized JSON responses.

```text
routes/
├── __init__.py                         # Route registration
├── auth_routes.py                      # Authentication endpoints (15 KB)
│   # POST /api/v1/auth/login, /register, /logout
│   # GET /api/v1/auth/login/sso, /check
│
├── api_routes.py                       # Generic API endpoints (8 KB)
│   # GET /health, /api/v1/
│
├── admin_routes.py                     # Admin operations (12 KB)
│   # GET /api/v1/admin/users
│   # POST /api/v1/admin/users/:id/promote
│   # GET/POST /api/v1/admin/providers
│
├── knowledge_routes.py                 # Knowledge graph operations (18 KB)
│   # GET/POST /api/v1/knowledge/nodes
│   # GET/POST /api/v1/knowledge/edges
│   # GET /api/v1/knowledge/query
│
├── mcp_routes.py                       # MCP operations (18 KB)
│   # GET/POST /api/v1/mcp/servers
│   # POST /api/v1/mcp/servers/:id/initialize
│   # GET /api/v1/mcp/tools
│   # POST /api/v1/mcp/tools/:id/call
│
├── ka_routes.py                        # Knowledge Algorithm routes (19 KB)
│   # GET /api/v1/ka/algorithms
│   # GET /api/v1/ka/algorithms/:id
│   # POST /api/v1/ka/execute
│
├── compliance_routes.py                # Compliance operations (9 KB)
│   # GET /api/v1/compliance/audit-logs
│   # GET /api/v1/compliance/standards
│   # GET /api/v1/compliance/audit/export
│
└── simulation_routes.py                # Simulation operations (11 KB)
    # POST /api/v1/simulation/start
    # GET /api/v1/simulation/:id
    # POST /api/v1/simulation/:id/step
```

---

## 4. Versioning & Dependencies

### 4.1. Backend (Python 3.11+)

| Package | Version | Purpose |
|---------|---------|---------|
| **Flask** | 3.1.2 | Web framework |
| **SQLAlchemy** | 2.0.36 | ORM |
| **Gunicorn** | 23.0.0 | WSGI server |
| **PostgreSQL** | 15+ | Database (via psycopg2) |
| **Redis** | 5.2.0 | Cache/queue |
| **Celery** | 5.4.0 | Task queue |
| **Flask-Login** | 0.6.3 | Authentication |
| **Authlib** | 1.3.0 | SSO/OIDC |
| **PyJWT** | 2.10.1 | JWT tokens |
| **Cryptography** | 44.0.0 | Encryption |
| **bcrypt** | 4.2.1 | Password hashing |
| **Last Updated:** 2026-01-28
| **Version:** 2.5.0-GRADUATED
| **Pydantic** | 2.x | Data validation |
| **Marshmallow** | 3.x | Schema validation |
| **OpenAI** | 1.58.1 | LLM integration |
| **Sentry-SDK** | 2.19.2 | Error tracking |
| **Alembic** | 1.14.0 | Database migrations |
| **NetworkX** | 3.4.2 | Graph processing |

### 4.2. Frontend (Node.js 18.17+)

| Package | Version | Purpose |
|---------|---------|---------|
| **Next.js** | 16.1.1 | React framework |
| **React** | 19.2.3 | UI library |
| **TypeScript** | 5.x | Type safety |
| **Tailwind CSS** | 4.x | Styling framework |
| **Radix UI** | Latest | Accessible primitives |
| **Lucide React** | 0.562.0 | Icon library |
| **SWR** | 2.3.8 | Data fetching |
| **Class Variance Authority** | 0.7.1 | CSS-in-JS |
| **ESLint** | 9.x | Linting |

---

## 5. Deployment Artifacts

- `Dockerfile` (Root): Builds the **Backend** container.
- `frontend/Dockerfile`: Builds the **Frontend** container.
- `docker-compose.yml`: Orchestrates both services + Postgres + Redis.

---

## 6. Enterprise Constraints

1.  **Strict Typing**: Frontend must use TypeScript (`.ts`/`.tsx`). Backend should use Type Hints where possible.
2.  **No Dead Code**: Unused files (e.g., `temp_script.py`, `old_index.html`) must be moved to `archive/` or deleted.
3.  **Config Separation**: Secrets must come from Environment Variables (`.env`), never hardcoded.
4.  **Audit Logs**: All state-changing actions in Backend must emit an Audit Log.
