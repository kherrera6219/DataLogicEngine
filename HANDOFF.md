## Session Update: July 2, 2026 (Part 2 - LlamaIndex Cache Fix)

### Completed Work
- **Fixed `[WinError 5] Access is denied` on Knowledge Base Page**: Discovered that LlamaIndex and HuggingFace models were attempting to write their caches directly into the read-only `C:\Program Files` directory where the backend was bundled (`_internal`). 
- **Electron Cache Variable Injection**: Updated `main.ts` in Electron to inject `LLAMA_INDEX_CACHE_DIR`, `HF_HOME`, and `TRANSFORMERS_CACHE` environment variables into the backend. These now explicitly point to `%APPDATA%\DataLogicEngine Desktop\runtime\cache`, preventing permission errors and restoring functionality to the `/api/v1/gateway/chat` and RAG Knowledge Base endpoints.
- **Installer Rebuilt**: Successfully packaged these cache directory fixes into `DataLogicEngine Setup Latest.exe`.

## Session Update: July 2, 2026 (LLM Failover & API Key Fix)

### Completed Work
- **Database Priorities Adjusted**: Fixed the production SQLite DB (`ukg_database.db`) so OpenAI and Google are priorities 1 and 2, while Ollama is pushed to priority 10 and no longer set as default.
- **Model Configured**: Updated Google model string in DB to `gemini-3.1-pro-preview`.
- **API Key Fallback fixed**: The installed app now properly reads environment variables from the `.env` file since encrypted keys generated in dev could not be decrypted in production.
- **.env Propagation**: Modified the Electron app (`main.ts`) to read the `.env` file from the runtime directory (`%APPDATA%\DataLogicEngine Desktop\runtime`).
- **Template Generation**: Added logic to create a template `.env` file in the runtime directory on first launch so users know where to put their keys.
- **Immediate Testing Fix**: Copied the existing `.env` file into the local runtime directory for immediate testing.
- **Installer Rebuilt**: Successfully packaged these fixes into `DataLogicEngine Setup Latest.exe`.

# DataLogicEngine — Session Handoff

## START HERE (next session) - updated 2026-07-08
**Current next session priority: remediate 8 open GitHub CodeQL code-scanning alerts for `py/stack-trace-exposure` before the final production rebuild/install validation. Dependabot is clean with 0 open alerts.**

- **Open code-scanning alerts:** GitHub CodeQL currently reports 8 open medium alerts, all `py/stack-trace-exposure`: #593-#596 in `backend/routes/search_routes.py`, #598 in `backend/routes/retention_routes.py`, #599 in `backend/security_api.py`, and #600-#601 in `backend/routes/storage_routes.py`. Evidence is recorded in `reports/code_scanning_alerts_2026-07-08.md`.
- **Recommended next-session fix pattern:** replace public `str(exc)`, traceback, or exception-detail responses with stable generic JSON messages; keep details in server logs only; add focused route regressions for each touched endpoint; run Ruff and focused pytest before commit.
- **Dependabot alert sweep:** GitHub returned 0 open Dependabot alerts. The remaining 5 dismissed `fix_started` alerts were historical `uv.lock` transitive pins; `uv.lock` now resolves `mako 1.3.12`, `urllib3 2.7.0`, and `werkzeug 3.1.8`. Evidence is recorded in `reports/dependabot_alerts_2026-07-07.md`.
- **First-run QC checkpoint:** desktop API-key save/test CSRF repair, Electron desktop auth header declaration for session recovery, stale-backend rebuild protection, frozen-backend ONNX Runtime/tokenizers packaging, and idle DSQP status-polling repair are fixed in source and rebuilt into a local installer. Reinstall the app before validating the installed binary again.
- **Installed-app first-run QC report added:** `reports/first_run_qc_2026-07-07.md` records backend/service/database health, SQLite/Chroma/object-store/Neo4j/Redis/MinIO checks, the API-key save/test failure investigation, DSQP idle-polling diagnosis, source corrections, validation, and remaining reinstall-provider checks.
- **Desktop API-key save/test CSRF repair:** signed Electron loopback requests now win over stale Flask session cookies in both the app-level API CSRF guard and `api_decorators`; frontend desktop mutations now establish/refresh desktop session and CSRF state before save/test calls and recover cleanly on CSRF 403s.
- **Second installed-app Save Model/session-recovery repair:** the Save Model path uses `/api/v1/gateway/keys`. After reinstall it still reached session CSRF/session-expired handling because Electron-injected desktop HMAC headers were not reliably part of the renderer-declared CORS/preflight header set, including the raw desktop challenge, auto-login, and CSRF-token calls used during recovery. `frontend/lib/api/client.ts` now declares placeholder `X-Desktop-Auth-*` headers for those Electron desktop requests, and Electron main replaces them with real HMAC signatures before send.
- **Packaging repair:** `npm --prefix frontend run electron:dist` now rebuilds the PyInstaller backend before Electron packaging. The frozen backend also explicitly includes `onnxruntime`, `tokenizers`, and their native files after live logs showed Chroma collection-stat dependency errors in the installed backend.
- **Idle DSQP status-polling repair:** `DesktopStatus` no longer calls `electronApi.dsqpPersonaProfiles()` during its 5-second status loop, so idle dashboard/status use should not trigger provider-backed DSQP construction or repeated OpenAI quota errors.
- **Validation completed for this checkpoint:** backend gateway/auth/settings pytest passed 16 tests, frontend API Vitest passed 16 tests, frontend typecheck passed, focused frontend lint passed, focused Ruff passed, and the full installer rebuild path passed after rebuilding the backend.
- **Installer rebuilt:** `DataLogicEngine Setup Latest.exe` was rebuilt from current source with SHA-256 `3afeafef6991f580574290500c702429218c38c0c50dff4088716909661ff8cb`; installer integrity passed and NSIS governance passed.
- **After CodeQL remediation:** reinstall the rebuilt installer, then validate provider save/test behavior for OpenAI and Google plus unsupported legacy-provider status handling.

**Previous audit checkpoint: documentation slice, code audit slices 1-12, cleanup approval, and selected CodeQL alert remediation are complete.**

- **Documentation audit slice complete:** root maintained docs and the active `docs/` tree were read against live code. Active docs now align to desktop auth, current gateway/API surfaces, and the live Google default `gemini-3.1-pro-preview`. `docs/openapi.yaml` was replaced with a current partial contract. Legacy duplicate exports were moved from `docs/api/` to `docs/archive/api/`.
- **Cleanup completed:** root scratch-output files such as `.gitout.txt`, `audit_deep*.txt`, `audit_dup*.txt`, `core_backend_inversions*.txt`, `enc_*.txt`, `commit_msg.txt`, and `orphaned_modules.txt` were deleted after user approval. Orphan scanner code candidates remain confirm-before-cut and were not removed.
- **Code audit slice 1 complete - LLM provider/model configuration:** `ApiOverlayConfig` no longer offers retired `gemini-3.5-flash`; `/api/v1/gateway/keys` now normalizes provider/key/model input and rejects unsupported provider types before database writes; LLM-path comments/docstrings were corrected to `gemini-3.1-pro-preview` or current model constants.
- **Commit checkpoint:** documentation audit and code audit slice 1 were published to `origin/main` in commit `7be99dc8` before continuing.
- **Code audit slice 2 complete - authentication/session/CSRF/settings authorization:** `/api/v1/settings/ai` now uses `api_session_login_required`, reads the authenticated user through `g.auth_user`/`current_user`, accepts signed desktop requests without a pre-existing Flask session, and returns JSON 401s for unauthenticated calls. Settings preference writes now canonicalize providers, restrict AI preference providers to `auto`/`openai`/`google`, validate models against current defaults, and clear model preference when provider is `auto`.
- **CSRF coverage added:** backend regressions now prove untrusted session-cookie mutations are blocked, strict token enforcement rejects missing tokens, and valid Electron `app://-` CSRF-token mutations pass.
- **Code audit slice 3 complete - API route decorator/session/API-key boundaries:** search, user-data, notification, operational admin, feature-flag, MCP, and LLM admin routes were audited for raw Flask-Login JSON API drift. Session-only desktop routes now use `api_session_login_required` and return JSON 401s. MCP admin routes no longer stack raw `@login_required` ahead of `api_admin_required`, and MCP tool execution now builds connector-scope context from the resolved authenticated principal so ExternalAPIKey users are visible.
- **Slice 3 regressions added:** tightened JSON unauthenticated assertions for user-data/search/notification/admin/feature-flag/LLM-admin routes, added a route-level MCP ExternalAPIKey regression for `/api/v1/mcp/clients`, and added unit coverage for `get_authenticated_principal()` plus MCP API-key tool context.
- **Code audit slice 4 complete - dead KA route module and stale Flask page routes:** `backend/api/ka_management.py` was confirmed unregistered and duplicate of the live `backend/routes/ka_routes.py` API, then removed with its synthetic-only test coverage. The remaining app-level raw Flask-Login decorators were broken server-rendered `/chat` and `/knowledge-graph` routes pointing at missing Jinja templates, so they were removed; Electron/Next owns those UI surfaces.
- **Slice 4 regressions added:** live KA route tests now prove `/api/v1/ka` and legacy `/api/ka` are registered through the active blueprint, unauthenticated KA list returns JSON 401, KA health remains public, and ExternalAPIKey access reaches the real KA list route. App route wiring now proves Flask does not register stale `/chat` or `/knowledge-graph` template pages.
- **Code audit slice 5 complete - live KA API behavior/data-contract correctness:** `backend/routes/ka_routes.py` now resolves API-key/session/desktop principals through the shared auth helper for execution/workflow logging, accepts the documented `data`/`context` execute payload while keeping `input` preferred, clamps algorithm pagination, falls back to KA id/name-safe metadata for sparse registry entries, validates batch request shapes, tolerates non-numeric layer names, and uses the real TruthCore accessor from `backend.truth_engine.api`.
- **Slice 5 regressions added:** focused KA route tests now prove invalid pagination does not 500, sparse KA metadata returns a frontend-safe name, API-key execute and batch calls work with the documented payload, malformed execute/batch/workflow bodies return JSON 400s, high-stakes workflow awaits TruthCore async methods through the sync route bridge, trace routes use the real TruthCore accessor, layers accepts non-`L<number>` labels, and legacy `/api/ka` emits deprecation/successor headers.
- **Code audit slice 6 complete - KA execution persistence/history correctness:** `/api/v1/ka/history` now serializes persisted `KAExecution` rows into the frontend tool-history contract with canonical KA ids/names, normalized risk/status values, clamped limits, and trace-run links only when `run_id`/`trace_run_id` exists in the persisted payload. `/api/v1/trace/ka-execution-feed` tolerates malformed limits.
- **Slice 6 DB-manager repair:** `backend/ukg_db.py` no longer writes removed `KAExecution` columns; it writes the current schema, flushes auto-created catalog rows before FK-dependent execution rows, preserves legacy `session_id` in `input_data`, and implements the missing `get_ka_executions()` used by `KAEngine.get_execution_history()`.
- **Slice 6 regressions added:** persisted history route tests cover frontend-safe records, lowercase KA id normalization, trace-run extraction, no false trace links, and invalid limits; DB-manager unit tests cover current-schema writes and readback dictionaries.
- **Code audit slice 7 complete - KA execution frontend/desktop IPC consumers:** `LiveTracePanel` now loads live progress and `/trace/ka-execution-feed` independently of trace-run list state, keeps stage loading dependent on the selected run, and renders the KA execution feed outside the current-run branch so persisted KA activity remains visible even before any trace run exists. Tool history now uses shared nullable response types and safe timestamp/duration/name/run-link fallbacks.
- **Slice 7 frontend contract cleanup:** shared `KAExecutionFeed` and tool-history response types now live in `frontend/lib/api/types.ts`; `frontend/types/electron.d.ts` reuses the shared feed type while Electron `main.ts`/`preload.ts` were verified already signed/allowlisted for `ka-execution-feed`.
- **Slice 7 regressions added:** `LiveTracePanel.test.tsx` covers KA feed rendering with zero trace runs, and `frontend/app/tools/history/page.test.tsx` covers nullable persisted execution rows plus trace-run links.
- **Code audit slice 8 complete - trace run viewer/list/export contracts:** `GET /api/v1/trace/runs` now clamps pagination, the frontend trace client encodes run ids and returns typed list/bundle/subresource responses, and Trace Explorer list/detail pages render nullable trace rows, pass/fail status vocabulary, malformed coordinate vectors, missing persona drafts, and export/load failures without crashing or showing invalid dates.
- **Slice 8 regressions added:** `tests/unit/test_trace_viewer_contract.py` covers bounded trace-run pagination; `frontend/tests/unit/lib/api/trace.test.ts` covers encoded run ids and bounded limits; `frontend/app/runs/page.test.tsx` and `frontend/app/runs/view/page.test.tsx` cover nullable rows, malformed bundles, visible load errors, persona fallbacks, and coordinate fallbacks.
- **Code audit slice 9 complete - trace export persistence/history lifecycle:** `POST /api/v1/trace/runs/<run_id>/export` now persists a `TraceExport` row with status, download URL, manifest hash, file size, export options, signature/encryption flags, and the protected payload. `/api/v1/trace/exports` now lists real exports, `/api/v1/trace/exports/<export_id>/download` streams the stored protected export document, and non-object export options no longer raise.
- **Slice 9 schema/test coverage added:** `TraceExport` now defines the fields and serializer read by the active API, migration `e7f8a9b0c1d2_harden_trace_export_records.py` upgrades existing local databases, `docs/DATABASE_SCHEMA.md` reflects the live table, and `tests/unit/test_trace_export_lifecycle.py` covers export history/download plus malformed option bodies.
- **Code audit slice 10 complete - gateway trace creation and DMRF/chat persistence:** successful gateway responses now call `_create_trace_run()` before returning, so direct LLM calls, quad responses, and UKG overlay responses have a resolvable `TraceRun` behind the `audit_trail` URLs. `_create_trace_run()` is now an upsert, tolerates anonymous users and non-UUID optional session ids, avoids duplicate stages, and carries DMRF tier/FROST/truth-engine metadata into the trace audit bundle.
- **Slice 10 regressions added:** `tests/integration/test_llm_gateway_integration.py` now covers direct-call trace persistence and anonymous DMRF-enriched trace creation; existing trace viewer and DMRF integration coverage was rerun with workspace-local temp paths.
- **Code audit slice 11 complete - gateway failure, streaming, and offline replay trace lifecycle:** failed gateway responses now persist a failed `TraceRun` before returning, including governance blocks, DMRF blocks, no-provider failures, provider exhaustion, and user-preference blocks. Failed chat/rate-limit/queued-offline payloads, SSE terminal/error events, and offline replay success/failure records now include `audit_trail` links for the returned `run_id`.
- **Slice 11 regressions added:** `tests/integration/test_llm_gateway_integration.py` covers failed trace-run persistence; `tests/integration/test_gateway_api_coverage.py` covers failed chat `audit_trail` payloads and stream terminal-event trace links; existing gateway stream unit, trace viewer, and DMRF integration coverage was rerun with workspace-local temp paths.
- **Code audit slice 12 complete - frontend and desktop gateway trace-link consumers:** frontend `ApiError` now preserves structured non-OK gateway payloads, `ChatInterface` applies shared trace-field extraction across success, queued, rate-limit, and desktop fallback messages, and the active chat renderer now displays provider/model context plus `ChatTracePanel` links for messages with `runId` or `auditTrail`.
- **Slice 12 consumer audit result:** no separate frontend stream UI or desktop IPC offline-queue consumer was found beyond chat submission and trace/DMRF progress proxying; Trace Explorer failed-run row handling remains covered by slices 8 and 11.
- **Slice 12 regressions added:** `frontend/components/Chat/ChatInterface.test.tsx` covers queued, rate-limited, and failed fallback trace links; `frontend/tests/unit/lib/api/client.test.ts` covers `ApiError.payload` preservation for structured failed gateway payloads.
- **CodeQL alert remediation complete - reflected output and exception disclosure:** selected alerts #582 through #592 were remediated in `backend/routes/ka_routes.py`, `backend/routes/search_routes.py`, `backend/routes/mcp_routes.py`, and `backend/tracing/api.py`. Public responses now use stable generic errors for invalid KA IDs, KA/search/MCP failures, MCP console/config paths, and trace export integrity-option failures; detailed exception data remains in server logs.
- **CodeQL remediation validation added:** targeted Ruff passed for the touched alert files and regressions; focused pytest for KA/search/MCP/trace export alert surfaces passed `69 passed` with workspace-local temp paths (20 SQLAlchemy legacy-query warnings plus the known Neo4j teardown logging warning after successful exit).
- **Validation completed for current checkpoint:** targeted backend ruff passed; frontend `ApiOverlayConfig.test.tsx` passed 8 tests; focused gateway/model pytest passed 53 tests with only a Neo4j driver teardown logging warning after successful exit; focused auth/settings pytest passed 16 tests; frontend API/auth/AI settings tests passed 34 tests; focused route/auth pytest passed 70 tests; live KA/app route pytest passed 10 tests; focused KA route pytest passed 15 tests; focused KA history/DB-manager pytest passed 25 tests; focused frontend KA history/live trace Vitest passed 6 tests; focused trace viewer/export pytest passed 2 tests; focused frontend trace viewer/API Vitest passed 13 tests; focused frontend chat/API trace-consumer Vitest passed 34 tests; focused trace export/viewer/authenticity pytest passed 7 tests; focused gateway/trace/DMRF pytest passed 21 tests; focused gateway/API/trace/DMRF pytest passed 57 tests with workspace-local temp paths; direct Ruff checks for trace export files, gateway trace files, and gateway API trace files passed; frontend typecheck passed; touched MCP phase route test passed; `scripts/generate_docs.py` refreshed inventory; `scripts/verify_docs_references.py` passes with 0 errors and 17 existing heading/style warnings. Pytest emitted the known cache-permission warning and teardown-only Neo4j logging warning after successful exits.
- **Next audit slice:** no additional trace production lifecycle slice is currently identified in the active TODO/HANDOFF queue; continue broader production-depth auditing from live docs/code if requested.

