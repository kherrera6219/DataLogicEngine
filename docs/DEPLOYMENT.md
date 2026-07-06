# Deployment Guide

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.8.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Platform Operations |
| Review cadence | Every 30 days |

## Purpose

Define supported deployment modes, packaging procedures, release gates, runtime guardrails, and required CI/CD configuration for DataLogicEngine.

This version reflects the current local-first architecture: Electron/Windows desktop, Windows VM using the same internal stack, canonical web/cloud deployment where configured, app-owned internal storage services, deterministic preflight validation, packaging smoke tests, and release-governed promotion.

## Audience

1. Release engineers
2. Platform engineers
3. SRE/operations
4. Desktop packaging maintainers
5. Security reviewers
6. Technical judges validating deployment maturity

## Related documents

1. `docs/PRODUCTION_READINESS.md`
2. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
3. `docs/RELEASE_CHECKLIST.md`
4. `docs/TESTING.md`
5. `docs/API.md`
6. `.github/workflows/ci.yml`
7. `.github/workflows/deploy.yml`
8. `docs/diagrams/06_local_first_security_model.md`
9. `docs/diagrams/08_testing_validation_and_release_governance.md`

## Supported deployment targets

DataLogicEngine currently supports three deployment targets:

| Target | Status | Description |
|---|---|---|
| Windows desktop / Electron | Primary | Local-first app shell with Flask backend and app-owned internal storage services. |
| Windows VM | Supported | Same Windows app stack installed inside a VM; not a managed-cloud database mode. |
| Web/cloud deployment | Controlled / optional | Flask/Next.js deployment path where configured; canonical `/api/v1/*` APIs, stricter host/CORS/HTTPS/session rules. |

Unsupported as primary runtime database sources:

- externally hosted PostgreSQL as the primary application database;
- externally hosted Redis as the primary runtime cache/session store;
- Neo4j Aura or external Neo4j as the default app graph store;
- hosted vector databases as the primary vector store;
- S3/Azure/GCS buckets as the primary object store.

The current `ConnectionManager` treats `local`, `vm`, and `auto` as supported storage modes and deprecates cloud/hybrid database mode in favor of app-owned internal services.

## Deployment guardrails

Before promoting any build:

1. Run runtime preflight validation:
   ```powershell
   python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
   ```
2. Validate lockfile governance:
   ```powershell
   python scripts/verify_lockfiles.py
   ```
3. Validate environment parity:
   ```powershell
   python scripts/verify_environment_parity.py --strict
   ```
4. Validate documentation references:
   ```powershell
   python scripts/verify_docs_references.py
   ```
5. Validate schema parity:
   ```powershell
   python scripts/validate_schema_parity.py
   ```
6. Run the relevant test suites from `docs/TESTING.md`.
7. Confirm release gates in `docs/RELEASE_CHECKLIST.md`.
8. Never enable `AUTO_CREATE_SCHEMA=true` in production. It is a disposable local-only escape hatch.
9. Apply database migrations before backend startup when running against migration-managed SQL storage:
   ```powershell
   flask db upgrade
   ```

## 1. Windows desktop deployment

The desktop build uses Electron and a local-first runtime model. The frontend can be built for Electron static export, while the backend runs as a local Flask service with app-owned storage services.

### Build command

Use the CI-equivalent order so the installer embeds the current backend source:

```powershell
.\.venv\Scripts\python.exe scripts\build_backend.py
$env:CSC_SKIP = "true"
npm --prefix frontend run electron:dist
```

The CI Windows packaging job follows the same dependency order: build the backend executable first, then produce the Electron/NSIS distribution.

