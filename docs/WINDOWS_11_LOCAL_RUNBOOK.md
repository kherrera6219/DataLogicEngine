# DataLogicEngine Windows 11 Local Runbook

## Goal

Run DataLogicEngine locally on Windows 11 with only:

1. Internet access
2. At least one LLM provider API key
3. A local `.env` file

PostgreSQL and Redis are optional for this local workflow. The default local path uses SQLite and in-memory cache fallbacks.

## Current Status (Deep-Dive Summary)

The repository is close to local-runtime ready. Core backend/frontend startup now works with targeted fixes already applied, and remaining work is concentrated in packaging consistency and regression cleanup.

### Completed Stabilization Phases

1. Bootstrap and dependency parity
2. Backend startup/import crash fixes
3. Frontend TypeScript/test/lint blockers
4. Windows local startup automation (scripts in `scripts/windows`)

### Remaining Phases

1. Packaging alignment (WinSW/WiX assets and service definitions)
2. Broader regression pass (selected backend/frontend suites on Windows)
3. Optional installer hardening for production desktop distribution

Phase 5 update:

1. Added `scripts/windows/prepare_wix_assets.ps1` to fetch `deploy/windows/winsw.exe` and validate WiX inputs.
2. Updated WinSW XML defaults to avoid hardcoded PostgreSQL/Redis assumptions.
3. Aligned installer diagnostics to warn clearly when WiX assets are missing.

## Quick Local Bring-Up (Windows 11)

Run from repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.template .env
```

Edit `.env` and set:

1. `SESSION_SECRET=<64+ char secret>`
2. At least one provider key:
   `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `AZURE_OPENAI_API_KEY` or `GOOGLE_API_KEY` or `MISTRAL_API_KEY`
3. `FLASK_ENV=development` (recommended for local HTTP workflow)

Install frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

Start the local stack:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

Stop the local stack:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\stop_local_stack.ps1
```

## Validation Gates

For each local setup attempt, validate:

1. Backend health: `http://127.0.0.1:5000/health`
2. Frontend availability: `http://127.0.0.1:3000`
3. Chat/gateway call succeeds with configured provider key
4. No startup import errors in backend logs

## Focused Backlog to Reach "Fully Working"

1. Consolidate duplicated/legacy launcher paths that still assume port `8080`.
2. Unify session key naming (`SESSION_SECRET`) across all legacy docs/utilities.
3. Normalize desktop packaging artifacts:
   ensure WinSW/WiX assets are either fully maintained or explicitly marked legacy.
4. Expand CI coverage for Windows startup smoke tests using the local scripts.
