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

## Local Data Services Subsystem Architecture

DataLogicEngine operates as a local-first application using an embedded and portable database stack. All database executables, configuration files, and active data directories reside entirely under the `databases/` folder in the repository root.

### 1. Database Provisioning & Installation

Portable databases (Windows binaries) are prepared using an automated script that pulls from validated mirrors and extracts them without system-level registration or registry pollution:

```powershell
# Download and install PostgreSQL 16, Redis, Neo4j Community, and Eclipse Temurin Java 17 JRE
python scripts/setup_local_databases.py --all
```

*Existing installations are automatically skipped. JRE 17 is bundled locally for isolated Neo4j Community operations, keeping the system free of global JRE path requirements.*

### 2. Datastore Inventory & Network Topology

The local-first runtime utilizes 5 distinct datastores to implement structured RAG, temporal auditing, and high-performance caching:

| Datastore | Port | Mode | Directory Path | Purpose |
|---|---|---|---|---|
| **PostgreSQL 16** | `5432` | Portable Process | `databases/postgresql/` | Structured system tables, relational models, and transaction audit trails. |
| **Redis** | `6379` | Portable Process | `databases/redis/` | Ultra-fast caching, rate-limiting tokens, and real-time reasoning cache. |
| **Neo4j Community** | `7687` | Portable Process | `databases/neo4j/` | Graph reasoning context, cross-persona debate paths, and relationship taxonomies. |
| **ChromaDB** | *(Portless)* | Embedded Client | `databases/chroma/` | High-dimensional RAG vector storage, indexing text chunks and document metadata. |
| **Local File Object Store** | *(Portless)* | Native Filesystem | `databases/objects/` | Local blob storage for Merkle logs, FROST snapshots, and immutable trace audit bundles. |

### 3. Service Lifecycle & Lifecycle Hooks

* **Auto-Start Hook**: The databases automatically bootstrap when launching `python app.py` through the Flask-embedded `DatabaseLifecycleManager`.
* **Manual Lifecycle Operations**: Developers can manually start and stop individual datastores:
  * PostgreSQL: `databases/postgresql/bin/pg_ctl.exe -D databases/postgresql/data -l databases/postgresql/pg.log start`
  * Redis: `databases/redis/redis-server.exe`
  * Neo4j: `databases/neo4j/bin/neo4j.bat start`
* **Verification Command**:
  ```powershell
  python scripts/setup_local_databases.py --verify
  ```
  *This checks whether expected binaries exist and attempts socket connections on service ports to report active statuses.*

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

1. Manual application-readiness evidence remains open for NVDA validation; automated WCAG, keyboard navigation, failure-mode, and export/delete evidence is tracked in `reports/app-readiness/`.
2. Register submit flow is intentionally disabled in the current local-first build; `/register` redirects to `/dashboard`.
3. Release builds still need a trusted production certificate provisioned in GitHub secrets and a signed release workflow run before public distribution.

## Related Documents

1. `docs/PRODUCT_OVERVIEW.md`
2. `docs/USER_GUIDE.md`
3. `docs/DEVELOPER_GUIDE.md`
4. `docs/DEPLOYMENT.md`
5. `docs/TESTING.md`

## Document Control

1. Owner: Platform Engineering
2. Last updated: 2026-05-23
3. Status: Active
4. Review cadence: Every 30 days
