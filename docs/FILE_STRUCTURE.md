# Application File Structure & Naming Conventions

## 1. Naming Conventions

The project adheres to strict naming conventions to ensure consistency across the split-stack architecture.

### 1.1. Backend (Python/Flask)

- **Modules/Files**: `snake_case.py` (e.g., `knowledge_graph.py`, `api_gateway.py`)
- **Classes**: `PascalCase` (e.g., `KnowledgeGraph`, `TraceEngine`)
- **Functions/Variables**: `snake_case` (e.g., `get_trace_by_id`, `current_user`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`, `DEFAULT_MODEL`)
- **Directories**: `snake_case` (e.g., `llm_gateway/`, `knowledge_algorithms/`)

### 1.2. Frontend (Next.js 15.1 / React 18.3)

- **Directories (Routes)**: `kebab-case` or plain names (e.g., `dashboard/`, `chat/`, `knowledge/`)
- **Files (Pages/Layouts)**: Reserved names (e.g., `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`)
- **Components**: `PascalCase.tsx` (e.g., `ChatInterface.tsx`, `TraceCard.tsx`, `NavBar.tsx`)
- **Hooks**: `camelCase` with `use` prefix (e.g., `useTraceData.ts`, `useAuth.ts`)
- **Utilities**: `camelCase` (e.g., `apiClient.ts`, `formatDate.ts`, `utils.ts`)
- **API Clients**: `camelCase` in `lib/api/` (e.g., `trace.ts`, `auth.ts`, `mcp.ts`)

---

## 2. Directory Structure Overview

```text
DataLogicEngine/
├── backend/                  # Flask Backend & API Logic (Primary Application)
├── core/                     # Internal Business Logic (17-Axis, Simulation Engines)
├── frontend/                 # Next.js Frontend (Desktop & Cloud UI)
├── docs/                     # Documentation & Specifications
├── tests/                    # Consolidated Test Suite
├── scripts/                  # Utility & DevOps Scripts
├── migrations/               # Database Migrations (Alembic)
├── wsgi.py                   # Production Entry Point
├── Dockerfile                # Backend Docker Configuration
└── README.md                 # Project Overview
```

---

## 3. detailed Structure

### 3.1. Backend (`/backend`)

The Flask 3.1 application logic, serving as the API and orchestrator for the core engines.

```text
backend/
├── app.py                      # Main entry point & Flask instance
├── mcp_server/                 # MCP Implementation (Tools, Resources)
├── simulation/                 # Simulation Wrappers
├── truth_engine/               # TruthEngine API Layer
├── knowledge_algorithms/       # Algorithm implementations (L9/L10)
├── auth/                       # Authentication (MFA, SSO)
├── security/                   # Hardening (Encryption, Audit)
├── services/                   # Service Layer (Email, Export)
├── routes/                     # Blueprint registration
│   ├── api_gateway/
│   ├── auth/
│   ├── llm_gateway/
│   └── ...
└── ukg_api.py                  # Core API Interface
```

### 3.2. Core (`/core`)

Internal business logic and mathematical framework of the UKG system.

```text
core/
├── axes/                       # 17-Axis Coordinate Framework implementation
├── simulation/                 # Deep Simulation Logic (Layers 4-10)
├── knowledge_algorithm/        # Base algorithm classes
├── mcp/                        # Internal MCP Protocol logic
├── memory/                     # Structured Memory Managers
├── graph/                      # Graph Traversal Logic
└── system/                     # System-level orchestration
```

### 3.3. Frontend (`/frontend`)

Next.js 15.1 application powered by Electron for Desktop Mode.

```text
frontend/
├── app/                        # App Router (Next.js)
│   ├── (auth)/                 # Auth routes (Login, Register)
│   ├── dashboard/              # Main Dashboard
│   ├── chat/                   # Chat Interface
│   └── ...
├── components/                 # React Components
│   ├── Chat/
│   ├── Graph/
│   └── ui/                     # ShadCN/Radix primitives
├── electron/                   # Main Process (Desktop Mode)
├── lib/                        # API Clients & Utilities
├── public/                     # Static Assets
└── package.json                # Dependencies
```

### 3.4. Documentation (`/docs`)

Comprehensive documentation covering architecture, APIs, and procedures.

```text
docs/
├── FILE_STRUCTURE.md           # This file
├── FILE_INVENTORY.csv          # Complete auto-generated file list
├── ARCHITECTURE.md             # System design & constraints
├── API.md                      # API Reference
├── SECURITY.md                 # Security policies
├── TESTING.md                  # Test strategies
└── ...
```

---

## 4. Updates & Verification

This document is automatically verified against the filesystem using `scripts/generate_docs.py`.

- **Last Scan**: 2026-02-04
- **Total Files**: >2000
- **Inventory**: See `docs/FILE_INVENTORY.csv` for the full manifest.