---

## ▶ START HERE (next session) — updated 2026-07-01
**LLM API, DB Initialization, and Packaging: ✅ COMPLETE (2026-07-01).** 
- **Database Initialization Fix:** Bootstrapped the local SQLite database schema using `backend/init_db.py` with compliant passwords (enforcing the hardened validation rule), and then successfully played all migrations forward via `flask db upgrade` (d1e2f3a4b5c6 through d6e7f8a9b0c1). This resolved the local desktop auto-login handshake (`/auth/desktop/auto-login` 500 error on missing `users` table) and unblocked the `/chat` 401 Unauthorized API blocker.
- **API Key Consolidation:** Extracted the correct Google and OpenAI API keys from `API KEY/key.txt` (git-ignored) and updated `.env`.
- **Model Re-mapping:** Standardized on `gemini-3.1-pro-preview` for Google Gemini defaults and `gpt-5.5` for OpenAI defaults in both backend (`model_defaults.py`) and frontend (`AiModelSettings.tsx`, `page.tsx`, `types.ts`).
- **Build & Package:** Successfully compiled the Python backend distribution via PyInstaller, compiled Next.js and Electron assets, and produced the NSIS installer at the root directory: `DataLogicEngine Setup Latest.exe`.
- **Unit Test Regression:** Fixed the memory service test failure (`test_truthcore_reads_and_writes_memory_each_layer`) by mock-injecting `ka_controller` into `TruthCoreEngine`.
- **Suite Status:** All **429 unit tests** and **20 integration tests** pass successfully 100% green.

- **Start each session by running** `scripts/find_orphaned_modules.py <root>` (dead-module scanner; conservative candidates → confirm-before-cut; gitignored report).
- **Test baseline (2026-07-01): 429 unit tests passed / 20 integration tests passed / 0 failed.**
- **Gotchas:** `.venv311` for pytest, `.venv`/PATH for ruff; git = `"C:\Program Files\Git\cmd\git.exe"`; pre-commit runs ruff + frontend lint/typecheck.

---

### Session log — 2026-07-01 (LLM API & Database Initialization Fix, App Packaging)

- **Database Bootstrap:** Initialized the local database `ukg_database.db` by executing `backend/init_db.py` and then ran `flask db upgrade` to successfully play all Alembic migrations forward. The database tables are now fully aligned with the migration history.
- **Model Upgrades:** Set OpenAI model to `gpt-5.5` and Google Gemini model to `gemini-3.1-pro-preview`. Updated the defaults across both the Python Flask backend and Next.js frontend interfaces.
- **Correct API Keys:** Integrated the valid test keys from `API KEY/key.txt` into `.env`. Verified via live script execution that both providers are functional and successfully return responses.
- **Unit Test Regression:** Resolved the `test_unified_memory_service.py` regression where un-injected controllers caused refine steps to skip and fail the memory writes assertions.
- **Production Build:** Rebuilt the python backend using PyInstaller (`build_backend.py`) and successfully compiled/packaged the Electron application into `DataLogicEngine Setup Latest.exe` at the repository root. All tests are 100% green.

---

### Session log — 2026-06-24 (A32 — scripts; FINAL area, audit complete)

### Session log — 2026-06-24 (A32 — scripts; FINAL area, audit complete)

- **Retired 12 dead one-off scripts** (all unreferenced; hardcoded-path or already-executed): superseded
  scanners `audit_deep.py`+`audit_duplicates.py`; one-shot doc-patchers `patch_todo`/`patch_handoff`/
  `patch_audit_plan_session`/`patch_audit_plan_v2`/`fix_todo_dup`/`dedup_todo_item16`; hardcoded route
  diagnostics `find_all_routes`/`scan_backend_routes`; KA codemods `fix_ka_imports`/`fix_kas`. **Kept** the
  reusable parameterized scanners `find_orphaned_modules.py` + `find_core_backend_inversions.py`.
- **Guarded `seed_data.py`** — `__main__` now refuses to seed when FLASK_ENV/ENV=production unless ALLOW_SEED=true
  (it runs db.create_all + inserts sample data; mirrors the AUTO_CREATE_SCHEMA block in app.py).
- **Sweep:** no remaining hardcoded-path scripts; no scripts import a deleted module; collection clean (1806).
  The scanner's 35 scripts/ "orphans" are legit CLI entry points (import-based scan over-reports here) — kept.
- **→ A32 COMPLETE. This was the last area — the v2.0 first-pass audit (A1–A32) is DONE.**

### Session log — 2026-06-24 (A31 — docs + generated inventories)

- **Regenerated the inventories** (`scripts/generate_docs.py`, git-ls-files driven) → 1634 files; they no longer
  list this run's deletions. Only residual "deleted-module" substring is the still-existing `test_sanitizer*.py`.
- **`.env.template` single-mode reconciliation** — removed zero-reader, single-mode-contradicting config: Azure
  AD/Entra SSO, Microsoft Graph, Azure Storage, and the wrong-framework `REACT_APP_API_URL`/`REACT_APP_AUTH_PROVIDER=
  azure_ad` (Next.js uses `NEXT_PUBLIC_*`). Kept the WIRED bits (`AZURE_OPENAI_API_KEY` → gateway "azure" provider;
  `NEXT_PUBLIC_API_URL` → config_manager.get_env_dict).
