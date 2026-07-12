# DataLogicEngine First-Run QC Report

Date: 2026-07-07  
Scope: installed Windows desktop app left running by user, local backend, internal databases, backend/frontend connectivity, provider-key save failure investigation.

## Executive Summary

The installed app is running and the local backend is live on `127.0.0.1:5000`. Core local services are reachable: SQLite, Redis, Neo4j, MinIO, Chroma local storage, and local object-store buckets are present.

Two production-readiness issues were found during QC:

1. API-key save/test failures can occur when Electron sends a valid signed desktop request but the backend sees a stale Flask session cookie first and enforces session CSRF before desktop auth. Source fix implemented.
2. The floating Desktop Engine status panel was polling DSQP persona profiles every 5 seconds. That endpoint constructs DSQP profiles and can call the configured cloud LLM, which caused repeated OpenAI quota errors in the live logs. Source fix implemented.
3. The standard `npm --prefix frontend run electron:dist` build path could still reuse a stale PyInstaller backend, and the frozen backend was missing ONNX Runtime/tokenizers for Chroma collection-stat calls. Source/build fixes implemented.

The installed app inspected during QC had not been rebuilt with these fixes yet. The user has since stopped and uninstalled the app, so final UI validation should be performed against the next rebuilt installer rather than the old installation.

## Live Runtime State

| Check | Result |
| --- | --- |
| Desktop app process | Running from `C:\Program Files\DataLogicEngine Desktop\DataLogicEngine Desktop.exe` |
| Backend process | `DataLogic_Backend.exe` running |
| Backend listen port | `127.0.0.1:5000` |
| `/live` | 200, live |
| `/ready` | 200, ready |
| `/health` | 200, database `ok`, secret key set, Redis ping returned |
| `/health/cache` | 200, Redis `ok` |

## Local Services

| Service | Evidence | Status |
| --- | --- | --- |
| Redis | PING returned `+PONG` | OK |
| PostgreSQL container | TCP connect to `127.0.0.1:5432` | Listening |
| MinIO API | `/minio/health/live` returned HTTP 200 | OK |
| MinIO console | HTTP 200 on `127.0.0.1:9001` | OK |
| Neo4j Bolt | Connected to `bolt://127.0.0.1:7690`; query returned 20 nodes, 18 relationships | OK |
| Neo4j HTTP | HTTP 200 on `127.0.0.1:7476` | OK |

Running containers observed:

- `ukg-neo4j` on `7476/7690` - app-targeted Neo4j instance.
- `devonz-neo4j` on `7474/7687` - older/default Neo4j instance, not the app target.
- `devonz-db` on `5432`.
- `devonz-redis` on `6379`.
- `devonz-minio` on `9000/9001`.
- `devonz-redis-insight` on `8001`.

The duplicate Neo4j stack is not currently blocking the app because the runtime is pointed at `7476/7690`, but it should be cleaned up later if it is no longer needed.

## Internal Databases

| Store | Result |
| --- | --- |
| Runtime SQLite | Present at `%APPDATA%\DataLogicEngine Desktop\runtime\ukg_database.db`, 65 tables, 2.9 MB |
| SQLite notable rows | `users=3`, `audit_logs=11883`, `llm_providers=3`, most knowledge/chat/simulation tables empty |
| Chroma SQLite | Present, 21 tables, 4 collections, 0 embeddings |
| Object store | Buckets present: `audit_logs`, `deliverables`, `eval_data`, `graphs`, `simulation_artifacts` |
| Object-store content | `deliverables` has 8 files, 16,474 bytes; other buckets empty |
| Neo4j graph | 20 nodes, 18 relationships, labels include `Pillar`, `KnowledgeNode` |

Empty knowledge/chat/simulation/vector content appears consistent with first-run or lightly used local data, not a service failure.

## Findings And Corrections

### Fixed In Source: Desktop CSRF/Auth Ordering

Observed UI symptom: saving/testing the Google API key showed `CSRF session token missing` even though the UI reported the key as saved.

