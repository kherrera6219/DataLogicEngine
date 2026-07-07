# DataLogicEngine Windows 11 Local Runbook

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.7.1 |
| Last updated | 2026-07-07 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Purpose

Run, validate, package, troubleshoot, and recover DataLogicEngine as a local-first Windows 11 application.

This runbook reflects the current Windows/local-first architecture: Electron frontend, Flask loopback backend, desktop local auth, app-owned storage services, local object/vector/graph/memory stores, provider-key management, packaging smoke, NSIS governance, and signed-release preparation.

## Audience

1. Windows desktop maintainers
2. Platform engineers
3. QA/release engineers
4. Support operators
5. Technical reviewers validating local-first behavior

## Related documents

1. `docs/ARCHITECTURE.md`
2. `docs/DEPLOYMENT.md`
3. `docs/SECURITY.md`
4. `docs/DATABASE_SCHEMA.md`
5. `docs/TESTING.md`
6. `docs/PRODUCTION_READINESS.md`
7. `docs/RELEASE_CHECKLIST.md`
8. `docs/diagrams/06_local_first_security_model.md`
9. `docs/diagrams/07_data_storage_and_memory_architecture.md`

---

## Local-first goal

Run DataLogicEngine locally on Windows 11 with:

1. local frontend and backend runtime;
2. local/hybrid desktop session behavior;
3. app-owned internal storage services;
4. optional provider API keys for model-backed flows;
5. deterministic validation and packaging evidence;
6. no requirement for externally hosted runtime databases.

Default local mode can use SQLite/in-memory fallbacks. Full local data mode can use app-owned PostgreSQL, Redis, Neo4j, ChromaDB, object store, USKD graph, and local memory files.

---

## Current state

As of v2.7.1 (2026-07-07):

1. Local startup scripts are functional.
2. Core frontend routes are reachable.
3. Desktop mode supports no-login startup through desktop local-auth policy.
4. Settings API key save/test, AI model controls, and local storage lifecycle controls are wired.
5. Desktop installer builds from a freshly rebuilt PyInstaller backend and is copied to the repo root with checksum and blockmap sidecars.
6. Startup script auto-resolves backend/frontend port conflicts by default.
7. Desktop runtime stores install secret using OS-protected encryption when available and writes local runtime logs under user data.
8. Silent install and retention-aware silent uninstall controls are available for enterprise deployment patterns; installer-mode smoke validates install and uninstall exit code `0`.
9. Installer build rebuilds the PyInstaller backend before packaging so the shipped backend matches source.
10. Provider tests return specific failure reasons such as `invalid_api_key`, `rate_limited`, `invalid_model`, and `network_error`.
11. Latest local rebuild evidence records installer SHA-256 `7edb91c80f55b3aca25c0477c42aacb8a393d717cf930c062f849a945293c783` with installer integrity and NSIS governance passing; reinstall/provider QC is the next validation step.
12. First-run QC on 2026-07-07 confirmed the installed backend, health endpoints, Redis, Neo4j, MinIO, runtime SQLite, Chroma metadata, and local object-store directories were reachable.
13. Desktop API-key save/test requests now prefer signed Electron desktop auth over stale Flask session cookies, and desktop mutations refresh desktop session/CSRF state before save/test calls.
14. The floating desktop status widget no longer auto-polls DSQP persona profiles, preventing idle provider-backed DSQP calls while the app is merely open.
15. The `electron:dist` build command rebuilds the PyInstaller backend before Electron packaging, and the frozen backend includes ONNX Runtime for Chroma collection statistics.

---

## Prerequisites

Required:

1. Windows 11.
2. Python `3.11`.
3. Node.js `24`.
4. npm.
5. PowerShell.
6. Git.

Optional:

1. Docker Desktop for container/build verification.
2. Provider API key for model-backed testing.
3. Local portable database binaries for full data services.

---

## Initial setup

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

Copy-Item .env.template .env
```

Set in `.env`:

1. `SESSION_SECRET=<long_random_value>`
2. Optional provider key:
   - `OPENAI_API_KEY`
   - `GEMINI_API_KEY` / `GOOGLE_API_KEY`

Install frontend dependencies:

```powershell
cd frontend
npm ci
cd ..
```

Run readiness checks:

```powershell
.\.venv\Scripts\python.exe .\scripts\dev_doctor.py --skip-ports
python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process
python .\scripts\verify_lockfiles.py
python .\scripts\verify_environment_parity.py --strict
```

---

## Start and stop

### Fast local mode

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

### Disable port auto-resolution

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

### Stop app and data services

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\stop_local_stack.ps1 -WithDataServices
```