- **Renamed** `test_sanitizer_and_context_aware.py` → `test_sanitizer.py` (context_aware tests removed in ORPH-v2).
- **Verified:** verify_docs_references 0 errors; deploy/** has no enterprise-layer source refs; docs/ already
  single-mode-clean from A15-B2. `tests/*.md` phase summaries left as historical snapshots.
- **→ A31 COMPLETE. Next: A32 (scripts) — last area.**

### Session log — 2026-06-24 (A12 dual-engine Postgres — DONE + local-stack naming fix)

Re-framed A12: it's NOT external-infra-gated — the databases are app-owned local components, just needed to be
running. Ran it against DataLogicEngine's OWN isolated Postgres.
- **Naming fix (the user's flag) — `start_local_stack.ps1`:** it identified data containers by published port,
  so on a machine also running another app's stack (`devonz-*`) it adopted *their* Postgres/Neo4j/MinIO + creds
  instead of our `ukg-*` containers. Added name-first resolution (`Get-DockerContainerByName` /
  `Resolve-DataServiceContainer`, prefer `ukg-*`, warn on foreign port-squatters) + made reuse-vs-start
  name-based. (`devonz` is nowhere in the repo — a genuinely separate app.)
- **Ran A12:** schema parity `pass 0/0`; the 16 Postgres-gated concurrency tests (never executed since A18's
  skipif gate) surfaced **3 issues**, all fixed: (1) stale `User(role=...)` fixtures (role dropped E-2c);
  (2) stale weak password `TestPassword123!` (now rejected); (3) **REAL Postgres-only bug** —
  `User.is_account_locked()` compared a naive `locked_until` (psycopg2 TIMESTAMP WITHOUT TIME ZONE) to aware
  `datetime.now(UTC)` → TypeError; lockout would crash on Postgres. Fixed by normalizing to aware-UTC.
- **Validation:** 16/16 concurrency on Postgres; broader Postgres slice 272 passed; SQLite same slice 256
  passed/16 skipped (no regression); ruff clean; PS parses clean; test container torn down.
  **→ A12 COMPLETE. All non-A31/A32 items cleared.**

### Session log — 2026-06-24 (A30 — config/ + migrations/ + k8s/)

DoD: migration head correct? k8s Ollama? `.env.template` OLLAMA vars? + A25/A28-deferred items.
- **Deleted `k8s/`** — `k8s/base/{backend,frontend}-deployment.yaml` (multi-replica Deployments + LoadBalancer
  + ukg-secrets; the multi-node cloud pattern, twin of the A25 operator). Zero refs in CI/deploy/spec (the
  `ukg-backend`/`ukg-frontend` hits are Docker image names in aws/azure/gcp build configs, not these manifests).
  User "choice A". (The plan's "k8s/ vs deploy/k8s/ dup" was already moot — A25 removed deploy/k8s/.)
- **Trimmed `config_manager.py`** (A28-deferred) — removed 4 dead enterprise services
  (webhook_server/model_context/core_ukg/dotnet_service) from ports+services + the JWT `auth` block. Verified
  zero readers (only `graph_store`/`verify_sqlite` use get_config, neither reads these). Kept api_gateway
  (=backend:5000)/frontend/system/database; fixed the stale "Enterprise" docstring.
- **`.env.template`: added LOCAL MODELS (OLLAMA) section** — OLLAMA_BASE_URL/PORT/TIMEOUT + LOCAL_SLM_ENDPOINT
  (read by gateway + local_model_acceleration; were undocumented despite Ollama being the primary local provider).
- **Migrations:** chain linear+single-head; documented in `migrations/README` that base schema = `create_all`
  and migrations are deltas (from-scratch `flask db upgrade` is not the bootstrap — intentional). `config.env`
  kept (referenced by runtime_precheck/security_manager).
- **Forward → A31:** `.env.template` still has heavy stale enterprise/cloud content (Azure AD/MS Graph/REACT_APP_*)
  to rewrite for single-mode; regenerate the generated inventories; clean stale tests/*.md summaries.
- **Validation:** config_manager imports clean + ruff clean + windows-platform config tests pass; full suite
  green (Neo4j forced down to skip the env-flaky e2e test). **→ A30 COMPLETE. Next: A31 (docs).**

### Session log — 2026-06-24 (outstanding-backlog knock-out — ORPH-4 + ORPH-v2; A30 prep)

Cleared the open forward backlog before opening A30. Two items done, one confirmed un-runnable here.
- **ORPH-4 ✅** — dropped the orphaned `OAuthAccount` model + `oauth_accounts` table (its only consumer,
  `oauth_manager.py`, went in ORPH-3). Removed the class from `models.py`, the `test_models` ORM pin (65→64),
  the `test_models_extended` import/test; new reversible+idempotent migration
  `d6e7f8a9b0c1_drop_oauth_accounts_table` off head `c5d6e7f8a9b0` (single head preserved); upgrade/downgrade
  round-trip + idempotency validated on SQLite; `DATABASE_SCHEMA.md` ER diagram updated.
- **ORPH-v2 security/services ✅** — orphan scanner → all 9 candidates TEST-ONLY. Per-module verify
  (confirm-before-cut): all zero prod importers, not bundled, dead-by-pivot or redundant with live code.
  **User decision: deleted 7** (`security/honeypot|context_aware|api_security|security_monitoring`,
  `email_service`, `export_service`, `services/file_upload_service`), **kept 2** (`security/data_classification`
  + `security/vulnerability_scanner` — plausible future compliance value, still test-only → reassess).
  Deleted 1 dedicated test file + trimmed 7 shared ones (kept their live-code coverage). Detail in
  `REPO_AUDIT_LOG.md`.
- **A12 ⛔ infra-gated** — Postgres (5432) + Docker unavailable in a bare session; can't run the dual-engine
  Postgres pass here. Path enabled since A18; run via `start_local_stack.ps1 -WithDataServices` or a CI matrix.
- **New findings forwarded:** (1) `active_defense.py` + `sanitizer.py` are now also test-only candidates →
  future pass; (2) a from-scratch `flask db upgrade` can't complete (`f3a4b5c6d7e8` → `NoSuchTableError:
  truth_sessions`; migrations are ALTER-only deltas on `db.create_all()`) → A30 "migration head" decision.
- **Validation:** full suite **1787 passed / 19 skipped / 0 failed** (10:22); collection clean (1806 pre-run);
  ruff clean; bandit baseline regenerated 479→472. **→ Backlog cleared (A12 excepted). Next: A30.**

### Session log — 2026-06-22e (A29 core/* — orphan/dead sweep of the deepest layer)

Ran `find_orphaned_modules.py core` over all 115 files. Most of `core/` was already audited (A9 persona/quad,
A11 axes, A13 system, A6a/b simulation, A21 mcp, N1 self_evolving); the un-audited small subdirs
(engine/graph/memory/nlp/orchestration) are scanner-clean = wired. **Removed 7 dead files** (all zero-importer,
verified):
- `core/algorithms/` entire dir (base_algorithm + perspective_analyzer + query_analyzer) — a dead parallel KA
  framework disconnected from the live backend/knowledge_algorithms (125 KAs, A7/A8).
- `core/knowledge_algorithm/resilience_router.py` + `core/security/rag_sanitizer.py` — relocated from
  backend/core in Sprint 1, never wired; redundant with live gateway resilience / rag_service injection screen.
- `core/simulation/pov_engine_enterprise.py` — dead "enterprise" POV wrapper (answers the plan's "which POV
  engine at L4?": live path uses base `pov_engine.POVEngine`); `core/simulation/query_analysis_system.py`.
- **Kept** `core/data/` (ka_registry.json is live + bundled in backend.spec).
- Validation: core imports OK, ruff clean, 66 simulation/axis tests pass, bandit baseline regenerated (479).
- **→ A29 COMPLETE. Next: A30 (`config/`, `migrations/`, `k8s/`)** — folds in the A25-deferred k8s/ vs
  deploy/k8s/ dup + k8s/base fate, and the A28-deferred stale config_manager enterprise port entries.

### Session log — 2026-06-22d (A28 backend root-level — retired enterprise multi-service layer)

Plan questions: graphql_schema=**live** (register_graphql wired in app.py, tested); celery_app=**wired** but no
worker in the packaged desktop app (`make_celery` at app.py:497; one `.delay` site in ka_master_controller);
app.py factory + N1/SEKRE **ok** (A6b/A13). 
- **Removed dead `backend/i18n.py`** — Flask-Babel **template** i18n for a server-rendered app, but this is
  Electron + Next.js (frontend owns i18n); `init_babel` never called, zero importers. (ORPH-v2 i18n resolved.)
- **Retired the enterprise multi-service layer (user decision) — 10 files.** The 3 standalone uvicorn FastAPI
  apps (`api_gateway`/`webhook_server`/`model_context_server`) + `enterprise_architecture.py` +
  `middleware/asgi_security.py` (their only consumer) + `scripts/run_enterprise_*`/`check_enterprise_health`/
  `start_enterprise.sh` + `tests/unit/test_api_gateway_auth.py`. Never launched by the desktop Flask backend —
  the microservices sibling of the retired K8s operator; also held the `model_context_server /list_models`
  stale stub. Blast radius verified (desktop factory + `backend.spec` reference none of it). **Kept**
  `config_manager` port entries (harmless data → A31/A32 cleanup) and `ka_111_api_gateway` (a KA, unrelated).
- **Fixed an ORPH-2 regression** (from `3781e1df`): two test files still imported the deleted
  `unified_middleware` (`test_unified_middleware.py` deleted; `test_unified_coverage.py` trimmed, kept its live
  `unified_mapping_api` tests). **Lesson:** grep ALL test importers after a module delete — pre-commit ≠ pytest.
- Validation: desktop backend+config+middleware import OK; middleware units 12 pass; ruff clean; bandit
  baseline regenerated (486 files). **→ A28 COMPLETE. Next: A29 (`core/*`).**

### Session log — 2026-06-22c (A27 backend/schemas — removed dead Marshmallow validation layer)

Plan: "request_schemas vs api_request_schemas — duplicate?" → **No.** Both are live **Pydantic** request-model
modules with distinct classes used by different routes (api_request_schemas → api/knowledge/compliance/
simulation routes; request_schemas → multimodal/storage). Arbitrary naming split + minor overlap
(PillarCreateRequest vs PillarLevelCreateRequest) but both used — kept both.
- **Real find = dead parallel Marshmallow layer** (validation migrated Marshmallow→Pydantic): emptied
  `__init__.py` (255 lines of Marshmallow `User*Schema`/`validate_with_schema`/… → minimal docstring),
  **deleted** `simulation_schemas.py` (Marshmallow) + `auth_schemas.py` (Pydantic multi-user auth). All had
  **zero importers + zero tests** (every ref was self-internal or in generated/audit docs).
- Verified: `import backend.schemas` + live submodule imports OK; ruff clean; 24 focused tests pass; orphan
  scanner schemas candidates gone (ORPHAN 3→1, only `i18n` left → A28); bandit baseline regenerated (492 files).
- **ORPH-4** (`OAuthAccount` model, models.py:244) NOT touched — needs an Alembic migration + 65-class ORM-pin
  update; deferred to a models/schema migration session.
- **→ A27 COMPLETE. Next: A28 (`backend/*.py` root-level)** — graphql_schema/celery_app/app.py factory; the 3
  standalone FastAPI services (api_gateway/model_context_server/webhook_server, incl. model_context_server
  `/list_models` placeholder stub); ORPH-v2 `backend/i18n.py`.

### Session log — 2026-06-22b (carry-over knock-out — 8/9 DONE; only A12 remains)

Cleared the carry-over backlog in commits `ff30a072` (batch 1), `3781e1df` (batch 2), `7b575e5b` (ORPH-3).
**DONE:** A18-pre (verified), ORPH-1 (db_utils removed), ORPH-2 (unified_middleware removed — api_gateway uses
asgi_security, not it), ORPH-3 (`mcp_server/oauth_manager.py` removed — user decision; SaaS-connector consumers
gone in pivot; `OAuthAccount` model kept → forward **ORPH-4** = assess dropping model+table in A27/schema),
A3-4 (HONEYPOT→BLOCK correct single-mode + comment; user_role already "owner"), A5-2 (verdict: defense-in-depth
UNION, keep all five), SC-2 (AES-256-GCM verified implemented + docs consistent), A32-mini (inversion-scanner
startswith fix → 0; audit_deep stale routes/ dropped; bandit baseline regenerated). **REMAIN:** **A12** Postgres
run — infra-gated (needs local stack). **Carry-over gate met → A27 (`backend/schemas/`) is next.**

**Orphan-scanner v2 (NEW, important):** hardened `find_orphaned_modules.py` to exclude prose docs (.md/.txt)
from the reference corpus (an audit/handoff/structure doc that *mentions* a path is not wiring and was masking
orphans). Now surfaces **13 candidates** (was 4) — recorded for **per-area verification, NOT mass-deletion**:
schemas/auth_schemas+simulation_schemas → **A27 (next)**; security/{api_security,context_aware,
data_classification,honeypot,security_monitoring,vulnerability_scanner} → A10; email_service/export_service/
file_upload_service → A19; i18n → A28. Several are plausibly dead-by-single-mode-pivot (esp. auth_schemas,
email_service) but each needs the per-module check (cf. the `feature_flag_routes` false-positive).

### Session log — 2026-06-22 (carry-over backlog knock-out — STARTED, EOD pause)

Goal this session: clear all open ☐ carry-over findings before opening A27. Enumerated the backlog and
started; paused at EOD with most items still pending. **Resume here next session, then A27 (`backend/schemas/`).**

**Authoritative open carry-over list (verify against live code — table drifts):**
1. **A18-pre — ✅ VERIFIED RESOLVED this session (doc-close only).** The `drop_all_test_tables` conftest-name
   collision is gone: the helper now lives in `tests/_helpers.py:44` and the two consumers import it via
   `from tests._helpers import drop_all_test_tables` (`tests/integration/test_api_endpoints.py:9`; root
   `tests/conftest.py:42` re-exports). No code change needed — closed the stale ☐ in the plan table.
2. **ORPH-1 `backend/utils/db_utils.py` (`DatabaseManager`) — confirmed dead; removal PENDING.** Self-described
   "Phase 3 test suite" helper; zero importers incl. tests; distinct from the live `UkgDatabaseManager`
   (`backend/ukg_db.py`). Clean delete (no test to trim).
3. **ORPH-2 `backend/api_gateway/unified_middleware.py` — investigated; PENDING (→A28).** Read confirms it's a
   Starlette `BaseHTTPMiddleware` (`UnifiedMiddleWare`) + `PIIShield` + `APIParityService` for the standalone
   `api_gateway` FastAPI service; **only tests import it** — no production consumer. Decide alongside the A28
   assessment of the 3 standalone FastAPI services (if that service is dead, this goes with it).
4. **ORPH-3 `backend/mcp_server/oauth_manager.py` — investigated; PENDING (→A21 revisit).** Read confirms it's
   real, coherent connector-OAuth token lifecycle (`get_/upsert_connector_oauth_token` against the
   `OAuthAccount` model) but with **zero callers** — built-but-unwired. Decide: wire into the MCP connector
   execution path or remove.
5. **A3-4 — NOT STARTED.** `backend/security/defense_supervisor.py`: `user_role` always "user"; HONEYPOT
   treated as BLOCK. Reconcile to single-mode (owner) + distinct HONEYPOT handling, or document.
6. **A5-2 — NOT STARTED.** Confirm the five overlapping injection defenses (shield/guardrail/supervisor/
   truthgate/dmrf) form a union (not redundant); decide consolidation; document verdict.
7. **SC-2 — NOT STARTED.** Confirm AES-256-GCM `EncryptionManager` is the implemented reality; fix any docs
   still describing Fernet/target-state.
8. **A32-mini — NOT STARTED.** `audit_deep.py:144` stale regex; `find_core_backend_inversions.py` docstring
   false-positive (`sufficiency.py:414`); `.bandit-baseline.json` stale all-zero blocks (`input_sanitizer.py`
   + `operator/operator.py` + `operator/controller.py`) → batch-regenerate.
9. **A12-followup — INFRA-GATED.** Dual-engine Postgres run; path enabled but needs the local Postgres stack
   running (`start_local_stack.ps1`). Not runnable in a bare session; run via local stack / CI matrix.

A task list (#1–#9) tracks these. Today's committed work prior to this pause: A25 (operator removal), A26
(tracing + A3-5 fix + TraceLogger removal), and `scripts/find_orphaned_modules.py` (+ ORPH-1/2/3 findings).

### Session log — 2026-06-21q (A26 backend/tracing — verify + A3-5 fix + dead TraceLogger removed)

Plan: "separate from TruthMemory? both fire on query?" → **separate, both fire** (distinct points).
- **Separate:** tracing = forensic audit-provenance in relational `Trace*` tables (write-once, read by the
  frontend Trace Viewer + compliance export, never re-read by reasoning); TruthMemory (DB-M) = the AI's
  reasoning memory (`StructuredMemoryGraph`, recall/consolidate per layer, feeds back). Orthogonal.
- **Both fire on query:** gateway writes `TraceRun`/`TraceStage` inline (`gateway.py:1899–1951`) + Socket.IO;
  TruthMemory recalls/consolidates inside `truth_core` (A23). `trace_bp` registered in both app factories.
- **A3-5 FIXED (silent compliance gap):** api.py's user-facing endpoints built bare `LLMGateway()` →
  `AIGovernanceEngine.db=None` → `process()`'s `record_audit_event` no-op'd (no `AIAuditEvent`) + daily token
  budget unenforced; traces still wrote (they import `db` directly), so 200s hid it. Passed
  `db_session=db.session` at the 3 reasoning sites (`gateway_chat`, streaming `generate()`,
  `replay_offline_queue`); mirrors known-good `chat.py:175`. Left `test_provider` (health-check) bare.
- **Dead `TraceLogger` removed (user decision):** writer helper with zero production callers (gateway
  open-codes the writes); deleted `backend/tracing/logger.py`, trimmed its test + import (+ unused `uuid`),
  fixed `docs/diagrams/07` to show gateway-writes / api-reads. Same class as the A20 test-only InputSanitizer.
- **Validation:** 47 focused tests pass (governance/gateway-api/tracing/integration_routes), ruff clean.
- **Forward → A31/A32:** `docs/FILE_INVENTORY.csv` still lists deleted `logger.py` (generated; batch-regen).
- **→ A26 COMPLETE. Next: A27 (`backend/schemas/`)** — `request_schemas.py` vs `api_request_schemas.py` dup?

### Session log — 2026-06-21p (A25 backend/operator — removed obsolete K8s operator)

Plan question "what is this pattern? used by anything? if not: document or remove." → **removed.**
- **What:** a Kubernetes `kopf` operator for multi-node cloud-cluster orchestration — `operator.py`
  (reconciles `UKGNode`/`MCPServer` CRDs → Deployments) + `controller.py` (`KAOperator` scales KA worker
  pods by Redis queue depth; `DRController` multi-region DR). Infrastructure twin of the removed multi-user
  auth surface; obsoleted by the same single-mode decision (even "cloud" = single-tenant single VM).
- **Zero-importer scan:** no Python importers (the one `import operator` is stdlib — false positive);
  no `__init__.py` (never a package); not in `backend.spec` (not bundled); `kopf` not in `requirements.txt`
  (can't run as wired); `controller.py` doubly-dead (no importer *and* no manifest invokes it). Only refs =
  duplicated `k8s/operator/` + `deploy/k8s/operator/` manifests + an archived "Planning/v3.0" design doc.
- **Deleted 13 files** (user decision: code + all operator manifests): `backend/operator/**`,
  `k8s/operator/**`, `deploy/k8s/operator/**` (emptied `deploy/k8s/` removed). **Kept** `k8s/base/`
  (generic Deployments — A30 question) and KA-107 (independently registered in `ka_registry.yaml`).
- **Verified clean:** post-delete `git grep` over active code/manifests = zero real operator refs.
- **Forward:** A32 (`.bandit-baseline.json` 2 stale all-zero operator blocks → batch-regen with the
  input_sanitizer block); A30 (duplicated `k8s/` vs `deploy/k8s/` + `k8s/base/` fate under single-mode).
- **→ A25 COMPLETE. Next: A26 (`backend/tracing/`)** — separate from TruthMemory? both fire on query?
  (folds in carry-over A3-5: governance `record_audit_event` no-op without a db session).

### Session log — 2026-06-21o (A24 backend/observability — verify-only)

All 3 plan questions YES. `crash_reporting.py` + `latency_slo.py`.
- **Sentry ✅:** `initialize_crash_reporting()` at startup (app.py:38) — real sentry_sdk.init (Flask+SQLAlchemy
  integrations), fail-soft (no DSN→disabled, import/init failure→fallback). `capture_exception_with_fallback`
  wired into app error handler (app.py:1257), always returns a stable crash id.
- **SLO ✅:** `evaluate_latency_slos` compares ai/connector p95/p99 vs env thresholds (min_samples gate) →
  violation flags; alerting downstream via Prometheus gauges + deploy/SENTRY_ALERTS/UPTIME_MONITORING.
- **Prometheus ✅:** `/metrics` (app.py:1193) aggregates latency_slo + crash_reporting prometheus lines.
- Tested: test_latency_slo_alerts + test_health_endpoint 9 pass. No stubs, no code changes.
- **→ A24 COMPLETE. Next: A25 (`backend/operator/`).**

### Session log — 2026-06-21n (A23 backend/memory — verify-only + all-databases-internal note)

- **Architecture note (user, 2026-06-21):** ALL databases (Postgres/Redis/Neo4j/Chroma/object/SQLite) are
  **local internal app-owned** components like Neo4j — not external services. Saved memory
  `architecture-local-databases`.
- **A23 DB-M confirmed:** `UnifiedMemoryService` genuinely wraps `StructuredMemoryGraph`
  (core.persona.quad.mathematical_framework): `consolidate`→`graph.memory_consolidation` (MC(M,I,t)),
  `recall` via graph relevance×temporal×importance. Local JSON persistence at
  `databases/memory/memory_graph.json` (app-owned); FROST checkpoint/restore; layer/persona namespacing.
  Wired into truth_core engine/emergence_controller, frost_service, /health. Memory tests 3 pass/1 skip
  (graph-backed E2E skips without the local Neo4j stack). No stubs, no code changes.
- **→ A23 COMPLETE. Next: A24 (`backend/observability/`).**

### Session log — 2026-06-21m (A22 backend/ingestion — verify-only)

All 3 plan questions YES. `backend/ingestion/` = `local_ingestion.py` (`LocalKnowledgeIngestionService`).
- **ChromaDB population ✅:** chunks → dedup'd SQL `KnowledgeGraphNode` rows → `rag.ingest_knowledge_node`
  into Chroma `knowledge_nodes` (A12 DB-C). **Async queue ✅:** `ingest_path_async` daemon thread +
  app_context + `_ASYNC_STATUS` + `GET /status/<id>`. **Neo4j sync ✅:** `_sync_to_neo4j` →
  `scripts.sync_nodes_to_neo4j.sync()` when `sync_neo4j=True`.
- Hardening: injection scrubbing, size cap, PDF/DOCX via DocumentProcessor, manifests. Wired: 5
  ingestion_routes endpoints + CLI + evidence script; 14 KI tests pass. No stubs, no code changes.
- **→ A22 COMPLETE. Next: A23 (`backend/memory/`).**

### Session log — 2026-06-21l (A21 backend/mcp_server — verify-only)

All 9 files real and wired, no stubs.
- **MCP inversion fix confirmed** — plan said "LY-4" but that's PersonaConstructionService; the MCP fix is
  **LY-6**. `scope_enforcement.py` (+ siblings) are shims re-exporting `core.mcp.*` (provider-neutral logic
  promoted to core; backend re-exports = correct backend→core direction). 0 real inversions.
- **Sampling real & wired:** `MCPSamplingService.create_message` (provider or deterministic local) via
  `mcp_routes` + `app.py`. **Subscriptions real & wired:** `MCPSubscriptionManager` subscribe/notify/SSE via
  `truth_link.transport.SSETransport`.
- **Forward:** (A32) `find_core_backend_inversions.py` false-positives on a *docstring* in
  `sufficiency.py:414` (prose mentioning `backend.truth_engine…`, not an import) — scanner should skip
  comments; real inversion count is 0; not CI-gating. (A28) `model_context_server.py` `/list_models` is a
  placeholder stub — assess the 3 standalone FastAPI services (api_gateway/model_context_server/webhook_server)
  together in A28.
- No code changes (verify-only, like A11/A13). **→ A21 COMPLETE. Next: A22 (`backend/ingestion/`).**

### Session log — 2026-06-21k (A20 backend/middleware — verify + remove disconnected InputSanitizer)

- **Stack active & correctly ordered:** `setup_middleware(app)` called at `app.py:588`; wires correlation_id
  (first, so request_id precedes logging/audit), security_headers, request_limits, timeout, resource_governor,
  + after_request etag/audit. `asgi_security` correctly wired into the FastAPI sub-services (not the Flask
  factory). Ordering sound.
- **Removed disconnected `input_sanitizer.py` (InputSanitizer)** — user decision. Built but only referenced by
  a unit test; never wired. Wiring it to an AI gateway would 400 legitimate LLM prompts (regex-blocks
  SQL/shell terms). Real protection already covered (SQLAlchemy params + semantic injection defenses + RAG
  screening). Deleted the module + its `test_input_sanitizer_json` (trimmed `test_middleware_units.py`, which
  still covers the other 4 middleware). Fixed resulting unused imports.
- Minor (forward → A32): `.bandit-baseline.json` has a stale all-zeros metrics block for the deleted file
  (harmless; generated baseline). Validation: middleware units 7 pass; ruff clean.
- **→ A20 COMPLETE. Next: A21 (`backend/mcp_server/`).**

### Session log — 2026-06-21j (A19 backend/services — verify + model-currency fixes)

Audited all 6 `backend/services/` — **all real and wired, no stubs**:
- **RAG populates context (✅ real):** `rag_service.get_context_for_query()` = vector search → score gating
  (`RAG_MIN_SCORE`) → injection-marker screening → token budgeting → optional citations; wired into gateway,
  truth_core, chat, ingestion.
- **Audio/Video real:** Whisper STT + Gemini failover + OpenAI TTS; OpenCV frames + Vision LLM via gateway;
  both wired into `multimodal_routes`.
- **Model-currency fixes (user flagged gpt-4o vision as very old):** `video_service` `gpt-4o` →
  `OPENAI_LATEST_MODEL` (gpt-5.5); `audio_service` `gemini-1.5-flash` → `GOOGLE_LATEST_MODEL`
  (gemini-3.1-pro-preview); `ka_06_config.json` `gpt-4o`/`gpt-4o-mini` → `gpt-5.5`. Now reference `model_defaults`
  constants (no future drift). ruff clean, imports OK.
- **Forward (minor):** `model_context_server.py` `/list_models` is a placeholder stub with stale `*-gpt-4`
  display names → A21/A28; `governance.py` legacy `gpt-4` cost-fallback entry (harmless).
- **→ A19 COMPLETE. Next: A20 (`backend/middleware/`).**

### Session log — 2026-06-21i (A18 resilience fault-injection — A18 COMPLETE)

Plan question "Resilience tests inject real failures?" → **YES**.
- `tests/resilience/` is **dead**: nothing git-tracked; source `test_self_healing.py` removed long ago
  (`742aec82`); only an untracked local `.pyc` ghost remained (absent from fresh clones). Removed the on-disk
  orphan (no git change).
- Real fault injection lives in the gateway suites: `test_gateway_failover` (inject `Exception("API Down")`
  → assert failover to 2nd provider), `test_gateway_enforces_provider_timeout` (slow provider → timeout
  bound), `TestCircuitBreaker` (real `record_failure` trips breaker + `recovery_timeout` re-closes; DB
  `side_effect` exercises degradation). 9 pass live.
- **→ A18 COMPLETE.** All A18 plan items done: test-isolation backlog, stale-fixture fix, skipped-tests
  justification, dual-engine parity, resilience. **Next: A19 (`backend/services/`)** — RAG context
  population, audio/video real-vs-stub.

### Session log — 2026-06-21h (A18 dual-engine SQLite+Postgres parity)

- **Schema parity ✅ confirmed:** `scripts/validate_schema_parity.py` (release gate) compiles every ORM
  table/column to both SQLite + Postgres DDL → **pass, 0 errors/0 warnings** after this session's model
  changes. Schema is fully portable to Postgres.
- **Enabled runtime dual-engine testing:** the suite was SQLite-only (root `app` fixture hard-coded sqlite).
  Added `TEST_DATABASE_URL` + `is_sqlite_test_db()` to `tests/_helpers.py`; `app` fixture now reads
  `TEST_DATABASE_URL` (defaults to the local SQLite file — **no-op unless set**). Run on Postgres with
  `TEST_DATABASE_URL=postgresql://…@localhost:5432/… pytest` (Postgres is the app's local internal store via
  `start_local_stack.ps1`).
- **Postgres-gated the 7 concurrency classes:** were unconditional `@pytest.mark.skip` (never ran on any
  engine) → now `skipif(is_sqlite_test_db())` so they skip on SQLite (16 tests, unchanged) and **run on
  Postgres**, exercising the live atomic-increment/lockout-race logic.
- Validation: parity gate 0/0; ruff clean; concurrency 16 skipped on SQLite (unchanged); conftest slice 15
  passed/1 skipped. **Local Postgres not running this session (5432 refused) → Postgres run path enabled but
  not yet executed; validate via CI Postgres-matrix or local stack** (forward).
- Next A18: resilience-test fault injection → then A19 (`backend/services/`).

### Session log — 2026-06-21g (A18 skipped-tests justification + Neo4j framing correction)

- **Skipped-tests justified** (A18 def-of-done). Reviewed every skip site (table in `REPO_AUDIT_LOG.md`).
  All are legitimate env/opt-in/platform gating **except** `end_to_end/test_full_simulation.py`, which was
  **dead** — an unconditional `pytest.skip` against a deprecated `process_query` API, patching a
  non-existent `simulation.simulation_engine` path; the flow is covered by `test_e2e_scenarios.py` +
  `tests/simulation/`. **Removed it.** The 7 `test_user_model_concurrency.py` skipped classes are legit
  (SQLite concurrency limit; they exercise live lockout methods) — forwarded a note to consider gating them
  to *run on Postgres* for dual-engine coverage.
- **Neo4j framing corrected (user note):** Neo4j is a **local internal, app-owned** data store (started via
  `scripts/windows/start_local_stack.ps1` / `setup_local_databases.py`, with Postgres/Redis/MinIO) — **not an
  external service**. Reworded the skip guard (docstring + reason → "Local Neo4j not started; run the local
  stack") and corrected the "external/CI lacks/provision in CI" framing in `REPO_AUDIT_LOG.md`, `TODO.md`,
  this file, and memory. The guard behavior is unchanged (skip a bare run that hasn't started the local stack;
  run once it's up).
- Validation: ruff clean; memory test 3 passed/1 skipped with the new reason.

### Session log — 2026-06-21f (A18 tests/ — backlog cleared: conftest collision + Neo4j guard)

Started Phase 4 / A18 by clearing the recorded test-isolation backlog:
- **A18-pre conftest collision** — repro confirmed: `tests/unit tests/compliance` collected together raised
  `ImportError: cannot import name 'authenticate_client_session' from 'conftest'
  (tests/unit/conftest.py)`. Only 2 files used the fragile `from conftest import …`. Created
  `tests/_helpers.py` (collision-free module) with `authenticate_client_session` + `drop_all_test_tables`;
  root `tests/conftest.py` re-exports them (single source of truth, back-compat); re-pointed the 2 imports.
  Now collects **698 tests, 0 errors**.
- **Neo4j-skip guard** — `test_truthcore_reads_and_writes_memory_each_layer` failed `assert 1 == 3`
  (Neo4j refused at 127.0.0.1:7690, so graph-backed memory writes don't happen). Added `_neo4j_available()`
  (resolves URI as `GraphStore`, 0.75s socket probe) + `@pytest.mark.skipif`. Now skips cleanly.
- **`integration_routes` isolation** — the "10 failed + 10 errors" memory baseline predated this session's
  fixes; passes **98/98 standalone** on current `main`; the conftest fix enables clean combined collection.
- **Bonus find (full-suite run):** the clean suite (1875 passed / 1 failed) surfaced
  `test_canonical_v1_simulation_routes_have_strict_happy_path_contract` (500≠201). Cause: the contract file's
  local `app` fixture built `User(role="user", …)` — `role` was dropped in E-2c, so the constructor raised and
  the fixture's bare `except` swallowed it → no test user → route 500. A leftover the E-2c sweep missed; fails
  standalone (not from the conftest move). Fixed by dropping the `role=` kwarg; swept tests/ for siblings (none
  — all other role/is_admin hits are mocks or non-persisting helper params). Contract file 6/6 green.
- Validation: targeted runs green (698/0, affected files 75/75, memory 3+1skip, integration_routes 98/98,
  contract 6/6), ruff clean. Clean full suite was 1875 passed/20 skipped/1 failed → that 1 is now fixed
  (expect 1876/20/0). Next: A18 remaining (20 skipped-tests justification, dual-engine SQLite+Postgres check,
  resilience tests) → then A19 (`backend/services/`).

### Session log — 2026-06-21e (F5-frontend — web-login vestige removal, A17-1 resolved)

Removed the dead multi-user web-login client surface (the A17-1 finding). **Confirm-before-cut
shrank the scope:** the `(auth)/login`+`(auth)/register` pages are already `redirect('/dashboard')`
stubs (PRODUCT_OVERVIEW's disabled-by-design state) and a zero-consumer scan showed **no component
uses `useAuth().login`** (only `settings/privacy` uses `logout`). So only the plumbing was dead:
- `lib/api/auth.ts` — removed `login` (`POST /auth/login`) + `logout` (`POST /auth/logout`) (both
  404 now) + `LoginCredentials`/`LoginResponse`; kept `check` + `desktopAutoLogin`.
- `contexts/AuthContext.tsx` — removed the unused `login` method + `LoginCredentials` import;
  simplified `logout` to single-mode (dropped the dead non-desktop `api.auth.logout()` + `/login`
  push; navigates to `/dashboard` = existing desktop behavior; `settings/privacy` logout still works).
- `lib/api/client.ts` — dropped stale `/auth/login` + `/auth/register` CSRF-exempt entries.
- Tests — rewrote `auth.test.ts` (kept check + desktopAutoLogin + a guard that login/logout are gone);
  neutralized a stale `buildApiUrl('auth/login')` example in `client.test.ts`.
- **Kept by design:** the redirect-stub pages + middleware/client session-expired `/login` redirect
  (documented disabled-by-design single-mode neutralization — not dead code).
- Validation: **full frontend suite 76 files / 378 tests pass**; tsc clean; pre-commit green. A17-1 RESOLVED.

### Session log — 2026-06-21d (A17 verify-only — Phase 3 COMPLETE)

Audited `frontend/lib/` (19 files) + `hooks/useTraceStream.ts` + 3 contexts. Verify-only pass
(like A11/A13) — all three plan exit questions confirmed against live code:
- **Socket.IO trace stream end-to-end ✅** — `useTraceStream` → `joinRunRoom` → `join_run_room`
  (`backend/websocket.py:82`, room `run_{id}`) → `emit_trace_stage_update` (room-scoped, from
  `gateway.py:1936`) → `socket.ts:197` binds `trace_stage_update`. Room naming matches both sides;
  client dedupes by `stage_id`, filters by `run_id`.
- **API client paths ✅** — `index.ts` composes all 8 domain modules; `trace.ts` matches the TV backend.
- **Auth refresh ✅** — `AuthContext.checkAuth` → `desktopAutoLogin` on no-session; `client.ts` recovers
  401 via `tryDesktopAutoLogin` + retry (desktop only).
- **A17-1 finding (forwarded → F5-frontend):** vestigial multi-user web-login client surface still
  present — `api/auth.ts` `login`/`logout` hit removed `/auth/login`+`/auth/logout` (404); `client.ts`
  CSRF-exempt list still lists `/auth/login`+`/auth/register`; `(auth)/login`+`(auth)/register` pages +
  AuthContext non-desktop branch. Unreachable in desktop mode. Not an isolated cut (login page imports
  `useAuth().login`) → coordinated F5-frontend removal alongside the final auth cleanup.
- Minor (noted, unchanged): `useSocket()` connects/setHandlers during render; `api.system.health` is a
  stub. No code changes. **→ A17 COMPLETE. PHASE 3 (A15+A16+A17) COMPLETE.**
- **Next: Phase 4 — A18 `tests/`** (the recorded test-isolation backlog: `tests/integration_routes`
  shared-DB isolation → function-scoped/per-test DBs; A18-pre conftest-name collision; Neo4j-skip guard).

### Session log — 2026-06-21c (A16 close-out — C3 + final accessibility sweep — A16 COMPLETE)

Closed the last two A16 items (Type Safety 100% + Test Coverage 80%+ were already met):
- **C3** (`test_provider` status codes inline) was **already implemented** in
  `ApiOverlayConfig.tsx` — `mapProviderTestError` maps 401/429/422/504 and `handleTestConnection`
  renders an inline "Connection Error" card with an `HTTP {statusCode}` badge (not just a toast).
  Added the missing regression test asserting the inline `HTTP 401` + "Invalid API key" path
  (7/7 ApiOverlayConfig tests pass).
- **Final accessibility sweep** — verified every settings/projects component is swept. All 4 settings
  components + `projects/ProjectDetail` carry ARIA; `admin` has no components (admin surfaces are pages,
  covered under A15). The one remaining gap was `DatabaseSettings.tsx`: its 12 Local/Cloud config inputs
  used `<Label>` without `htmlFor` and `<Input>` without `id` (visually but not programmatically
  associated). Fixed all 12 label/input associations, added `role="status"` + sr-only text to the
  loading spinner, and `aria-busy` to the root container. Added an a11y regression test
  (10/10 DatabaseSettings tests pass). typecheck clean.
- **→ A16 COMPLETE.** Next in order: **A17** (`frontend/lib/`, `hooks/`, `contexts/`).

### Session log — 2026-06-21b (A15 per-page error/loading verification — A15 COMPLETE)

Closed the last A15 def-of-done item: per-page error + loading-state verification across all 29
`frontend/app` pages. Eleven route segments already had a route-level `error.tsx` (the shared
`RouteErrorFallback` pattern), and error boundaries inherit to children (so `settings/privacy`,
`projects/view`, `runs/view`, `admin/compliance`+`admin/mcp*` were already covered). The data-driven
pages **without** a boundary were `algorithms`, `knowledge`, `profile`, `tools/history`.
- Added route `error.tsx` (RouteErrorFallback) to those 4 segments — render-exception boundary now
  matches the other 11.
- **Real bug fixed:** `knowledge/page.tsx` destructured SWR but **ignored `error`**, so a failed
  `api.knowledge.pillars` fetch showed the misleading "No pillars defined" *empty* state. Now surfaces
  an error card (the empty state only renders for an actual empty array, so no conflict).
- Single-mode cleanup: `profile/page.tsx` toast told users to "Use Admin > User Management" (removed
  in E-2a) → reworded to OS-level single-owner copy.
- `app/app-surfaces.test.tsx` extended to assert all **15** module error boundaries (was 11); 5/5 pass.
  `tsc` typecheck clean. (`algorithms`/`profile`/`tools-history` already had thorough in-component
  loading+error handling; `knowledge` now does too.)
- **→ A15 COMPLETE.** Next in order: **A16** final accessibility sweep + carry-over **C3**
  (`test_provider` status codes inline in `ApiOverlayConfig.tsx`), then **A17** (`frontend/lib`/hooks/contexts).

### Session log — 2026-06-21 (A15 B2 — RBAC/multi-user doc reconciliation, single-mode)

Closed the A15 **B2** carry-over: reconcile docs that still describe the now-removed multi-user
auth surface. The auth deprecation (Phases A–F) is COMPLETE in code, so these docs were actively
misleading. Verified the 3 originally-named targets (`PRODUCT_OVERVIEW.md`, `ARCHITECTURE.md`,
`diagrams/11`) were already single-mode-clean; a live grep-by-concept surfaced **8 other live docs**
still referencing deleted modules/columns. All corrected **after confirming against live code**
(`rbac.py`/`mfa.py`/`tenant_rls.py`/`zero_trust.py`/`token_manager.py` deleted; `session_manager.py`
kept; User `role`/`is_admin`/`mfa_*`/`backup_codes` columns dropped; `auth_routes.py` exposes only
`/check`, `/csrf-token`, `/desktop/challenge`, `/desktop/auto-login`):
- **`docs/API.md`** — biggest fix: Section 1 documented `/login`, `/register`, `/logout`, `/mfa/setup`,
  `/mfa/confirm`, `/mfa/verify`, `/login/sso` — **all return 404 now**. Replaced with the 4 real
  desktop-auth endpoints; dropped "user and role management" admin capability + tenant-RLS metric + SSO/MFA.
- **`docs/AUTH_DECORATORS.md`** — removed the deleted `from backend.security.rbac import require_permission`
  example; documented `@api_admin_required` as an alias of `@api_login_required` + the `current_user_is_owner()` gate.
- **`docs/DATABASE_SCHEMA.md`** — users ER diagram dropped 5 removed columns; tenant-isolation section reframed
  (RLS module gone, `tenant_id` columns vestigial); sensitive-fields table trimmed.
- **`docs/SECURITY.md`** — "Tenant isolation" → "Tenant scope (single-mode)"; removed deleted module/metric/test refs.
- **`ARCHITECTURE_MAP.md`, `DEVELOPER_GUIDE.md`, `AI_MANAGEMENT_SYSTEM_42001.md`, `SDLC_SSDF_MAPPING.md`,
  `diagrams/02`, `diagrams/07`** — removed RBAC/RLS/tenant-RLS/user-management references.
- Left untouched by design: `docs/archive/**` (historical record), generated inventories
  (`GENERATED_STRUCTURE.md`/`FILE_INVENTORY.csv` → A31/A32), and audit records (`docs/audits/**`, `REPO_AUDIT_LOG.md`).
- Validation: `scripts/verify_docs_references.py` → **0 errors** (18 pre-existing heading-style warnings).
- **Remaining A15:** F5 (E-2c is already done) + per-page error/loading-state verification. **Remaining A16:**
  final accessibility sweep + carry-over C3 (`test_provider` status codes in `ApiOverlayConfig.tsx`). **A17 not started.**

### Session log — 2026-06-19e (CRITICAL models.py restore + auth Phase D & E-1/E-2a/E-2b)

**🔴 Critical regression found + fixed.** HEAD commit `6c7cf68b` (scoped "fix(mfa): verify_totp")
had silently committed a stale, truncated `models.py` (2609→960 lines), dropping **47 ORM model
classes** (TraceRun/Trace*/Truth*/MCP*/Node/Edge/PillarLevel/Sector/Domain/Location/
KnowledgeAlgorithm/KAExecution/UserAIPreferences/…). `import models` still succeeded, so nothing
failed loudly, but top-level imports broke in `llm_gateway/gateway.py`, `routes/api_routes.py`,
`repositories/node_repository.py` (+ CI pytest collection). The whole backend would not boot.
- **Fixed** (`8362882b`): restored `models.py` from parent `2b1f67e3`, kept only the intended
  `verify_totp`→pyotp change; added regression guard `test_models_orm_surface_is_complete` pinning
  all 65 ORM classes (verified it catches truncation). Reviewed last 20 commits — this was the ONLY
  damage. **Lesson:** always read `git show --stat` (scope), not just the subject, before trusting a commit.

