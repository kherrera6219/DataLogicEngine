# Application File Structure

## Purpose

Describe the primary repository layout and naming conventions used by DataLogicEngine.

## Naming Conventions

### Backend (Python/Flask)

1. Modules/files: `snake_case.py`
2. Classes: `PascalCase`
3. Functions/variables: `snake_case`
4. Constants: `UPPER_SNAKE_CASE`

### Frontend (Next.js/React/TypeScript)

1. Routes/directories: app-router folders (`app/<route>/page.tsx`)
2. Components: `PascalCase.tsx`
3. Hooks/utilities: `camelCase` (`useX.ts`, `utils.ts`)
4. API clients: `frontend/lib/api/*`

## Repository Layout (Top Level)

```text
DataLogicEngine/
├── backend/          # Backend modules and integrations
├── core/             # Core logic and frameworks
├── frontend/         # Next.js UI and Electron runtime
├── routes/           # API route modules
├── scripts/          # Local automation and validation scripts
├── tests/            # Test suites
├── docs/             # Active and historical documentation
├── deploy/           # Deployment and operations assets
└── sdk/              # Python SDK
```

## High-Value Subtrees

### `frontend/`

1. `app/` route pages
2. `components/` UI and feature components
3. `electron/` desktop process sources
4. `lib/api/` shared API client layer

### `backend/` and `routes/`

1. Gateway/auth/storage/simulation/tracing services
2. Route blueprints and API handlers
3. Supporting integrations and policy enforcement

### `scripts/windows/`

1. `start_local_stack.ps1`
2. `stop_local_stack.ps1`
3. `test_frontend_route_policy.ps1`
4. `prepare_wix_assets.ps1`

## Generated Inventory

1. Full inventory CSV: `docs/FILE_INVENTORY.csv`
2. Generated structure summary: `docs/GENERATED_STRUCTURE.md`
3. Generation command:

```powershell
.venv\Scripts\python.exe .\scripts\generate_docs.py
```

## Document Control

1. Owner: Platform Engineering
2. Last updated: 2026-02-08
3. Status: Active
4. Review cadence: Every 30 days
