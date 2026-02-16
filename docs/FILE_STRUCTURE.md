# Application File Structure

## Purpose

Define repository layout, naming conventions, and inventory generation standards for DataLogicEngine.

## Audience

1. Developers and reviewers
2. Architecture and platform teams
3. Release engineers
4. Security and compliance auditors

## Repository layout (top level)

```text
DataLogicEngine/
├── backend/          # Backend services, middleware, security, AI orchestration
├── core/             # Core engine and domain abstractions
├── frontend/         # Next.js app, component system, Electron desktop runtime
├── routes/           # API route handlers and endpoint wiring
├── scripts/          # Verification, generation, packaging, and runbook automation
├── tests/            # Unit, integration, security, and end-to-end tests
├── docs/             # Source-of-truth docs, standards, runbooks, ADRs
├── deploy/           # Deployment and platform assets
└── sdk/              # SDK and external integration helpers
```

## Naming conventions

### Backend (Python/Flask)

1. Modules/files: `snake_case.py`
2. Classes: `PascalCase`
3. Functions/variables: `snake_case`
4. Constants: `UPPER_SNAKE_CASE`

### Frontend (Next.js/React/TypeScript)

1. Routes/directories: App Router folders (`app/<route>/page.tsx`)
2. Components: `PascalCase.tsx`
3. Hooks/utilities: `camelCase` (`useX.ts`, `utils.ts`)
4. API clients: `frontend/lib/api/*`

### Scripts and automation

1. Python verification scripts: `verify_<area>.py`
2. Windows operations scripts: verb-first PowerShell names (`start_*.ps1`, `verify_*.ps1`)
3. Generated artifacts: explicitly named in `docs/` and not hand-edited

## High-value subtrees

### `frontend/`

1. `app/` route pages and app-router segments
2. `components/` UI components and feature composition
3. `electron/` desktop process and IPC bridge code
4. `lib/` API and shared utilities
5. `tests/` unit and E2E coverage

### `backend/` and `routes/`

1. API gateway/auth/storage/simulation/tracing services
2. Middleware for security headers, limits, request correlation, and runtime policy
3. AI governance and model routing layers
4. Connector and MCP service paths

### `scripts/windows/`

1. `start_local_stack.ps1`
2. `stop_local_stack.ps1`
3. `run_packaging_smoke.ps1`
4. `verify_nsis_governance.ps1`
5. `verify_installer_signature.ps1`

## Generated inventory and structure artifacts

1. Full file inventory:
   `docs/FILE_INVENTORY.csv`
2. Generated structure summary:
   `docs/GENERATED_STRUCTURE.md`
3. Architecture implementation map:
   `docs/ARCHITECTURE_MAP.md`

## Generation procedure

Run from repository root:

```powershell
.venv\Scripts\python.exe .\scripts\generate_docs.py
```

This updates:

1. `docs/FILE_INVENTORY.csv`
2. `docs/GENERATED_STRUCTURE.md`

## Validation

1. Verify cross-document references:
   `python scripts/verify_docs_references.py`
2. Verify environment parity:
   `python scripts/verify_environment_parity.py`
3. Verify lockfile governance:
   `python scripts/verify_lockfiles.py`

## Related documents

1. `docs/ARCHITECTURE_MAP.md`
2. `docs/DOCUMENTATION_STANDARDS.md`
3. `docs/DOCUMENTATION_COVERAGE_MATRIX.md`
4. `docs/README.md`

## Document control

1. Owner: Platform Engineering
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days
