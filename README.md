# DataLogicEngine

DataLogicEngine is a local-first AI orchestration application for chat, traceable runs, knowledge graph exploration, simulations, and operations visibility.

It runs in two modes:

1. Desktop mode (Windows Electron): no login required, boots directly to the internal dashboard.
2. Web mode (browser): session-based authentication for protected routes.

## Current Status (February 8, 2026)

The application is functional for local Windows use with API keys and internet access.

### Live

1. Core routing for dashboard, chat, projects, admin, settings, runs, simulations, graph.
2. Desktop no-login startup path.
3. Sidebar collapse/expand controls in app and settings navigation.
4. API key save/test workflow in settings.
5. AI model configuration and provider model testing in settings.
6. Storage health checks and local service lifecycle actions (`Start All`/`Stop All`/autostart toggle).
7. Installer build pipeline (`electron-builder`) with installer copied to repo root.

### Partial / In Progress

1. `Settings > Notifications` is still placeholder UI.
2. `Settings > Storage > Cloud Config` form fields are not fully wired to persistence.
3. MCP admin actions are partially available (`Add Server` and console actions are still disabled in UI).
4. Register page UI exists but registration submit flow is not yet wired.

## Quick Start (Windows 11)

### 1. Clone and install dependencies

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

### 2. Configure `.env`

Set at minimum:

1. `SESSION_SECRET` (long random value)
2. At least one provider key:
   `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `GEMINI_API_KEY`/`GOOGLE_API_KEY`

### 3. Start local stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

Default endpoints:

1. Frontend: `http://127.0.0.1:3000`
2. Backend health: `http://127.0.0.1:5000/health`

Stop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\stop_local_stack.ps1
```

## Optional Local Data Services

Run with PostgreSQL, Redis, Neo4j, and MinIO using Docker-backed local services:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1 -WithDataServices
```

Validate:

```powershell
.venv\Scripts\python.exe .\scripts\verify_api_keys.py
.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
```

## Desktop Installer

Build installer:

```powershell
npm --prefix frontend run electron:dist
```

Artifacts:

1. `DataLogicEngine Setup Latest.exe`
2. `DataLogicEngine Setup <version>.exe`
3. `frontend/dist/` (packaging output)

Run installer manually:

```powershell
.\DataLogicEngine Setup Latest.exe
```

## Architecture Summary

1. Frontend: Next.js App Router (`frontend/app`), Electron shell (`frontend/electron`).
2. Backend: Flask API + orchestration services (`app.py`, `backend/`, `routes/`).
3. Data plane: SQLite fallback by default, optional PostgreSQL/Redis/Neo4j/object/vector integrations.
4. AI providers: OpenAI, Anthropic, Google Gemini (plus configured provider adapters).

## Documentation

Primary docs:

1. `docs/README.md`
2. `docs/PRODUCT_OVERVIEW.md`
3. `docs/USER_GUIDE.md`
4. `docs/DEVELOPER_GUIDE.md`
5. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
6. `docs/DEPLOYMENT.md`
7. `docs/ARCHITECTURE.md`
8. `docs/SECURITY.md`
9. `docs/TESTING.md`

## Testing

Backend smoke check:

```powershell
python .\scripts\test_smoke.py
```

Backend:

```powershell
python run_test_suite.py
```

Frontend:

```powershell
cd frontend
npm test
```

E2E visual checks:

```powershell
cd frontend
npm run test:e2e:visual
```

## Contributing

See `CONTRIBUTING.md`.

## License

PolyForm Noncommercial License 1.0.0 (`LICENSE`).