---

## Local data services architecture

The Windows local-first runtime uses app-owned/internal data services and local filesystem stores.

| Store | Default port | Mode | Directory path | Purpose |
|---|---:|---|---|---|
| PostgreSQL | `5432` | portable process where enabled | `databases/postgresql/` | structured system tables, traces, audit records. |
| Redis | `6379` | portable process where enabled | `databases/redis/` | cache, session/rate-limit support, queue/stream behavior. |
| Neo4j | `7687` | portable process where enabled | `databases/neo4j/` | graph relationships and graph query behavior. |
| ChromaDB | portless | embedded local client | `databases/chroma/` | vector storage and semantic retrieval. |
| Object store | portless | filesystem | `databases/objects/` | deliverables, audit logs, FROST snapshots, trace bundles, eval data. |
| UnifiedMemory | portless | JSON persistence | `databases/memory/memory_graph.json` | structured reasoning memory graph. |

Default object-store buckets:

```text
audit_logs
simulation_artifacts
deliverables
graphs
eval_data
```

### Prepare local databases

```powershell
python scripts/setup_local_databases.py --all
```

This prepares local PostgreSQL, Redis, Neo4j, and Java dependencies where supported by the setup script.

### Verify local databases

```powershell
python scripts/setup_local_databases.py --verify
```

### Validate local data plane

```powershell
.venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
python .\scripts\validate_schema_parity.py --report reports\schema_parity_report_local.json
```

---

## Desktop local-auth behavior

Desktop mode uses local/hybrid runtime policy rather than public cloud auth assumptions.

Current desktop local-auth controls:

1. loopback/Electron runtime detection;
2. per-install secret;
3. one-time nonce challenge;
4. nonce TTL;
5. HMAC-SHA256 challenge response;
6. per-request HMAC signature;
7. timestamp skew validation;
8. constant-time comparison;
9. DPAPI helper where available.

Troubleshooting desktop auth:

1. confirm runtime mode is local/hybrid;
2. confirm request is loopback/Electron;
3. confirm install secret exists;
4. check nonce expiry;
5. check timestamp skew;
6. check HMAC signature generation;
7. confirm cloud mode is not accidentally enabled.

Relevant files:

- `backend/security/desktop_local_auth.py`
- `backend/security/dpapi_store.py`
- `frontend/lib/runtime/policy.ts`
- `frontend/contexts/AuthContext.tsx`

---

## Validation checklist

1. Frontend responds: `http://127.0.0.1:3000`
2. Backend health responds: `http://127.0.0.1:5000/health`
3. Readiness responds: `http://127.0.0.1:5000/ready`
4. Metrics responds: `http://127.0.0.1:5000/metrics`
5. Provider key validates:
   ```powershell
   .venv\Scripts\python.exe .\scripts\verify_api_keys.py
   ```
6. Route policy smoke passes:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\windows\test_frontend_route_policy.ps1 -FrontendPort 3000
   ```
7. Local data stack validates:
   ```powershell
   .venv\Scripts\python.exe .\scripts\verify_local_data_stack.py
   ```
8. Runtime precheck passes:
   ```powershell
   python .\scripts\runtime_precheck.py --strict --skip-ports --allow-env-from-process
   ```
9. Schema parity passes:
   ```powershell
   python .\scripts\validate_schema_parity.py
   ```

---

## Desktop installer workflow

Build installer from source. The backend executable must be rebuilt before Electron packaging so the shipped backend matches the current Python source:

```powershell
.\.venv\Scripts\python.exe scripts\build_backend.py
$env:CSC_SKIP = "true"
npm --prefix frontend run electron:dist
```

Expected files:

1. `DataLogicEngine Setup Latest.exe`
2. `DataLogicEngine Setup Latest.exe.sha256`
3. `DataLogicEngine Setup Latest.exe.blockmap`
4. `frontend/dist/` packaged app artifacts
5. `dist/DataLogic_Backend/` PyInstaller backend bundle

Run manually:

```powershell
.\DataLogicEngine Setup Latest.exe
```

Silent install:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install_silent.ps1
```

Silent uninstall preserving data:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall.ps1 -Silent -KeepData
```

Silent uninstall deleting data:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\uninstall.ps1 -Silent -DeleteData
```

---

## Packaging smoke and governance

Run before release candidate approval:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
.\.venv\Scripts\python.exe scripts\verify_installer_integrity.py --require-artifacts
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
```

Run installer-mode smoke when validating install/uninstall behavior:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path -Mode installer
```