**Auth deprecation — Phase D done + Phase E started** (continuation of the A15 deferred auth removal;
plan: `docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md`):
- **Phase D** (`c60f3daf`): removed multi-tenant `tenant_rls.py` (Postgres RLS — no-op on SQLite
  desktop, obsolete under single-mode) + its app.py wiring/metrics + tests. (MFA module already gone.)
- **Phase E-1** (`c60aee15`): dropped `mfa_enabled`/`mfa_secret`/`backup_codes` columns + `verify_totp`;
  reversible Alembic migration `b4c5d6e7f8a9` (validated upgrade/downgrade/idempotent).
- **Phase E-2a** (`e2994349`): removed admin user-mgmt UI (`frontend/app/admin/page.tsx`) + backend
  (`backend/admin.py` deleted; `admin_routes.py` slimmed to cache/health). Cleared 13 pre-existing
  test failures. Compliance + MCP admin pages/nav kept.
- **Phase E-2b** (`deb6a656`): collapsed ALL ~50 `is_admin` authorization gates to single-owner via
  `current_user_is_owner()` (api_decorators) + `_user_is_owner()` (tracing/api.py); deleted dead
  `backend/decorators.py`. `role`/`is_admin` columns are now INERT.
- **Phase E-2c** (`950eda75`): dropped `role`/`is_admin` columns + indexes (migration `c5d6e7f8a9b0`,
  validated); to_dict/GraphQL return single-mode constants; conftest keeps params but stops persisting;
  ~10 test files + 3 scripts updated; 2 obsolete `windows/verify_*` scripts deleted.
  **→ AUTH DEPRECATION PHASES A–F COMPLETE** (no MFA/tenancy/admin-UI/roles; all gates single-owner).
