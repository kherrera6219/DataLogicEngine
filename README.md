# DataLogicEngine

DataLogicEngine is a local-first AI orchestration application for chat, traceable runs, knowledge graph exploration, simulations, and operations visibility.

It runs in two modes:

1. Desktop mode (Windows Electron): no login required, boots directly to the internal dashboard.
2. Web mode (browser): session-based authentication for protected routes.

## Current Status (February 17, 2026)

The application is functional for local Windows use with API keys and internet access.

### Live

1. Core routing for dashboard, chat, projects, admin, settings, runs, simulations, graph.
2. Desktop no-login startup path.
3. Sidebar collapse/expand controls in app and settings navigation.
4. API key save/test workflow in settings.
5. AI model configuration and provider model testing in settings.
6. Storage health checks and local service lifecycle actions (`Start All`/`Stop All`/autostart toggle).
7. Installer build pipeline (`electron-builder`) with installer copied to repo root.
8. MCP connector scope enforcement with user/tenant execution context propagation.
9. Connector latency/error telemetry exported to metrics and analytics surfaces.
10. SSRF protection on API gateway upstream forwarding and enterprise health probes.
11. CI/release gates for schema parity validation (`SQLite` vs `Postgres`) and installer checksum integrity.
12. Connector OAuth lifecycle handling and runtime input/output contract validation for Jira/Salesforce MCP tools.
13. AI latency percentile metrics (`p50`/`p95`/`p99`) exported in `/metrics` for alerting integration.
14. Deterministic startup precheck now enforced as CI/deploy release gate.
15. Diagnostic support-bundle generator for sanitized incident collection.
16. Snapshot and trace bundle HMAC integrity verification controls.
17. Crash reporting fallback IDs with pipeline probe checks.
18. Dedicated Windows installer code-signing workflow.
19. Database-level tenant isolation support for Postgres (RLS bootstrap + request-scoped tenant DB context).
20. Vault-aware secret resolution and production secure-source enforcement for runtime session secrets.
21. Signed/encrypted trace export envelopes for evidence packaging.
22. Immutable audit replica hash-chain append and verification controls.
23. AI and connector latency SLO baseline/violation gauges (`p95`/`p99`) exported in `/metrics`.
24. Desktop startup script now auto-resolves backend/frontend port conflicts by default.
25. Desktop install secret persistence now uses OS-protected encryption when available (`safeStorage`) with plaintext migration support.
26. Desktop runtime logs are persisted under user data with best-effort restricted local permissions.
27. Controlled auto-update policy is runtime gated (disabled by default unless explicitly enabled with feed URL).
28. NSIS governance checks and packaging smoke validations are automated for Windows CI.
29. Developer governance controls now include repository pre-commit hooks (`lint + typecheck`) and a CI governance gate.
30. Environment parity and lockfile integrity checks are enforced via `scripts/verify_environment_parity.py` and `scripts/verify_lockfiles.py`.
31. ADR baseline, release checklist workflow, and branch/code-owner governance policies are documented and versioned.
32. Python lint baseline is fully clean (`.venv\Scripts\python.exe -m ruff check .` passes).

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

Production supports vault-backed secret resolution alternatives:

1. `SESSION_SECRET_FILE=<path-to-secret-file>`
2. `SESSION_SECRET_DPAPI_B64=<dpapi-encrypted-secret>`
3. `DLE_SECRET_STORE_JSON=<path-to-json-secret-store>`
4. Optional strict controls: `PRODUCTION_VAULT_SECRETS_REQUIRED=true` and `ALLOW_PLAINTEXT_PROD_SECRETS=false`

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
3. `DataLogicEngine Setup Latest.exe.sha256`
4. `DataLogicEngine Setup <version>.exe.sha256`
5. `frontend/dist/` (packaging output)

Run installer manually:

```powershell
.\DataLogicEngine Setup Latest.exe
```

Silent install:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install_silent.ps1
```

Silent uninstall (preserve data):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall.ps1 -Silent -KeepData
```

Silent uninstall (delete data):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall.ps1 -Silent -DeleteData
```

Verify installer integrity:

```powershell
python .\scripts\verify_installer_integrity.py --require-artifacts
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts -CheckRevocation
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_signing_certificate_health.ps1 -CertificatePath .\codesign.pfx -CertificatePassword "<password>" -CheckRevocation
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -Mode portable
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
8. `docs/ARCHITECTURE_MAP.md`
9. `docs/SECURITY.md`
10. `docs/TESTING.md`
11. `docs/FILE_STRUCTURE.md`
12. `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`

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
npm run typecheck
npm test
```

E2E visual checks:

```powershell
cd frontend
npm run test:e2e:visual
```

Route E2E smoke:

```powershell
cd frontend
npm run test:e2e -- tests/e2e/route-sidebar-smoke.spec.ts
```

Operational hardening checks:

```powershell
python .\scripts\validate_schema_parity.py
python .\scripts\verify_installer_integrity.py --require-artifacts
python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process
python .\scripts\generate_support_bundle.py --skip-http
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1
```

## Contributing

See `CONTRIBUTING.md`.

## License

PolyForm Noncommercial License 1.0.0 (`LICENSE`).
