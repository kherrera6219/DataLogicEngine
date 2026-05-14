# DataLogicEngine Developer Guide

## Purpose

Developer onboarding and daily engineering workflow.

## Prerequisites

1. Python 3.11+
2. Node.js 22+
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
git config core.hooksPath .githooks
cd frontend
npm install
cd ..
```

Verify local readiness before booting services:

```powershell
.\.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports
```

Set in `.env`:

1. `SESSION_SECRET` — required for persistent sessions. If omitted in development the app generates an ephemeral secret and logs a warning (sessions reset on every restart). **Required and enforced at startup in production** — the app will refuse to start without it. Generate a value with:
   ```powershell
   python scripts/generate_secrets.py
   ```
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

Bootstrap smoke check:

```powershell
.\.venv\Scripts\python.exe .\scripts\test_smoke.py
```

Developer environment doctor:

```powershell
.\.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports
```

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

Docs reference validation:

```powershell
.venv\Scripts\python.exe .\scripts\verify_docs_references.py
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

## Local workflow notes

1. `/api/v1/*` is the supported REST surface for application integrations; older `/api/*` aliases are compatibility-only.
2. `AUTO_CREATE_SCHEMA=true` is a disposable local-only escape hatch and must not be carried into shared or production environments.
3. Run `.\.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports` before escalating local setup issues or handoff problems.

## Related Documents

1. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
2. `docs/TESTING.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DEPLOYMENT.md`
5. `docs/CONTRIBUTING.md`

## Document Control

1. Owner: Developer Experience
2. Last updated: 2026-03-31
3. Status: Active
4. Review cadence: Every 30 days