- **A18 finding:** `tests/integration_routes` has a severe pre-existing shared-DB isolation bug
  (baseline = 10 failed + 10 errors standalone; failures vary per run) + the A18-pre conftest-name
  collision. Not introduced by this work; flagged for the A18 (tests/) audit.

### Session log — 2026-06-19f (CI repair after auth deprecation)

CI/Deploy had been red **since before this session** — root cause was the
`test_mfa_comprehensive` collection error (pre-session) which interrupted the whole
suite, masking many failures. Fixing it (this session) let the suite run and exposed
a mix of real regressions + long-masked pre-existing failures. Each was confirmed by
running the failing tests at baseline `8362882b` (before D/E). Fixed in `379437bd`:
- **My regressions:** (1) `user_data_routes.delete_user_profile` read the dropped
  `current_user.role` → 500; removed the obsolete owner-self-delete guard. (2) frontend
  E2E route-smoke specs (`route-sidebar-smoke`, `electron-route-sidebar-smoke`,
  `visual-audit`) listed bare `/admin`, which 404s now that the admin dashboard page was
  removed (E-2a) → dropped `/admin` (kept `/admin/compliance`, `/admin/mcp[/servers]`).
- **Pre-existing (failed at baseline; from Phase B `api_admin_required`→`api_login_required`):**
  `ukg_api.create_pillar/create_sector` raised `KeyError`→500 on missing fields once the
  admin gate stopped blocking; added 400 validation. `test_connect_requires_admin` asserted
  removed admin-denial → rewrote as `test_connect_requires_auth` (unauth → 401/403).