Release-candidate verification should then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
.\.venv\Scripts\python.exe scripts\verify_installer_integrity.py --require-artifacts
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path -Mode installer
```

### Expected outputs

Typical desktop outputs include:

- `frontend/dist/` packaged app output;
- repo-root installer copy such as `DataLogicEngine Setup Latest.exe` where configured by packaging scripts;
- matching integrity sidecars such as `.sha256` and `.blockmap` where generated;
- packaging smoke reports under `reports/`;
- installer integrity and signature reports under `reports/` where verification is run.

### Manual installer run

```powershell
.\DataLogicEngine Setup Latest.exe
```

### Desktop runtime behavior

The desktop target uses:

1. Electron renderer.
2. Flask backend on loopback.
3. Runtime policy for desktop session flow.
4. Desktop local auth with per-install secret, nonce challenge, HMAC signatures, timestamp skew validation, and loopback/Electron policy checks.
5. App-owned storage services and local filesystem paths.
6. Windows DPAPI helper for protected local data where available.
7. Object-store trace/export artifacts under app-owned local directories.

Relevant implementation:

- `frontend/electron/main.ts`
- `frontend/electron/preload.ts`
- `frontend/lib/runtime/policy.ts`
- `frontend/contexts/AuthContext.tsx`
- `backend/security/desktop_local_auth.py`
- `backend/security/dpapi_store.py`

### Desktop PostgreSQL authentication

The bundled portable PostgreSQL path may initialize with `--auth=scram-sha-256`. A random superuser password is generated on first launch and stored at:

```text
<install-root>/databases/postgresql/.pg_local_pw
```

Do not delete this file. It is required to reconnect to the local database. Restrict access using local filesystem permissions/ACLs.

### Local object, vector, and memory paths

Default local storage paths include:

```text
./databases/chroma
./databases/objects
./databases/memory/memory_graph.json
```

Object-store buckets initialized by the app include:

```text
audit_logs
simulation_artifacts
deliverables
graphs
eval_data
```

## 2. Windows VM deployment

The Windows VM target installs and runs the same app package used by the desktop target. It is not a switch to managed cloud databases.

PostgreSQL/SQLite, Redis, Neo4j, ChromaDB, object storage, and memory graph files remain app-owned/internal services on the VM filesystem and loopback network.

### VM setup

1. Provision a Windows VM with the same OS prerequisites as the Windows desktop target.
2. Install the signed app package or current installer artifact.
3. Let the application initialize internal database services under app-owned data directories.
4. Validate runtime health through `/health`, `/ready`, `/metrics`, and desktop database status paths where available.
5. Confirm logs and artifacts are stored in expected local/VM directories.
6. Run a packaging smoke or startup smoke check after installation.

### Unsupported VM shortcuts

Do not treat the VM target as permission to substitute managed cloud services for the internal runtime data layer unless a future architecture revision explicitly supports it.

Unsupported by default:

- managed PostgreSQL or external `DATABASE_URL` as primary application DB;
- managed Redis or external `REDIS_URL` as primary session/cache/queue service;
- Neo4j Aura or external `NEO4J_URI` as default graph store;
- hosted vector databases as primary vector store;
- S3/Azure/GCS as primary object store.

## 3. Controlled web/cloud deployment

A web/cloud deployment is possible where configured, but it has a different trust boundary than desktop/local mode.

Web/cloud requirements:

1. Strong `SESSION_SECRET` and production secrets.
2. Trusted host configuration.
3. HTTPS enforcement.
4. CORS allowlist with no production wildcard.
5. CSRF origin/token validation.
6. Secure cookies.
7. Rate limiting backed by the configured store.
8. No desktop loopback trust assumption.
9. Explicit database/storage architecture approval.
10. Contract, parity, security, and readiness checks passing in CI.

Cloud deployments should use canonical `/api/v1/*` routes and avoid relying on desktop-only auth shortcuts.

## 4. CI/CD deployment workflow

The CI workflow validates the app before deploy promotion.

Important CI jobs:

| Job | Purpose |
|---|---|
| `lint` | Ruff lint safety gate. |
| `backend-test` | Backend dependency install, `pip-audit`, smoke check, runtime precheck, docs references, schema parity, pytest, contract tests, parity tests, security tests. |
| `frontend-build` | Node 24, npm install, design tokens, lint, typecheck, Vitest, Next build, Playwright, a11y, visual regression. |
| `windows-packaging-smoke` | PyInstaller backend build, Electron dist, NSIS governance, installer integrity, portable launch smoke, report upload. |
| `governance` | Pre-commit governance, environment parity, lockfile governance. |
| `docker-build` | Backend and frontend Docker build verification. |

Deployment workflow may build container artifacts for CI compatibility. Container image build verification does not change the default runtime policy: application database services remain internal for the Windows desktop/VM targets.

## 5. GitHub Container Registry artifacts

The deploy workflow may publish images to GitHub Container Registry when configured.

- Image build: always runs where configured.
- Image push to `ghcr.io/<owner>/datalogicengine`: runs only when `GHCR_PAT` is configured.
- If `GHCR_PAT` is missing, build still succeeds and push is skipped by design.

### Configure `GHCR_PAT`

1. Create a GitHub Personal Access Token classic for the account/org that owns the package.
2. Grant scopes:
   - `write:packages`
   - `read:packages`
   - `delete:packages` only if cleanup is needed.
3. Add repository secret:
   - Repository `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`
   - Name: `GHCR_PAT`
   - Value: token value.

### Expected image tags

The workflow may publish tags through `docker/metadata-action`:

- branch ref tags;
- semver tags when pushing version tags;
- commit SHA tags.

## 6. Production deploy variables

`deploy-production` uses a hard gate and fails if required configuration is missing.

Required:

- `DEPLOY_COMMAND`
  - Shell command executed in the deploy job.
  - Example: `./deploy/deploy_production.sh`

Recommended:

- `PRODUCTION_HEALTHCHECK_URL`
  - URL checked after deployment for readiness.
  - Example: `https://datalogicengine.com/health`

### Configure repository variables

1. Open repository `Settings` -> `Secrets and variables` -> `Actions` -> `Variables`.
2. Create `DEPLOY_COMMAND` with the production deploy command.
3. Create `PRODUCTION_HEALTHCHECK_URL` if a production endpoint exists.

### Verify deployment workflow configuration

1. Open `Actions` -> `Deploy` -> `Run workflow`.
2. Run once with `deploy_production=false` to verify build/test/image stages.
3. Run again with `deploy_production=true`:
   - if `DEPLOY_COMMAND` is missing, `Deployment Config Gate` fails with actionable errors;
   - if configured, deployment runs and health check executes when `PRODUCTION_HEALTHCHECK_URL` is set.

## 7. Optional WiX/WinSW path

Electron Builder with NSIS is the current primary Windows packaging path. WiX/WinSW assets remain available for service-style packaging workflows.

If using the WiX manifests under `deploy/windows/`, prepare assets first:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\prepare_wix_assets.ps1
```

This fetches `deploy/windows/winsw.exe`, validates expected backend/frontend WiX inputs, and generates service wrapper artifacts such as:

- `deploy/windows/DataLogic_Backend.exe`
- `deploy/windows/DataLogic_Frontend.exe`

Before release, also run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
```

## 8. Performance and diagnostics

### Frontend bundle analysis

```powershell
$env:ANALYZE="true"; npm --prefix frontend run build
```

Reports are saved to:

```text
frontend/.next/analyze/{client,edge,nodejs}.html
```

### Backend profiling

```powershell
python scripts/profile_simulation.py
```

Generates:

```text
simulation_profile.html
```

### Runtime precheck JSON report

```powershell
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process --json-report reports/runtime_precheck_report_local.json
```

### Environment parity report

```powershell
python scripts/verify_environment_parity.py --strict --json-report reports/environment_parity_report_local.json
```

## 9. Deployment readiness checklist

Before release, confirm:

1. `docs/API.md`, `docs/ARCHITECTURE.md`, and this guide have current version/date metadata.
2. `scripts/runtime_precheck.py --strict` passes.
3. `scripts/verify_docs_references.py` passes.
4. `scripts/verify_lockfiles.py` passes.
5. `scripts/verify_environment_parity.py --strict` passes.
6. Schema parity validation passes.
7. Backend tests pass.
8. Frontend lint, typecheck, tests, and build pass.
9. Contract, parity, and security sweeps pass.
10. Windows packaging smoke passes for desktop release.
11. NSIS governance passes for installer release.
12. Installer integrity verification passes for root installer artifacts.
13. Installer-mode install/uninstall smoke passes where release scope requires install behavior evidence.
14. Docker image build verification passes where applicable.
15. `/health`, `/live`, `/ready`, and `/metrics` respond correctly in the target runtime.
16. `AUTO_CREATE_SCHEMA` is not enabled in production.
17. Production secrets are not defaults.
18. Desktop-only auth is not exposed as cloud trust.

## 10. Troubleshooting

### Static worker exited

Usually occurs in static export mode if a page crashes during rendering.

Check:

```text
build_error.log
frontend build output
Next.js route rendering logs
```

### Rewrite issues

Next.js rewrites are web/standalone behavior. Desktop/Electron mode communicates through direct backend endpoints or Electron-specific runtime paths.

### Health check fails after install

Check:

1. backend process status;
2. local database service initialization;
3. `.pg_local_pw` presence for bundled PostgreSQL;
4. loopback port binding;
5. firewall/Defender blocking;
6. `SESSION_SECRET` and runtime env values;
7. `reports/runtime_precheck_report_*.json` where generated.

### Desktop auth fails

Check:

1. Electron runtime detection;
2. loopback host;
3. desktop install secret file;
4. nonce expiry;
5. timestamp skew;
6. HMAC signature generation;
7. cloud mode accidentally enabled.

### Object/vector store fails

Check:

1. local directory permissions;
2. `./databases/chroma` availability;
3. `./databases/objects` availability;
4. object bucket/key path traversal rejection;
5. antivirus or filesystem lock contention.

## Change notes for v2.8.0

1. Added release-candidate verification commands for NSIS governance, installer integrity, portable smoke, and installer-mode install/uninstall smoke.
2. Updated CI job and readiness checklist wording for installer integrity and install behavior evidence.

## Change notes for v2.7.0

1. Updated version/date for the July 2026 rebuild documentation refresh.
2. Corrected the Windows desktop build procedure to rebuild the PyInstaller backend before Electron/NSIS packaging.
3. Added installer integrity/signature report outputs to the expected desktop artifacts.

## Change notes for v2.6.0

1. Added document metadata with version and update date.
2. Reframed deployment around current local-first desktop, Windows VM, and controlled web/cloud deployment targets.
3. Updated internal storage policy to match `ConnectionManager` local/VM/auto behavior.
4. Added desktop runtime/auth behavior tied to current implementation files.
5. Added CI job breakdown matching the current workflow gates.
6. Added packaging smoke and NSIS governance release checks.
7. Added deployment readiness checklist.
8. Added troubleshooting for desktop auth, health checks, and local object/vector store issues.