For signed production distribution, run the signing workflow and verify signature:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts -CheckRevocation
```

Local unsigned builds are valid for workstation validation, but they are not production release evidence. A local `NotSigned` status is expected unless a trusted production signing certificate is configured.

---

## Controlled auto-update policy

Auto-update is disabled by default.

Enable only with explicit feed policy:

```text
DLE_AUTO_UPDATE_ENABLED=true
DLE_AUTO_UPDATE_FEED_URL=<https://...>
```

Optional controls:

```text
DLE_AUTO_UPDATE_AUTO_DOWNLOAD=true|false
DLE_AUTO_UPDATE_AUTO_INSTALL_ON_QUIT=true|false
```

Do not enable auto-update for production without signed update artifacts and tested rollback behavior.

---

## Secure local log storage

Runtime logs:

```text
%APPDATA%\DataLogicEngine\logs\desktop-runtime.log
```

Installer-managed local data logs:

```text
C:\ProgramData\DataLogicEngine\logs
```

Logs should not include raw provider keys, plaintext secrets, unredacted PII, or private customer content.

---

## Optional WiX/WinSW packaging path

If using `deploy/windows/` manifests:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\prepare_wix_assets.ps1
```

This verifies:

1. `deploy/windows/winsw.exe` exists;
2. service wrappers are refreshed:
   - `deploy/windows/DataLogic_Backend.exe`
   - `deploy/windows/DataLogic_Frontend.exe`

Electron Builder/NSIS is the primary current packaging path. WiX/WinSW remains optional.

---

## Troubleshooting

### Chat fails with `No active providers found`

1. Open Settings -> AI Providers and confirm at least one provider is listed and active.
2. Confirm key was saved to the same database the running app uses.
3. Desktop uses the runtime-root SQLite file, not necessarily `instance/`.
4. As a fallback, set provider key in `.env`.
5. Re-run:
   ```powershell
   .venv\Scripts\python.exe .\scripts\verify_api_keys.py
   ```

### Settings page shows module/storage size error

This usually means a local storage backend is absent or disabled.

1. Rebuild the frontend.
2. Validate local data stack.
3. Confirm absent backends render as `0 B` / `Not created` rather than crashing.

### Electron Builder fails with npm/path errors

Run:

```powershell
cd frontend
npm run fix:eb
npm run electron:dist
cd ..
```

The repo includes a patch for NVM-for-Windows/npm wrapper path issues.

### Backend health fails

1. Check backend port.
2. Check `.env` and `SESSION_SECRET`.
3. Check database service startup.
4. Check `AUTO_CREATE_SCHEMA` is not set in unsafe mode.
5. Run runtime precheck.
6. Review local logs.

### Chroma/Object/Neo4j/local data store fails

1. Check local directory permissions.
2. Check antivirus/file locks.
3. Check `databases/chroma/`.
4. Check `databases/objects/`.
5. Check Neo4j process and port `7687`.
6. Run local data stack validation.
7. Run schema parity validation.

### Desktop auth fails

1. Confirm Electron/loopback runtime.
2. Confirm local/hybrid mode.
3. Check install secret.
4. Check nonce expiry.
5. Check timestamp skew.
6. Check HMAC signature.
7. Confirm cloud mode did not enable desktop trust.

---

## Known limitations

1. Manual application-readiness evidence remains open for NVDA validation; automated WCAG, keyboard navigation, failure-mode, and export/delete evidence is tracked in `reports/app-readiness/`.
2. Register submit flow is intentionally disabled in the current local-first build; `/register` redirects to `/dashboard`.
3. Release builds require trusted production certificate provisioned in GitHub secrets and signed release workflow run before public distribution.
4. Provider-backed flows require valid provider credentials and network access.
5. Unsigned local builds are suitable for developer validation but not public/customer release.

---

## Change notes for v2.7.0

1. Updated version/date for the July 2026 desktop rebuild documentation refresh.
2. Made the full backend-before-Electron installer rebuild order explicit.
3. Added installer integrity, portable packaging smoke, and installer-mode install/uninstall smoke commands.
4. Removed Anthropic from the provider-key setup list because the current supported user-facing model choices are OpenAI and Google/Gemini.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Updated the runbook around the current local-first Windows architecture.
3. Added desktop local-auth behavior and troubleshooting.
4. Added current local data services, object/vector/graph/memory architecture.
5. Added packaging smoke, NSIS governance, signed-release verification, and auto-update policy guidance.
6. Expanded validation checklist and troubleshooting sections.
