# DataLogicEngine Windows 11 Local Runbook

## Goal

Run DataLogicEngine locally on Windows 11 with:

1. Internet access
2. At least one LLM provider API key
3. Local `.env` configuration

Default path uses SQLite/in-memory fallbacks. PostgreSQL/Redis/Neo4j/object services are optional.

## Current State (May 22, 2026)

1. Local startup scripts are functional.
2. Core frontend routes are reachable.
3. Desktop mode supports no-login startup.
4. Settings API key save/test, AI model controls, and local storage lifecycle controls are wired.
5. Desktop installer builds successfully and is copied to repo root.
6. Startup script now auto-resolves backend/frontend port conflicts by default.
7. Desktop runtime now stores install secret using OS-protected encryption when available and writes local runtime logs under user data.
8. Silent install and retention-aware silent uninstall controls are available for enterprise deployments.

## Prerequisites

1. Python 3.11+
2. Node.js 24+
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

Port conflict behavior:

1. `BackendPort` and `FrontendPort` are auto-resolved to the next available port by default.
2. Disable auto-resolution when needed:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1 -AutoResolvePortConflicts $false
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

1. `DataLogicEngine Setup Latest.exe` (repo root installer)
2. `DataLogicEngine Setup Latest.exe.sha256` and `DataLogicEngine Setup Latest.exe.blockmap` (repo root integrity sidecars)
3. `frontend/dist/` packaged app artifacts without duplicate setup EXEs

Run manually:

```powershell
.\DataLogicEngine Setup Latest.exe
```

Silent install:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install_silent.ps1
```

Silent uninstall (preserve data by default):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall.ps1 -Silent -KeepData
```

Silent uninstall (delete data):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall.ps1 -Silent -DeleteData
```

NSIS governance + packaging smoke checks:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -Mode portable
```

Controlled auto-update policy (desktop packaged runtime):

1. Auto-update is disabled by default.
2. Enable only with explicit feed policy:
   - `DLE_AUTO_UPDATE_ENABLED=true`
   - `DLE_AUTO_UPDATE_FEED_URL=<https://...>`
3. Optional controls:
   - `DLE_AUTO_UPDATE_AUTO_DOWNLOAD=true|false`
   - `DLE_AUTO_UPDATE_AUTO_INSTALL_ON_QUIT=true|false`

Secure local log storage:

1. Desktop runtime log file: `%APPDATA%\DataLogicEngine\logs\desktop-runtime.log` (best-effort restricted permissions).
2. Installer-managed local data logs: `C:\ProgramData\DataLogicEngine\logs` (restricted ACL applied by installer script).

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

1. Manual application-readiness evidence remains open: WCAG, keyboard, NVDA, and failure-mode validation are tracked in `TODO.md`.
2. Register submit flow is intentionally disabled in the current local-first build; `/register` redirects to `/dashboard`.
3. Release builds still need trusted production code-signing certificate evidence before public distribution.

## Related Documents

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/USER_GUIDE.md`
3. `docs/DEVELOPER_GUIDE.md`
4. `docs/DEPLOYMENT.md`
5. `docs/TESTING.md`

## Document Control

1. Owner: Platform Engineering
2. Last updated: 2026-05-22
3. Status: Active
4. Review cadence: Every 30 days
