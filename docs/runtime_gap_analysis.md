# Runtime Gap Analysis & Stabilization Plan

## Objective
Identify blockers preventing the Universal Knowledge Graph application from running end-to-end (backend API + frontend UI) and establish a phased plan to close those gaps.

## Current Observations
- **Entry point drift**: Backend defaults to port 8080, while README and some scripts still reference 5000/3000 combinations. This creates confusion when wiring the frontend to the API.
- **Environment configuration ambiguity**: Both `.env` and `config.env` exist, but the project lacks a canonical setup checklist and validation, making first-time setup error-prone.
- **Database bootstrapping is manual**: Developers must run ad-hoc commands to create tables; there is no quick sanity check for database presence.
- **Frontend↔backend expectations are implicit**: Next.js expects an API host but no default proxy or documented URL, so UI calls can silently fail.
- **Health checks are missing**: There is no fast way to verify that prerequisites (Python/Node versions, ports, templates/static assets) are ready before starting both stacks.

## Gaps Blocking a Complete Run
1. **Port & endpoint alignment**
   - Backend default port differs across docs/scripts; frontend base URL is undocumented.
2. **Config & secrets readiness**
   - No enforced presence of `.env`/`config.env`; secrets and DB URLs can be absent without warning.
3. **Database availability**
   - SQLite/PostgreSQL initialization is not validated prior to boot; missing tables will fail at runtime.
4. **Frontend dependency installation**
   - No quick indicator that `npm install` was executed in `frontend/`.
5. **Static/template assets**
   - Rendering depends on `templates/` and `static/` but their absence is not surfaced until runtime.

## Phased Plan
- **Phase 1 – Runtime Readiness (start now)**
  - Align documented ports with backend defaults and expose a preflight script that verifies environment, ports, config files, DB presence, and asset folders.
  - Provide a short runbook to close the immediate blockers above.
- **Phase 2 – Backend/API Reliability**
  - Add database migrations (Flask-Migrate), API error/health endpoints, and a consistent response envelope for UI consumption.
  - Introduce integration tests that hit key routes with the configured DB.
- **Phase 3 – Frontend Integration & UX Stability**
  - Add a configurable API base URL for Next.js, document proxy setup, and create UI smoke tests against the running backend.
  - Surface backend status in the UI (e.g., health badge) and standardize error messaging.

## Phase 1 Deliverables (implemented in this update)
- **Runtime precheck script** (`scripts/runtime_precheck.py`) to flag missing tools, config, DB initialization, and port conflicts for backend (8080) and frontend (3000).
- **Configuration validation in precheck** to surface missing `SECRET_KEY` and `DATABASE_URL` values early.
- **Documentation alignment** so Quick Start and runtime expectations match the backend’s 8080 default.
- **Backend health endpoint** (`/health`) that reports configuration readiness, database connectivity, and timestamped status for monitoring.
- **Actionable runbook** in this file to guide developers from clone to first successful run.

## Phase 1 Runbook (execute in order)
1. Ensure Python 3.11+ and Node 20.x are installed; activate a virtualenv.
2. Copy `config.env` to `.env` (or provide equivalent values) and confirm secrets/DB URL.
3. Install backend deps: `pip install -r requirements.txt`.
4. Install frontend deps: `cd frontend && npm install`.
5. Initialize the database (SQLite default):
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```
6. Run the precheck: `python scripts/runtime_precheck.py`.
7. Start backend: `python main.py` (serves on http://localhost:8080 by default).
8. Start frontend: `cd frontend && npm run dev` (served on http://localhost:3000).
9. Point frontend API calls to `http://localhost:8080` (configure proxy/env in Phase 3).

## Next Steps
- Extend the precheck to validate DB migrations and API health once Flask-Migrate and health endpoints are added (Phase 2).
- Add a frontend `.env.local` template that injects the backend base URL for local development (Phase 3).
