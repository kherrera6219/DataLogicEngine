# DataLogicEngine Developer Guide

## Purpose

Developer onboarding and daily engineering workflow.

## Prerequisites

1. Python 3.11+
2. Node.js 20+
3. Windows PowerShell (for local run scripts on Windows)
4. At least one provider API key for end-to-end feature testing

Optional local services:

1. Docker Desktop (for PostgreSQL, Redis, Neo4j, MinIO local stack)

## Initial Setup

```powershell
git clone https://github.com/kherrera6219/DataLogicEngine.git
cd DataLogicEngine

python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

Copy-Item .env.template .env
cd frontend
npm install
cd ..
```

Set in `.env`:

1. `SESSION_SECRET`
2. At least one provider key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`)

## Local Run Modes

### Fast local mode (API keys + internet)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

### Full local data stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1 -WithDataServices
```

Stop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\stop_local_stack.ps1
```

## Build and Packaging

Frontend build:

```powershell
npm --prefix frontend run build
```

Electron compile:

```powershell
npm --prefix frontend run electron:build
```

Desktop installer:

```powershell
npm --prefix frontend run electron:dist
```

## Testing

Backend suite:

```powershell
python run_test_suite.py
```

Frontend unit tests:

```powershell
npm --prefix frontend test
```

Route policy smoke:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\test_frontend_route_policy.ps1 -FrontendPort 3000
```

Provider/model validation:

```powershell
.venv\Scripts\python.exe .\scripts\verify_api_keys.py
```

Local data plane validation:

```powershell
.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
```

## Repository Structure (High Level)

```text
DataLogicEngine/
├── backend/          # Backend services and orchestration
├── core/             # Core logic and frameworks
├── frontend/         # Next.js UI + Electron runtime
├── routes/           # API route modules
├── scripts/          # Local ops and validation scripts
├── tests/            # Automated tests
└── docs/             # Active and historical documentation
```

## Documentation Maintenance

Regenerate inventory and generated structure docs after major repository changes:

```powershell
.venv\Scripts\python.exe .\scripts\generate_docs.py
```

## Common Gaps to Keep in Mind

1. Notifications settings tab is still placeholder UI.
2. Storage cloud configuration form is not fully persisted.
3. Register form is visual only; no submit wiring yet.
4. Some MCP admin actions are intentionally disabled pending backend workflows.

## Related Documents

1. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
2. `docs/TESTING.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DEPLOYMENT.md`
5. `docs/CONTRIBUTING.md`

## Document Control

1. Owner: Developer Experience
2. Last updated: 2026-02-08
3. Status: Active
4. Review cadence: Every 30 days