Root cause: signed Electron loopback requests were valid, but both the app-level API CSRF guard and route decorators preferred Flask session cookies first. If that cookie session had no matching `api_csrf_token`, the request failed before the desktop signature path could authenticate it.

Source changes:

- `app.py`: app-level API CSRF guard now accepts valid signed desktop auth before enforcing session-token CSRF.
- `backend/auth/api_decorators.py`: signed desktop auth is preferred over cookie session auth and cached on `g`.
- `frontend/lib/api/client.ts`: desktop mutations now establish/refresh the desktop session before CSRF token use and clear stale CSRF tokens after desktop login.
- Tests added/updated for stale-session desktop mutations and desktop CSRF refresh flow.

### Fixed In Source: Electron Header Declaration For Save Model

Observed after reinstall: the installed app first showed `Failed to save model configuration: CSRF session token missing`, then after the first partial repair showed `Failed to save model configuration: Session expired. Please re-authenticate.` when saving a pasted Google key through Settings -> AI Models.

Root cause: the Save Model button calls `/api/v1/gateway/keys`. Electron's main process injects signed `X-Desktop-Auth-*` headers through `webRequest.onBeforeSendHeaders`, but the renderer had not declared those header names before Chromium CORS/preflight handling. The first patch declared placeholders for normal `request()` mutations but missed the raw desktop challenge, desktop auto-login, and CSRF-token fetch calls used for session recovery. The backend then did not reliably receive a valid desktop-auth signature during save or recovery and either fell back to stale cookie-session CSRF or returned session-expired handling.

Source changes:

- `frontend/lib/api/client.ts`: Electron desktop requests now declare placeholder `X-Desktop-Auth-Timestamp`, `X-Desktop-Auth-Request-Signature`, and `X-Desktop-Auth-Signature` headers for normal mutations and for the raw desktop challenge, desktop auto-login, and CSRF-token fetch calls. The Electron main process replaces those placeholder values with real HMAC signatures before the request is sent.
- `frontend/tests/unit/lib/api/client.test.ts`: coverage now proves the normal mutation path and all desktop recovery handshake calls include the desktop auth header names.
- `tests/integration_routes/test_gateway_keys_desktop_auth.py`: coverage now proves `/api/v1/gateway/keys` accepts signed desktop requests both without a session and with a stale cookie session while CSRF enforcement is enabled.

### Fixed In Source: DSQP Status Polling

Observed live log symptom: repeated `GET /api/v1/gateway/dsqp-persona-profiles` calls and OpenAI 429 quota errors.

Root cause: `DesktopStatus` polled `electronApi.dsqpPersonaProfiles()` every 5 seconds. That endpoint constructs DSQP profiles and can call the configured cloud provider.

Source changes:

- `frontend/components/DesktopStatus.tsx`: removed automatic DSQP profile polling from the floating status widget.
- `frontend/components/DesktopStatus.test.tsx`: added coverage confirming DSQP profiles are not auto-loaded while status polling runs.

### Fixed In Build: Backend Rebuild, ONNX Runtime, And Tokenizers Packaging

Observed live log symptom: the installed backend reported `The onnxruntime python package is not installed`, then later `The tokenizers python package is not installed`, while gathering collection stats.

Root cause: the elevated `frontend/build_installer.ps1` wrapper rebuilt the PyInstaller backend, but the normal `npm --prefix frontend run electron:dist` command did not. The frozen backend could therefore be stale, and `backend.spec` did not explicitly collect ONNX Runtime/tokenizers package files and native DLLs.

Source/build changes:

- `frontend/scripts/build-backend-for-installer.ps1`: non-interactive backend rebuild helper for installer packaging.
- `frontend/package.json`: `electron:dist` now rebuilds the PyInstaller backend before Next/Electron packaging.
- `requirements.txt`: `onnxruntime==1.26.0` and `tokenizers` are explicit packaging dependencies.
- `backend.spec`: PyInstaller now collects ONNX Runtime and tokenizers binaries, data files, metadata, and hidden imports.

