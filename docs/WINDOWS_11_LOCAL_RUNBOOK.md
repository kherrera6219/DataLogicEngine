# DataLogicEngine Windows 11 Local Runbook

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.8.0 |
| Last updated | 2026-07-13 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Purpose

Run, validate, package, troubleshoot, and recover DataLogicEngine as a local-first Windows 11 application.

This runbook reflects the current Windows/local-first architecture: Electron
frontend, an explicit Flask loopback application/runtime, desktop local auth,
installation ownership and readiness, app-owned storage services, local object/
vector/graph/memory stores, provider-key management, packaging smoke, NSIS
governance, and signed-release preparation.

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

Development/testing mode can explicitly use SQLite, memory, and filesystem
fallbacks. Production mode requires app-owned PostgreSQL, Redis, Neo4j,
ChromaDB, and MinIO and refuses fallback when any required service is absent.

---

## Current state

As of Phase 2 closure (2026-07-13):

1. `create_app()` produces isolated application instances; importing `app.py`
   performs no application construction or resource startup.
2. Startup is phased and protected by a per-user installation identity, version
   record, runtime-root ACL, and exclusive OS lock.
3. One app-owned supervisor publishes truthful per-service state and refuses to
   trust an unknown listener merely because a port is open.
4. `/live`, `/ready`, `/health`, authenticated capabilities, and signed desktop
   lifecycle events have distinct contracts with correlation IDs.
5. Electron waits for `/ready`, shows actual service/runtime degradation, and
   uses bounded graceful shutdown.
6. Production refuses SQLite fallback and automatic schema creation. Missing
   MinIO/Chroma or any other required service keeps production not ready.
7. The development launcher passes a real start/probe/stop cycle and leaves no
   backend/frontend listener after shutdown.
8. Full production container delivery, immutable service versions, unique
   protected service credentials, installation-specific ports, and real use of
   all five services remain Phase 3 release blockers.
9. Existing installer/signing evidence predates this runtime refactor and is not
   Phase 2 installed-production evidence; packaging qualification resumes in
   Phases 14-15.

---

## Prerequisites

Required:

1. Windows 11.
2. Python `3.11`.
3. Node.js `24`.
4. npm.
5. PowerShell.
6. Git.

Additional requirements by task:

1. Rootless Podman Machine/WSL2 for the approved production data-plane path
   (delivery qualification remains Phase 3).
2. Docker Desktop only for development compatibility/container-build checks.
3. Provider API key for model-backed testing.

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
   - `LLM_DEFAULT_PROVIDER=google` when both OpenAI and Google keys are present and Google should be the env fallback default

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

The launcher checks ownership before starting any service. If another product
owns a configured data port, startup fails with the process/container name and a
repair action. Do not stop an unrelated product automatically and do not point
DataLogicEngine at that listener. Installation-specific service ports are part
of Phase 3 provisioning.

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
| PostgreSQL | `5432` default | Phase 3 app-managed OCI service | runtime-root volume | production relational authority. |
| Redis | `6379` default | Phase 3 app-managed OCI service | runtime-root volume | production cache, session, rate-limit, queue, and stream service. |
| Neo4j | `7687` default | Phase 3 app-managed OCI service | runtime-root volume | production graph authority. |
| ChromaDB | app-owned | Phase 3 qualified local service/store | runtime-root volume | vector storage and semantic retrieval. |
| MinIO | `9000` default | Phase 3 app-managed OCI service | runtime-root volume | production object-store authority. |
| UnifiedMemory | portless | JSON persistence | `databases/memory/memory_graph.json` | structured reasoning memory graph. |

The ports above are defaults, not proof of ownership. The runtime trusts only
the installation identity and expected supervised process/container identity.
Filesystem object storage is a development/bootstrap path, not the production
MinIO substitute.

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
4. Authenticated metrics responds: `http://127.0.0.1:5000/metrics`
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
3. Development may use a runtime-root SQLite file; production uses the internal
   PostgreSQL authority and refuses SQLite.
4. For development only, a provider key may be supplied through `.env`.
   Production secrets must use the approved protected source.
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
7. Compare `/live` with `/ready`: a live process may correctly be not ready.
8. Inspect authenticated `/api/v1/system/capabilities` for the service state,
   safe reason, expected identity, and active lifecycle operation.
9. If `runtime_already_owned` appears, close the other DataLogicEngine process;
   do not delete the lock while that owner is alive.
10. If a foreign port owner is named, stop/configure that product or wait for
    Phase 3 installation-specific port provisioning; never reuse it.

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
6. The Phase 3 five-service OCI data plane is not yet delivered or qualified by
   the installer, so production/public release remains NO-GO.

---

## Change notes for v2.8.0

1. Replaced stale installed-runtime claims with the verified Phase 2 factory,
   ownership, phased startup, readiness, lifecycle, and shutdown contract.
2. Clarified the development fallback versus production five-service boundary
   and added foreign-port/runtime-lock repair guidance.

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
