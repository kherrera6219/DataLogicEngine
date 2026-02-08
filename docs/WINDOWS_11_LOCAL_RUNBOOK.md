# DataLogicEngine Windows 11 Local Runbook

## Goal

Run DataLogicEngine locally on Windows 11 with:

1. Internet access
2. At least one LLM provider API key
3. Local `.env` configuration

Default path uses SQLite/in-memory fallbacks. PostgreSQL/Redis/Neo4j/object services are optional.

## Current State (February 8, 2026)

1. Local startup scripts are functional.
2. Core frontend routes are reachable.
3. Desktop mode supports no-login startup.
4. Settings API key save/test, AI model controls, and local storage lifecycle controls are wired.
5. Desktop installer builds successfully and is copied to repo root.

## Prerequisites

1. Python 3.11+
2. Node.js 20+
3. npm
4. Optional: Docker Desktop for local data service stack

## Initial Setup

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

Copy-Item .env.template .env
```

Set in `.env`:

1. `SESSION_SECRET=<long_random_value>`
2. At least one key:
   `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`/`GOOGLE_API_KEY`

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

## Start / Stop

### Fast local mode

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

### Full local data services

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1 -WithDataServices
```

### Stop app stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\stop_local_stack.ps1
```

### Stop app + data services

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\stop_local_stack.ps1 -WithDataServices
```

## Validation Checklist

1. Frontend responds: `http://127.0.0.1:3000`
2. Backend health responds: `http://127.0.0.1:5000/health`
3. Provider key validates:
   `.venv\Scripts\python.exe .\scripts\verify_api_keys.py`
4. Route policy smoke passes:
   `powershell -ExecutionPolicy Bypass -File .\scripts\windows\test_frontend_route_policy.ps1 -FrontendPort 3000`
5. Optional local data stack validates:
   `.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py`

## Desktop Installer Workflow

Build installer:

```powershell
npm --prefix frontend run electron:dist
```

Resulting files:

1. `DataLogicEngine Setup Latest.exe` (repo root alias)
2. `DataLogicEngine Setup <version>.exe` (repo root versioned copy)
3. `frontend/dist/` artifacts

Run manually:

```powershell
.\DataLogicEngine Setup Latest.exe
```

## Optional WiX/WinSW Packaging Path

If you use `deploy/windows/` manifests:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\prepare_wix_assets.ps1
```

This ensures:

1. `deploy/windows/winsw.exe` is present.
2. Service wrappers are refreshed:
   `deploy/windows/DataLogic_Backend.exe`, `deploy/windows/DataLogic_Frontend.exe`.

## Known Limitations

1. `Settings > Notifications` remains placeholder.
2. Storage cloud config form persistence is incomplete.
3. Register submit flow is not wired.
4. Some MCP admin actions remain disabled pending backend workflow completion.

## Related Documents

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/USER_GUIDE.md`
3. `docs/DEVELOPER_GUIDE.md`
4. `docs/DEPLOYMENT.md`
5. `docs/TESTING.md`

## Document Control

1. Owner: Platform Engineering
2. Last updated: 2026-02-08
3. Status: Active
4. Review cadence: Every 30 days