- **Still red, NOT fixed (pre-existing, A18 scope):** `tests/integration_routes` shared-DB
  isolation flakiness (order-dependent) + `test_truthcore_reads_and_writes_memory_each_layer`
  (needs the app's **local internal** Neo4j running — it's app-owned, started via the local
  data stack, not an external service — and this run hadn't started it). These predate the auth
  work and need the A18 test-isolation overhaul (function-scoped/per-test DBs) + a Neo4j-skip guard.
- Validation: security (234), unit (864), trace/gateway/mcp/feature-flag (143), admin/model (60+22) green;
  1935-test collection clean; pre-commit green on every commit.

_Last updated: 2026-06-19 — **A16 Priority 2 coverage is now 80.06%+; latest frontend batch adds project/settings/MCP/chat accessibility refinements.**
Done: Sprint 0, A4, A3, A1a, A1b, A2(+A2-2), A5, A6a, A6b (Phase 1); A7+A8, A9, A10, A11, A12,
A13, A14 (Phase 2); A15 F1-F4 nav structure (Phase 3)._
_**A16 Priority 2 (in progress):** Type Safety 100% (23/23 UI primitives), Accessibility advanced beyond the original 14-component baseline with new chat/project/settings/MCP batches, Test Coverage **56% → 80.06%+**. Added broad test coverage for `lib/api/client`, `lib/telemetry/client-errors`, app error/loading surfaces, `DatabaseSettings`, and a range of chat/UI controls. Coverage target is met; remaining work is the final accessibility sweep and any last audit polish._

### Session log — 2026-06-19d (wrap-up follow-up: chat search label + documentation sync)

Closed one more live accessibility gap after the larger 2026-06-19c batch:
- `frontend/components/Chat/ChatInterface.tsx` — labelled the sidebar session search input instead of relying on placeholder-only text
- `frontend/components/Chat/ChatInterface.test.tsx` — asserted the new labelled search textbox alongside the existing main-landmark/composer focus checks

Validation for the follow-up change: targeted `ChatInterface` tests passed and frontend `npm run typecheck` stayed clean.

### Session log — 2026-06-19c (next accessibility sweep: project/settings/server config)

Continued the A16 accessibility sweep across the next reviewed UI surfaces:
- `frontend/components/projects/ProjectDetail.tsx` — added `main`/`aside` landmarks, labelled back/upload/new-note actions, labelled message filtering, table semantics, and status/alert messaging for loading/error states
- `frontend/components/settings/ApiOverlayConfig.tsx` — labelled provider/model/endpoint/key controls, upgraded tier cards from click-only `div`s to keyboard-accessible buttons, added busy state + confidence slider labelling, and labelled copy/run/test actions
- `frontend/components/mcp/McpServerConfig.tsx` — labelled refresh/server-selection controls, busy state, alert semantics for error cards, and explicit inspect/close button labels
- Matching test updates landed in `ProjectDetail.test.tsx`, `ApiOverlayConfig.test.tsx`, and `McpServerConfig.test.tsx`

Validation for this batch: targeted tests for the three touched components passed, full frontend `npm run test` passed, `npm run typecheck` passed, and `npm run lint` remained warning-only (existing `ConfirmationDialog.test.tsx` unused var + generated coverage warning).

### Session log — 2026-06-19b (A16 coverage target reached + accessibility batch)

Raised frontend coverage to **80.06%** by adding and expanding tests for:
- `frontend/tests/unit/lib/api/client.test.ts` — CSRF, desktop auto-login recovery, provider-test errors, text/error parsing, failed-fetch handling
- `frontend/tests/unit/lib/telemetry/client-errors.test.ts` — Sentry fallback, global error/unhandled rejection wiring
- `frontend/app/app-surfaces.test.tsx` — `global-error`, `not-found`, `loading`, and route error boundaries across app sections
- `frontend/components/settings/DatabaseSettings.test.tsx` — status, refresh/start/stop flows, auto-start persistence, backup flows, cloud-config save
- targeted coverage follow-ups for `CommandBar`, `DetailedResponseView`, `DesktopStatus`, and `copy-button`

Accessibility improvements in this batch:
- `ChatInterface.tsx` — `main` landmark, composer autofocus, Ctrl/Cmd+Enter submit, live-region/busy state
- `DetailedResponseView.tsx` — labelled regions, metric/persona meter semantics, focusable persona cards, labelled actions
- `MessageBubble.tsx` — article semantics, polite live updates, explicit control labels
- `CommandBar.tsx` — Alt+K focus shortcut, labelled search, decorative icon hiding
- `AiModelSettings.tsx`, `KnowledgeIngestionSettings.tsx`, `McpClientConfig.tsx` — labelled switches/inputs/actions, busy states, alert/status semantics

Results: **80.06% statements**, **82.15% lines**, 0 app-surface files left at 0% coverage, and the targeted frontend tests/typecheck/lint pass after the latest changes.

### Session log — 2026-06-19 (A16 Priority 2 test coverage improvements)

Improved test coverage from 65.95% to 71.71% by creating 5 comprehensive test files for high-impact components:
- **AiModelSettings.test.tsx**: 12 tests covering provider loading, error handling, model selection, API key handling
- **ClientErrorBootstrap.test.tsx**: 6 tests covering error handler installation, cleanup lifecycle, mount/unmount
- **ConfirmationDialog.test.tsx**: 10 tests covering dialog states, risk tier badges, confirm/cancel actions
- **FeatureFlagGate.test.tsx**: 7 tests covering feature flag state, children/fallback rendering, complex JSX
- **route-error-fallback.test.tsx**: 10 tests covering error display, reset button, error reporting, icon rendering

Results: 31 new tests created, 280 total tests passing, 0 components with 0% coverage. Components coverage now at 71.71% (1214/1693 statements covered).

Validation: All tests pass with `npm run test`; pre-commit green; 0 ESLint/TypeScript errors.

### Session log — 2026-06-18b (A15 frontend nav/structure batch)

Map-first audit of all 29 `frontend/app` pages (detail: `REPO_AUDIT_LOG.md` A15 entry). Landed F1–F4;
F5/B2 deferred to next batch. User decisions: wire all orphaned surfaces into nav; consolidate to AppSidebar.
- F1: `tools/history` `/runs/${id}` (404, no `/runs/[id]` route) → `/runs/view?id=`.
- F2: removed orphaned duplicate `projects/[id]` (same `<ProjectDetail>` as `projects/view`; static-export casualty).
- F3: `AppSidebar` now single authoritative nav; `NavBar` reduced to chrome (logo/cloud/theme/account).
- F4: wired `/runs` (Trace Explorer), `/truth-engine`, `/analytics`, `/algorithms`, `/admin/compliance`
  into sidebar — were built + smoke-tested but had NO nav path. Grouped Workspace/Knowledge/Trace/System.
- Tests: updated `AppSidebar.test.tsx` + `NavBar.test.tsx`; component suite 51 files/150 tests pass; tsc+eslint clean.

### Session log — 2026-06-18 (pre-Phase-3 cleanup sweep)

Cleared low-risk outstanding carry-overs before opening A15 (full detail: `REPO_AUDIT_LOG.md`
"Pre-Phase-3 cleanup sweep"). Confirm-before-cut throughout (zero-importer scans, verify by concept).
- **A9-2 + bonus:** deleted dead `quad_models.py` (misnamed SDK-dup, stale axis semantics) and **6
  broken `verify_*.py` scripts** that ImportError on the A6a-deleted `LayerController`/`Layer3AgentEngine`
  (leaf scripts A6a's import-graph scan couldn't see).
- **A9-1:** removed `axis_role_mapper.py` (+ its 1 circular test); **kept** `persona_loader.py` +
  `persona_manager.py` CLI (user decision — working tool).
- **A9-3** docstring tightened; **A32-min** stale `audit_deep.py` ref dropped; **A13-min** verified N/A.
- **B1:** reconciled 4 stale "AES-256-GCM is target-state" docs to the AES-256-GCM-implemented reality.
- **C1/C2:** `ai_guardrail` typo fixed; defense-supervisor `user_role` "user"→"owner" (single-owner).
- **Deferred (correctly scoped):** A3-5→A26, A28-min→A28, B2→A15, C3→A16, C4/C5 open minors.
- Validation: quad 40 + supervisor/guardrail 16 pass; py_compile clean. 17 files (8 deletions).

### Session log — 2026-06-14

**A14 SDK audit repair** — Antigravity commit `087a9917` executed the A14 SDK audit
but introduced 5 bugs that collectively broke `import ukg_sdk` and all overlay tests:
- **ImportError** (`Coordinate` → `Coordinate17` rename not reflected in `__init__.py`)
- **`veto_reason` AttributeError** × 2 (field doesn't exist on `KAExecutionResult`)
- **Builtin KA handler registration guard** (builtins never wired with empty registry)
- **KA-61 regex gap** (`"ignore all previous instructions"` not caught)

Fixed all 5 in `008287ca`; 33 SDK tests pass, ruff clean. **Phase 2 is now complete.**

---

### Session log — 2026-06-13

Big session: A9 → A10 (+ full auth deprecation) → A11 → A12 → A13. Highlights:
- **Architecture reframe (user-confirmed):** app is **single-mode / OS-level auth** (even
  cloud = single-tenant VM). Multi-user auth is obsolete. See memory `architecture-single-mode`.
- **A9 `core/persona/quad/`** — reachability map; `quad_engine` is demo-only; resolved
  follow-on carry-overs A1a-2 (dead `LLMRouter` removed) + A1a-4 (fabricated refinement
  fallback fixed) + A10-password (werkzeug scrypt confirmed).
- **A10 `backend/security/`** — A3-4/A5-2/SC-2 resolved; **auth deprecation executed +
  BANKED at A+B+C-partial** (~1,900 LOC dead auth removed: zero_trust, token_manager, rbac;
  authz decorators collapsed; stale CSRF dropped). Remainder (admin UI, MFA, tenant_rls,
  User-field slim) is vestigial-but-wired → **deferred to A15/A16**. Past-audit
  reconciliation done (bounded — only multi-user features superseded).
- **A11 `core/axes/`** — verify-only; 17 axes register correctly, N3/N4/DUP-4 clean.
- **A12 `backend/storage/`** — DB-N/DB-C/DB-M re-confirmed live; **fixed RT-10** (atomic
  settings write).
- **A13 `core/system/`** — verify-only; services live; DUP-2 = 3 distinct orchestrators;
  SekreEngine wired live.
- **4 stale-plan corrections caught** before harm: Phase-C auth removals (keep-path),
  DUP-2 (retained, not deleted), TV-6 (Socket.IO is gateway/websocket), DB-M naming.
- Every step committed + pushed, pre-commit green, all trackers synced.

> **Deferred auth-deprecation work (for A15/A16, frontend-coordinated):** admin user-mgmt
> routes (↔ `frontend/app/admin/page.tsx`), MFA (`mfa.py` + `User.mfa_*` ↔ 3 frontend
> files), `tenant_rls.py` (Postgres RLS + startup + metrics), `User.role/is_admin` slim.
> Full plan + entanglement map: `docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md`.

This document captures the current working state of the DataLogicEngine desktop
app, the issues fixed in recent sessions, the build/deploy process, and the
known-good verification steps. It is the primary handoff reference; the
`docs/WINDOWS_11_LOCAL_RUNBOOK.md` has the detailed local-run instructions.

> **Audit Plan v2.0 progress (2026-06-11).** Working through
> `docs/audits/DataLogicEngine_Complete_Audit_Plan_v2.md`. Per-session detail
> lives in `REPO_AUDIT_LOG.md`; the live status table is in
> [Section 8](#8-open--next).
>
> | Session | Scope | Commit | Result |
> |---|---|---|---|
> | Sprint 0 | N3 delete legacy axes, N4 Axis 4/5 + honeycomb Axis-3 bug | `821737d1` | ✅ |
> | A4 | `local_model_acceleration/` | `821737d1` | ✅ A4-1/2/3 fixed |
> | A3 | `llm_gateway/` + N2 defense supervisor wired | `1ddeec49` | ✅ |
> | A1a | `truth_core/` + `truth_gate/` | `86486a78` | ✅ A1a-1 fixed |
> | A1b | `truth_memory/` + `truth_link/` | `5027fc3b` | ✅ A3-3/A1a-3 + A4-7 resolved |
> | A2 | `dsqp/` — patent claim | `4390c608` | ✅ matches disclosure; validator process-aware (A2-1) |
> | A2-2 | DSQP LLM-assisted construction | `a1784a17` | ✅ query-derived personas; offline fallback kept |
> | A5 | `dmrf/` — 17-axis router | `5d8dc848` | ✅ all 17 axes; no MLflow conflict; A5-1 wired DMRFDesktopConfig |
> | A6a | `core/simulation/` L1–L5 | `2afe2d14` | ✅ L5 override fixed; 12 dead legacy files removed |
> | A6b | `core/simulation/` L6–L10 + SEKRE | `62aa320f` | ✅ **N1 SEKRE wired**; L6–L10 mapped (no deletions) |
> | **— PHASE 1 COMPLETE (8/8) —** | | | |
> | A7+A8 (Phase 2) | `knowledge_algorithms/` (125 KAs) | `e7836182` | ✅ 125/125 registry resolve; 117 real + 8 compact + 0 stub; KA-113 + KA-005 + A5-3 fixes |
> | A9 (Phase 2) | `core/persona/quad/` | `5a1353c9` | ✅ models/sufficiency/pod_orch/math LIVE (DUP-5 clean); quad_engine demo-only; A1a-2/A1a-4 resolved |
> | A10 (Phase 2) | `backend/security/` | `b1a92674` | ✅ A3-4/A5-2/SC-2 + password resolved; **auth deprecation A+B+C-partial** (−1,900 LOC dead auth); remainder → A15/A16 |
> | A11 (Phase 2) | `core/axes/` | `85c114fe` | ✅ verify-only — 17 axes register; N3/N4/DUP-4 clean |
> | A12 (Phase 2) | `backend/storage/` | `cea5039e` | ✅ DB-N/DB-C/DB-M live; **RT-10 atomic-write fix** |
> | A13 (Phase 2) | `core/system/` | `4a66ebff` | ✅ verify-only — services live; DUP-2 = 3 distinct orchestrators; SekreEngine wired |
> | A14 (Phase 2) | `sdk/UKG_Python_SDK/` | `008287ca` | ✅ SDK surface confirmed; 5 Antigravity bugs fixed (ImportError + veto_reason AttributeError + registry guard + builtins veto_reason + KA-61 regex); 33 tests pass |
> | **— PHASE 2 COMPLETE (A7–A14) —** | | | |
> | **A15** | `frontend/app/` (pages) | — | **NEXT** — Phase 3 frontend; deferred auth removals (admin UI, MFA, tenant_rls, User-slim) land here |
>
> Status correction (recorded Sprint 0): RT-1..RT-18 were already completed
> 2026-06-07/08 (`df29906b`, `0eb2b0bb`, `cc01c15b`; `df29906b` also migrated
> `routes/` → `backend/routes/`) — the v2.0 plan listed them from a stale
> snapshot. Full suite after A6b: **2047 passed / 21 skipped / 0 failed**,
> ruff clean. Both June-10-scan disconnected components are now wired:
> N2 (defense_supervisor, A3) and N1 (SEKRE, A6b).

---

## 1. Current State (2026-05-30)

- Desktop app builds, packages (NSIS), installs, and uninstalls successfully.
- The installer is at the repo root: `DataLogicEngine Setup Latest.exe`.
- Installed per-machine to `C:\Program Files\DataLogicEngine Desktop\`.
- Both provider API keys in `C:\software\DataLogicEngine\API KEY\key.txt` were
  verified valid against the live provider APIs:
  - OpenAI (`sk-proj-…`): valid, 118 models accessible.
  - Gemini (`AQ.Ab8RN6…`): valid, 50 models accessible (works as a Google AI
    Studio key despite the non-`AIza` prefix).
- Uninstall is discoverable via "Uninstall DataLogicEngine" shortcuts on the
  Desktop and Start Menu (created by `frontend/electron/installer.nsh`).

## 2. Root Cause Found This Session (important)

Every earlier "rebuild" only rebuilt the **frontend**. The Python backend bundled
in the installer (`dist/DataLogic_Backend/DataLogic_Backend.exe`) was stale
(built 2026-05-21), so the shipped app ran old backend code regardless of source
fixes. Symptoms this produced:

- `404` for `/api/v1/gateway/dsqp-persona-profiles` and
  `/api/v1/gateway/network-status` (these exist in current source but not the
  old build) — surfaced as the Live Trace `[object Object]` and the System
  Output 404 in the UI.
- The Flask app-context provider fix never took effect → chat failed with
  "No active providers found" / "added to the local offline queue".
- The Settings `size_bytes` guard appeared not to apply.

**Fix:** `frontend/build_installer.ps1` now rebuilds the PyInstaller backend
(`scripts/build_backend.py`) and re-applies the electron-builder npm patch
(`npm run fix:eb`) **before** packaging. The shipped backend now always matches
source.

## 3. Fixes Landed (committed to `main`)

- **Gateway app-context** (`backend/llm_gateway/gateway.py`): `_get_eligible_providers()`
  wraps the `LLMProvider.query` in an explicit `app.app_context()` so provider
  resolution works from async coroutines (Electron-spawned backend).
- **API key forwarding** (`frontend/electron/main.ts`): keys from `.env`
  (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, …) are merged into
  the spawned backend process env.
- **Settings crash** (`frontend/components/settings/DatabaseSettings.tsx`):
  guarded undefined storage-backend metrics with `(metric ?? {})` and optional
  chaining; absent local backends render "0 B / Not created".
- **Provider test errors** (`backend/llm_gateway/api.py` `test_provider`):
  returns specific statuses — `invalid_api_key` (401), `rate_limited` (429),
  `invalid_model` (422), `network_error` (504) — instead of a generic message.
- **Cross-provider failover** already exists in `LLMGateway.process()`: providers
  tried in priority order; auth/`401`/`invalid api key` is non-retryable for that
  provider and triggers failover to the next (e.g. OpenAI → Gemini).
- **Uninstall shortcuts** (`frontend/electron/installer.nsh`): Desktop + Start
  Menu shortcuts created on install, removed on uninstall.
- **Build tooling** (`frontend/scripts/patch-electron-builder.mjs`): durable fix
  for the electron-builder v26 + NVM-for-Windows npm collector failure
  ("No JSON content found in output"). Runs on `postinstall` and before
  `electron:dist`.
- **Unsigned local builds**: `frontend/electron-builder.yml` sets
  `verifyUpdateCodeSignature: false`.

## 4. Environment Notes (Windows dev machine)

- **Two venvs exist:**
  - `.venv311` — Python **3.11.14**, real install. **Use this** for backend
    build and scripts. Has flask, sqlalchemy, cryptography, openai, pyinstaller.
    (Missing `anthropic` — only needed if using the Anthropic provider.)
  - `.venv` — Python 3.13 from the **Windows Store**. Sandboxed; subprocess
    stdout is unreliable. **Avoid for scripting.**
- **Node.js**: NVM-for-Windows at `C:\nvm4w\nodejs` (node.exe + npm).
- **Git**: `C:\Program Files\Git\cmd\git.exe` (not on PATH; call full path).
- Reliable script execution pattern in PowerShell:
  `Start-Process -FilePath <py> -ArgumentList <script> -NoNewWindow -Wait -PassThru`
  with `-RedirectStandardOutput`/`-RedirectStandardError` to files.

## 5. Build & Deploy Process

Full rebuild + repackage (preferred, does everything in order):

```powershell
# Run elevated; rebuilds backend, frontend, patches eb, packages NSIS, copies to root
powershell -ExecutionPolicy Bypass -File frontend\build_installer.ps1
```

Manual steps (if doing piecemeal):

```powershell
# 1. Backend (PyInstaller) — REQUIRED whenever backend source changes
.\.venv311\Scripts\python.exe scripts\build_backend.py
# 2. Frontend
cd frontend
C:\nvm4w\nodejs\node.exe node_modules\next\dist\bin\next build
C:\nvm4w\nodejs\node.exe node_modules\typescript\bin\tsc -p electron
# 3. Patch electron-builder for NVM, then package
node scripts\patch-electron-builder.mjs
C:\nvm4w\nodejs\node.exe node_modules\electron-builder\out\cli\cli.js --win --config electron-builder.yml
```

Before packaging, ensure no `DataLogic_Backend.exe` process is running and that
`frontend\dist\win-unpacked` is removed (stale locked files cause
`ERR_ELECTRON_BUILDER_CANNOT_EXECUTE`).

## 6. Install / Uninstall

- **Install**: run `DataLogicEngine Setup Latest.exe` (elevated). Wizard mode.
- **Uninstall (interactive)**: Desktop or Start Menu "Uninstall DataLogicEngine".
- **Uninstall (silent, blocking)**:
  ```powershell
  $u = 'C:\Program Files\DataLogicEngine Desktop\Uninstall DataLogicEngine Desktop.exe'
  $tmp = Join-Path $env:TEMP 'dle_uninst.exe'; Copy-Item $u $tmp -Force
  Start-Process $tmp -ArgumentList '/S','/allusers','_?=C:\Program Files\DataLogicEngine Desktop' -Verb RunAs -Wait
  ```

## 7. Verification After Install

1. Backend bundled timestamp matches the latest backend build:
   `Get-Item 'C:\Program Files\DataLogicEngine Desktop\resources\backend\DataLogic_Backend.exe'`
2. Launch the app → **Enterprise AI** → send "hello" → expect a real model reply.
3. Open **Settings** → loads without the `size_bytes` crash.
4. **Live Trace** panel shows no `[object Object]`.
5. Live runtime log (for debugging):
   `C:\Users\<user>\AppData\Roaming\DataLogicEngine Desktop\logs\desktop-runtime.log`
   — should NOT show 404s for `/gateway/dsqp-persona-profiles` or
   `/gateway/network-status`.

## 8. Open / Next

### Status (2026-06-11)

- ~~RT-1 multimodal handler bug~~ — done `df29906b`/`0eb2b0bb` (handlers renamed).
- ~~RT-2 unauthenticated `/search/suggest`~~ — done `0eb2b0bb`.
- ~~RT-3..RT-18 routes sprint~~ — all 18 closed; see
  `docs/audits/DataLogicEngine_Routes_Audit.md` resolution table.
- ~~N3 legacy axis files~~ — deleted this session (+ orphaned enums + `__init__.py`).
- ~~N4 Axis 4/5 gap~~ — resolved this session; honeycomb_api Axis-5 lookup bug
  fixed + auth added.
- ~~A4 local_model_acceleration audit~~ — complete; A4-1/2/3 fixed, A4-4/5/7/8
  assigned forward. See `REPO_AUDIT_LOG.md`.

- ~~A3 llm_gateway audit~~ — complete 2026-06-11. Governance enforced
  per-request confirmed; DMRF flag wired; classifier vs KA-113 = different
  axes (model tier vs reasoning tier), by design. Fixed: 4 unauthenticated
  desktop status endpoints (now signed `desktopFetch` + auth), N2 wired,
  A4-4 tier re-probe, A4-5 stream guard, A4-8 `process()` harness.
  Details in `REPO_AUDIT_LOG.md` (A3 entry).
- ~~N2 defense_supervisor~~ — WIRED: `backend/security/defense_supervisor.py`
  screens pipeline queries on the cheapest local Ollama tier (JSON mode,
  8 s timeout, fail-open). Kill switch `DEFENSE_SUPERVISOR_ENABLED=false`.
  Prompt moved to `backend/security/prompts/defense_supervisor.txt`.

- ~~A1a truth_core + truth_gate audit~~ — complete 2026-06-11. Engine is the
  real entry point; L9 max-5 enforced; L10 emergence gate makes real
  decisions; L7 AGI planner real; TruthGate L8 fail-closed. Fixed hardcoded
  `processing_time_ms: 500` in the audit trail. Details in `REPO_AUDIT_LOG.md`
  (A1a entry).

- ~~A1b truth_memory + truth_link audit~~ — complete 2026-06-11 (`5027fc3b`).
  Resolved **A3-3/A1a-3**: confirmed via canonical `dmrf/models.py` `TIER_ORDER`
  that `moderate` = Tier 2; the audit-commit/footer gate wrongly excluded it,
  so Tier 2 runs were skipping audit bundles. Exclusion set normalized to
  `{"", "0", "t0", "1", "t1", "trivial"}` with `.lower().strip()` (also fixes
  the SDK's `"T1"`/`"T2"` casing) across `_build_response`, `_create_trace_run`,
  and the new cache-hit path. Resolved **A4-7**: cache stores/returns
  `original_run_id`; Tier 2+ cache hits now write a `cache_hit` compliance
  `TruthAuditEvent` linking new + original run ids. (Reviewed 2026-06-11: API
  call matches `TruthAuditRecorder.log_event` signature; 127 focused tests pass.)

- ~~A2 dsqp patent-claim audit~~ — complete 2026-06-11. Verdict: matches
  `docs/ip/dsqp_technical_disclosure.md` as the explicitly-scoped deterministic
  slice. 7-step per-axis chain, per-query construction (no cross-query cache),
  registry = question specs, templates = questions only — all confirmed. Fixed
  A2-1 (validator now checks the self-questioning *process* ran, not just
  coverage). Documented A2-2: deterministic answers are axis-keyed scaffolds —
  implement LLM-assisted construction before any external IP filing. Details in
  `REPO_AUDIT_LOG.md` (A2 entry).

- ~~A2-2 DSQP LLM-assisted construction~~ — built 2026-06-11. `dsqp_answer_generator.py`
  generates the 7 persona components from the query on the local model (per-axis
  JSON call), with per-component fallback to the deterministic scaffold; provenance
  + `construction_mode` recorded. `DSQP_LLM_ASSISTED=false` kill switch;
  conftest pins it off for tests. Personas are now genuinely query-derived. Details
  in `REPO_AUDIT_LOG.md` (A2-2 entry).

- ~~A5 dmrf 17-axis router audit~~ — complete 2026-06-11. All 17 axes
  exercised; tier_classifier is the reasoning tier (distinct from the gateway's
  model-escalation classifier); convergence_policy + frost_bridge real; no
  MLflow experiment conflict; 4 adapters real delegations. Fixed A5-1 (wired
  the orphaned `DMRFDesktopConfig`). Forwarded A5-2 (5 overlapping injection
  defenses → A10), A5-3 (unused `ka_controller` param). `REPO_AUDIT_LOG.md`
  (A5 entry).

- ~~A6a core/simulation L1–L5 map~~ — complete 2026-06-11. Live path:
  `SimulationEngine` (app_orchestrator/master_workflow/system_initializer) wires
  L4–L10; master_workflow wires L1–L3. L1–L5 live = layer1_entry / layer2_knowledge
  / layer3_expert / layer4_reasoning / layer5_integration. Fixed A6a-1 (L5
  override). Removed 12 zero-importer dead files (2 dead orchestrators +
  their exclusive layer-variant chains). `REPO_AUDIT_LOG.md` (A6a entry).

- ~~A6b L6–L10 + SEKRE~~ — complete 2026-06-11. Live L6–L10 mapped
  (layer6_enhancement / layer7_agi_system / layer8_quantum / layer9_recursive
  [max-5 enforced] / layer10_synthesis); the 4 variant files are demo/research
  (kept); `legacy_simulation_engine` + `agentic/` live (kept). **N1 SEKRE wired**
  post-L10 in `SimulationEngine` (fail-safe, Tier-3+ gate, read-only default).
  `REPO_AUDIT_LOG.md` (A6b entry).

## ✅ Phase 1 complete — Phase 2 (Reasoning Depth) in progress

- ~~A7 partial — `knowledge_algorithms/` registry/config map + high-risk~~
  done 2026-06-11. All 125 registry entries resolve to importable callables;
  configs are by-convention `config/ka_NN_config.json` (graceful fallback,
  `ka_33` reserved); KA-117 rename confirmed. High-risk KAs verified real
  (KA-014 confidence, KA-061 adversarial fail-closed, KA-005 classification,
  KA-116/032/034/024). **NOTE: the plan's high-risk KA *numbers* were stale**
  (e.g. real `ka_107` = disaster_recovery, not "reasoning boundary"; entropy is
  `ka_116`, not 102) — verify by concept, not the plan's numbering. Fixed A7-1
  (KA-113 length-only → multi-signal). `REPO_AUDIT_LOG.md` (A7 entry).

- ~~A8 per-KA rating sweep + A5-3~~ done 2026-06-11. All 125 KAs rated:
  117 real + 8 compact-real (7 `l10/` modules delegating to `l10/common`, KA-112)
  + 0 stub; 0 orphan configs. A5-3 resolved — KA-005 now emits `suggested_tier`
  (fixing TruthCore's previously-dead KA-005 tiering branch) and the unused
  `DMRFTierClassifier.ka_controller` param was dropped. The 100–117 band are
  *representational* infra KAs (describe ops; the real celery/redis layer
  performs them). `REPO_AUDIT_LOG.md` (A8 entry).

### ✅ A9 — `core/persona/quad/` complete (2026-06-12)

Reachability map done (full detail in `REPO_AUDIT_LOG.md` A9 entry). Verdict:
- **LIVE / canonical:** `models.py` (PersonaProfile 7-component + QueryState),
  `persona_scaling/sufficiency.py` (DUP-5 clean — `GatewayPersonaSufficiencyTool`
  + Phase-5 `PersonaSufficiencyTool`), `persona_scaling/profiles.py`,
  `pod_models.py`, `pod_orchestrator/`, `mathematical_framework/`.
- **DEMO-ONLY:** `quad_engine.py` — heuristic 4-persona engine, importers are demo
  scripts + 1 test only. **Plan premise was wrong**: the real query-time 7-component
  construction is `core/system/persona_construction_service.py` → DSQP, not here.
  Fixed its stale docstring (named the A6a-deleted `layer2_legacy_knowledge.py`).
- **Forwarded carry-overs:** A9-1 `axis_role_mapper.py` (test-only) +
  `persona_loader.py` (script-only) → A29; A9-2 `quad_models.py` (misnamed L3
  models, dup of SDK, 1 script importer) → A14/A29; A9-3 `__init__.py` docstring
  → A31. No risky deletions this session. `tests/persona/quad/` 41 passed.

### A10 — `backend/security/` IN PROGRESS (2026-06-13)

**Major reframe (user-confirmed):** app is now **local-first, single operating mode**;
auth is at the **OS level** (even cloud = single-tenant VM). The multi-user model is
gone. See memory `architecture-single-mode`. This makes a whole sub-stack obsolete.

Carry-overs resolved (REPO_AUDIT_LOG.md A10 entry):
- **A3-4 — ✅ N/A by design** (one owner: `user_role` moot; HONEYPOT→BLOCK correct).
- **A5-2 — ✅ keep all five** injection defenses (defense-in-depth union, distinct
  stages/techniques; still relevant — input protection is independent of user model).
- **SC-2 — ✅ AES-256-GCM is the active data cipher** (`encryption_manager`); Fernet
  only wraps the KEK + legacy fallback. Docs reconciliation remains.
- **Password hashing — ✅ verified 2026-06-12** (werkzeug `scrypt:32768:8:1`); don't re-chase.

**Headline:** multi-user auth/RBAC/session/MFA/tenancy stack is architecturally
obsolete. Desktop single-user auth already works (Windows SID + signed Electron
loopback). `zero_trust.py` + `token_manager.py` are already fully dead (test-only).
Full removal blast radius: **147 auth-decorator usages** + ~29/172 test files.

> **Decision (user, 2026-06-13): plan full deprecation before any code changes.**
> Plan delivered → **`docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md`** (6 phases,
> A–F; Phase A = delete the 2 dead modules, risk-free). **Awaiting review/approval —
> NO auth code changed yet.** Next session: review plan, approve a starting phase.

Other carry-overs: A3-4 + A5-2 (injection-defense consolidation) + SC-2 in A10;
A3-5 in A26; A18-pre in A18. Full list in the plan's carry-over table.

Still open for later sessions:
- A2-2 (future DSQP slice, pre-IP): LLM-assisted answer generation.
- A3-4 (for A10): supervisor `user_role` enrichment; HONEYPOT handling with
  `active_defense.py`.
- ~~A1a-2~~ ✅ done 2026-06-12: `truth_core/router.py` `LLMRouter` dead code removed.
- ~~A1a-4~~ ✅ done 2026-06-12: fabricated "Mock result" fallback → honest
  `skipped`/0.0 (was polluting memory graph + downstream context).

Phase 1 remaining order: A5 → A6a → A6b
- A5: `backend/dmrf/` — 17-axis router, FROST bridge, truth integration adapters

**Still unwired (from June 10 scan):**
- `core/self_evolving/sekre_engine.py` — wire after A6b (layer map first)

### Carry-over from prior sessions

- ~~End-to-end chat~~ — resolved (Section 10). gpt-5.5 returns real replies.
- ~~`anthropic` package~~ — non-issue; provider uses raw `httpx`.
- **Minor:** `RAG context retrieval failed: Access is denied ... llama_index` in
  installed app. Non-fatal; move RAG index dir to per-user runtime dir when needed.
- **Minor:** Gemini/Anthropic providers still use async `httpx`. Apply sync-call
  pattern from Section 10 if either becomes the active chat provider.
- Settings UI: surface `test_provider` status codes inline in `ApiOverlayConfig.tsx`.

## 9. CI Status (2026-05-30 night)

All five originally-failing checks were fixed and pushed to `main`, along with
the chain of jobs that fixing them unmasked (frontend unit tests behind the
typecheck gate; docker-build jobs gated on upstream success). Final result:
**Security Scan, Deploy, and CI/CD Pipeline all green.**

Highlights (full detail in `TODO.md` → "CI And Security Evidence"):
- Dependency scan: the stale `chromadb==0.5.23` pin locked `transformers` onto a
  vulnerable build; bumping `transformers` then exposed that `chromadb 1.x` is in
  the pre-auth CVE range `GHSA-f4j7-r4q5-qw2c` (server-mode only; not reachable
  via the embedded `PersistentClient`). Final pin `chromadb==0.6.3` clears both —
  it is `<1.0.0` and still allows CVE-free `transformers 5.9.0`.
- Bandit B608 `# nosec` on the `sqlite_master` row-count query.
- Frontend typecheck + `LiveTracePanel` unit-test mock fix.
- `verify_docs_references.py` no longer flags absolute API routes (`/api/v1/*`);
  fixed a broken diagram reference in `docs/README.md`.
- npm-audit job deflaked (skip electron binary download).
- Both Dockerfiles copy `frontend/scripts` before `npm ci` (postinstall fix).

## 10. Desktop Chat Enablement (2026-05-31)

End-to-end Enterprise AI chat was failing ("The local desktop queue saved this
request for replay…"). The root cause was a chain of three independent problems,
all now fixed and committed to `main`:

1. **`ukg_sdk` not packaged** (`backend.spec`). The gateway imports its provider
   HTTP clients / overlay from the in-repo SDK via a runtime `sys.path` insert
   that does not exist in the frozen app. The bundled backend logged
   `No module named 'ukg_sdk'`, so `_create_sdk_provider()` returned `None` and
   every request went to the offline queue. Fix: add `sdk/UKG_Python_SDK` to
   `pathex` + `collect_submodules('ukg_sdk')` + `collect_data_files('ukg_sdk')`.
   Also bundled `tiktoken_ext.openai_public` (the `cl100k_base` plugin) so RAG
   token counting stops raising `Unknown encoding cl100k_base`.

2. **gpt-5.5 called incorrectly.** gpt-5.5 is a *reasoning* model: it rejects a
   custom `temperature` and counts reasoning tokens against `max_output_tokens`.
   The provider sent `temperature` and a tiny `max_output_tokens` (the Test Model
   probe sent `5`, below the Responses-API minimum of 16). Fix
   (`ukg_sdk/providers/openai.py`): drop `temperature` for gpt-5.x/o-series, send
   `reasoning={"effort": "medium"}`, and floor `max_output_tokens` to 1024 for
   reasoning models. OpenAI standardized to a **single model, `gpt-5.5`**
   (`model_defaults.py`, `AiModelSettings.tsx`).

3. **Async client vs. Flask's event loop** (the subtle one). Test Model (a single
   isolated call) worked, but the chat runs the multi-step `UKGOverlay` pipeline,
   and Flask runs `async def` views via `asgiref.async_to_sync` on a reused
   thread-local loop. Creating a fresh `AsyncOpenAI` (asyncio/httpx) client per
   call across those steps mismanaged the client lifecycle ("Event loop is
   closed") and every attempt failed. Fix: call the **synchronous** OpenAI client
   (`self.client.responses.create`) — a blocking call has no loop-bound resources
   to mismanage. Validated against the live key: direct call, full
   `UKGOverlay.run`, and two sequential requests via `async_to_sync` all return
   real answers. (Note: the backend does **not** use eventlet — it is not bundled
   and nothing calls `monkey_patch()`; the issue was purely `async_to_sync`.)

**Desktop UI fixes (same session):**
- `ChatInterface.tsx`: replaced mojibaked emoji in the header/avatars (rendered
  as `ðŸŽ¯`/`ðŸ¤–`) with lucide icons (`Target`/`Bot`/`User`).
- `LiveTracePanel.tsx`: error display defensively coerced to a string so it can
  never render `[object Object]`.
- `DesktopStatus.tsx`: the Desktop Engine status panel is now **minimizable** — a
  header `−` collapses it to a small corner pill (click to reopen); the
  preference persists via `lib/state/storage`.
- `NetworkState._configured_providers()` (`gateway.py`): counts active DB
  providers with a saved key, not just `*_API_KEY` env vars, so the desktop
  status reports ONLINE/DEGRADED (not OFFLINE) after a key is saved in Settings.
  (Saving a key never overwrote the other provider — the DB stores one row per
  provider; the moving "Default" badge is just the `is_default` flag.)

**Refactor reverted.** A large, unpushed, in-progress modularization (splitting
`models.py`/routes/`app.py`/tracing into packages) had broken ~19 tests and the
security_scan suite. Since it was local-only, delivered no functional value, and
the chat fix is independent of it, it was reverted with
`git reset --hard origin/main` (recoverable via reflog at `f9c427fc`). All KA
upgrades and the chat fixes are preserved on `main`.

**Verification after installing the latest build:** launch → Enterprise AI → send
"hello" → expect a real gpt-5.5 reply (not the offline-queue message). The
runtime log should show **no** `No module named 'ukg_sdk'` and **no**
`Provider attempt exception`. `network-status` should report
`configured_providers: ["openai", …]` with `state: DEGRADED` (expected on desktop
with no local model) rather than `OFFLINE`.
