# Application File Structure & Naming Conventions

## 1. Naming Conventions

The project adheres to strict naming conventions to ensure consistency across the split-stack architecture.

### 1.1. Backend (Python/Flask)

- **Modules/Files**: `snake_case.py` (e.g., `knowledge_graph.py`, `api_gateway.py`)
- **Classes**: `PascalCase` (e.g., `KnowledgeGraph`, `TraceEngine`)
- **Functions/Variables**: `snake_case` (e.g., `get_trace_by_id`, `current_user`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`, `DEFAULT_MODEL`)
- **Directories**: `snake_case` (e.g., `llm_gateway/`, `knowledge_algorithms/`)

### 1.2. Frontend (Next.js/React)

- **Directories (Routes)**: `kebab-case` (e.g., `knowledge-base/`, `trace-runs/`)
- **Files (Pages/Layouts)**: `camelCase.tsx` or reserved names (e.g., `page.tsx`, `layout.tsx`, `middleware.ts`)
- **Components**: `PascalCase.tsx` (e.g., `ChatInterface.tsx`, `TraceCard.tsx`)
- **Hooks**: `camelCase` (e.g., `useTraceData.ts`)
- **Utilities**: `camelCase` (e.g., `apiClient.ts`, `formatDate.ts`)

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

This directory contains the Next.js 14 App Router application.

```text
frontend/
├── app/                      # Application Routes (App Router)
│   ├── (auth)/               # Auth Group (Login/Register)
│   │   ├── login/
│   │   └── register/
│   ├── dashboard/            # Main Dashboard
│   │   └── page.tsx
│   ├── chat/                 # Chat Interface
│   ├── runs/                 # Trace Viewer
│   │   ├── [id]/             # Dynamic Route (Run Details)
│   │   └── page.tsx
│   ├── knowledge/            # 17-Axis Knowledge Browser
│   ├── layout.tsx            # Root Layout (Providers, Navbar)
│   └── page.tsx              # Landing Page
│
├── components/               # React Components
│   ├── Chat/                 # Chat-specific Components
│   │   ├── ChatInterface.tsx
│   │   └── MessageBubble.tsx
│   ├── ui/                   # Reusable UI Library (Shadcn/Base)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── table.tsx
│   │   └── ...
│   └── ...
│
├── lib/                      # Shared Logic & Utilities
│   ├── api.ts                # Typed API Client
│   ├── utils.ts              # Helper Functions (cn, formatting)
│   └── ...
│
├── public/                   # Static Assets (Images, Icons)
├── next.config.ts            # Next.js Configuration (Proxy)
└── tailwind.config.ts        # Tailwind CSS Configuration
```

### 3.2. Backend (`/backend`)

Contains the Flask application logic, API endpoints, and service integrations.

```text
backend/
├── auth.py                   # Authentication Logic (Flask-Login/JWT)
├── api.py                    # Main API Blueprint Registry
├── config.py                 # Application Configuration Class
├── llm_gateway/              # AI Model Integration Layer
│   ├── api.py                # Gateway Endpoints
│   ├── gateway.py            # Routing Logic (UKG Context Injection)
│   ├── providers.py          # Model Adapters (OpenAI, Azure)
│   └── models.py             # Database Models for Usage/Keys
├── tracing/                  # Distributed Tracing Module
│   ├── trace.py
│   └── models.py
└── ...
```

### 3.3. Core (`/core`)

This folder houses the "Business Logic" of the Universal Knowledge Graph, independent of the HTTP API layer where possible.

```text
core/
├── axes/                     # 17-Axis Implementation
│   ├── axis1_knowledge.py
│   ├── axis2_sector.py
│   └── ... (up to axis17)
├── knowledge_algorithm/      # Knowledge Algorithms (KAs)
│   ├── ka_base.py            # Base Class for KAs
│   └── implementations/      # Specific KA Logic
├── mcp/                      # Model Context Protocol
│   ├── mcp_manager.py        # Tool Registration & Server
│   └── ...
├── engine/                   # Core Execution Engine
└── ...
```

---

## 4. Versioning & Dependencies

### 4.1. Backend

- **Python**: `3.11+`
- **Flask**: `3.x`
- **SQLAlchemy**: `2.x`
- **Pydantic**: `2.x`

### 4.2. Frontend

- **Node.js**: `18.17+` (LTS Recommended)
- **Next.js**: `14.x` (App Router)
- **React**: `18.x`
- **Tailwind CSS**: `3.x` / `4.x`

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