Validation evidence at this checkpoint: the rebuilt `dist\DataLogic_Backend` and `frontend\dist\win-unpacked\resources\backend` payloads contained ONNX Runtime and tokenizers native files and metadata.

Production correction (2026-07-11): the later `tokenizers==0.23.1` pin was incompatible with `transformers>=5.0.0` and blocked all clean dependency installs. The supported pin is now `tokenizers==0.22.2`; a fresh Python 3.11 PyInstaller bundle contains `onnxruntime-1.26.0.dist-info` and `tokenizers-0.22.2.dist-info`.

## Validation Completed

Commands passed:

- `python -m pytest tests\security\test_session_security.py tests\unit\test_auth_api_decorators_security.py tests\integration_routes\test_settings_routes_auth.py` - 14 passed.
- `npm run test -- tests/unit/lib/api/client.test.ts components/DesktopStatus.test.tsx` - 24 passed.
- `npm run typecheck` - passed.
- `npm run lint -- components/DesktopStatus.tsx components/DesktopStatus.test.tsx lib/api/client.ts tests/unit/lib/api/client.test.ts` - passed.
- `python -m ruff check app.py backend\auth\api_decorators.py tests\security\test_session_security.py` - passed.
- `python -m pytest tests\integration_routes\test_gateway_keys_desktop_auth.py tests\security\test_session_security.py tests\unit\test_auth_api_decorators_security.py tests\integration_routes\test_settings_routes_auth.py` - 16 passed after the Save Model endpoint patch.
- `npm --prefix frontend run test -- tests/unit/lib/api/client.test.ts` - 16 passed after the desktop auto-login/session-recovery header patch.
- `npm --prefix frontend run lint -- lib/api/client.ts tests/unit/lib/api/client.test.ts` - passed after the desktop auto-login/session-recovery header patch.
- `npm --prefix frontend run typecheck` - passed after the desktop auto-login/session-recovery header patch.
- `python -m ruff check app.py backend\auth\api_decorators.py tests\security\test_session_security.py tests\integration_routes\test_gateway_keys_desktop_auth.py scripts\build_backend.py` - passed after the desktop auto-login/session-recovery header patch.
- `npm --prefix frontend run electron:dist` - passed after wiring the backend rebuild helper into the standard installer build command and packaging ONNX Runtime/tokenizers.
- `python scripts\verify_installer_integrity.py --require-artifacts` - passed after the final rebuild.
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot "C:\software\DataLogicEngine"` - passed after the final rebuild.

## Rebuild Evidence

After the user stopped and uninstalled the old app, the installer was rebuilt from current source.

| Check | Result |
| --- | --- |
| Build command | `npm --prefix frontend run electron:dist` |
| Installer | `DataLogicEngine Setup Latest.exe` |
| SHA-256 | `3afeafef6991f580574290500c702429218c38c0c50dff4088716909661ff8cb` |
| Checksum sidecar | `DataLogicEngine Setup Latest.exe.sha256` matches the installer hash |
| Blockmap sidecar | Present |
| Installer integrity | Passed, report written to `reports/installer_integrity_report.json` |
| NSIS governance | Passed, report written to `reports/nsis_governance_report.json` |

The installer `.exe`, `.sha256`, `.blockmap`, and NSIS governance report are intentionally ignored local build artifacts. The tracked integrity report records the rebuilt installer hash.

## Outstanding Before Final Production Lock

1. Reinstall the rebuilt app so the installed binary includes these source fixes.
2. Re-test API key save and provider test flows in the installed UI for OpenAI, Google, and unsupported legacy Ollama status handling.
3. Confirm the rebuilt app no longer emits repeated DSQP/OpenAI quota errors while idle on the dashboard/status panel.
4. Decide whether to remove or stop the older `devonz-neo4j` container if it is not needed.
5. Keep provider validation separate from idle QC: OpenAI currently returns quota errors when called, so Google should be validated with the real key after reinstall without triggering OpenAI from status widgets.
