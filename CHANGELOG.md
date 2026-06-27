# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Stale bundled backend shipped in the installer (root cause of recurring desktop errors)**: the PyInstaller backend (`dist/DataLogic_Backend/DataLogic_Backend.exe`) was not rebuilt as part of the frontend/installer rebuild, so the packaged app ran a backend from an earlier build. This caused `404` responses for `/api/v1/gateway/dsqp-persona-profiles` and `/api/v1/gateway/network-status` (surfacing as the Live Trace `[object Object]` and System Output 404), kept the Flask app-context provider fix inactive, and made chat fail. The build pipeline now rebuilds the backend before packaging so the shipped backend always matches source.
- **Provider test now reports the real reason**: `test_provider` in `backend/llm_gateway/api.py` previously returned a generic "Provider connectivity check failed". It now classifies the underlying error and returns a specific status/message — `invalid_api_key` (401), `rate_limited` (429), `invalid_model` (422), or `network_error` (504) — so the UI can tell the user an API key is invalid instead of a generic failure.
- **LLM Gateway — "No active providers found" in desktop mode**: `_get_eligible_providers()` in `backend/llm_gateway/gateway.py` queried `LLMProvider.query` outside a Flask application context when invoked from async coroutines (Electron-spawned backend), raising "Working outside of application context", silently falling back to env-only provider discovery, and ultimately failing every chat with "No active providers found". The DB query is now wrapped in an explicit `app.app_context()` push obtained via `current_app._get_current_object()`.
- **Desktop API keys not forwarded to backend**: Electron `startBackend()` in `frontend/electron/main.ts` spawned the Python backend without forwarding API keys from `.env`. Provider keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, etc.) are now parsed from `.env` and merged into the backend process environment (with inherited `process.env` taking precedence).
- **Settings page crash — `Cannot read properties of undefined (reading 'size_bytes')`**: `DatabaseSettings.tsx` assumed every storage backend metric object was defined. When a backend (Neo4j/Chroma/object store) is not running in local SQLite desktop mode, the metric is `undefined` and the component crashed the whole Settings route. Hardened with `(metric ?? {})` and optional chaining on `data?.size_bytes` / `lastBackup?.size_bytes`; absent backends now render "0 B / Not created" instead of crashing.

### Removed
- **Legacy external SaaS connectors (Jira, Salesforce)**: removed the
  `backend/mcp_server/tools/jira.py` and `backend/mcp_server/tools/salesforce.py`
  MCP connectors, their registrations, the Jira webhook processor in
  `backend/webhook_server/webhook_server.py`, and the `jira`/`salesforce` entries
  in `KNOWN_CONNECTORS`. These external SaaS integrations are not part of the
  local-first / desktop-only product. Connector-specific tests were removed and
  generic connector-framework tests repointed to the `github` connector label.
- **Multi-user authentication stack (single-mode consolidation)**: retired the
  obsolete multi-user RBAC, web login/register, MFA/TOTP, SSO/OIDC, role, and
  tenant-isolation/RLS paths in favor of single-owner OS-level desktop auth
  (`current_user_is_owner()` + desktop auto-login). Dropped the `OAuthAccount`
  model/table (migration `d6e7f8a9b0c1_drop_oauth_accounts_table`), removed
  `backend/security/tenant_rls.py`, and retired dead security modules and
  one-off audit scripts. `tenant_id` columns are kept as vestigial. See
  [`REPO_AUDIT_LOG.md`](REPO_AUDIT_LOG.md) for the full v2.0 audit record.

### Changed
- Replaced explicit KA stub behavior in `KA-011`, `KA-033`, `KA-039`, `KA-048`, `KA-077`, `KA-109`, and `KA-Master` with deterministic local implementations and focused tests.
- **Documentation accuracy sweep (v2.0 audit)**: reviewed and corrected the
  `docs/` tree, `docs/diagrams/`, and root docs against the post-audit
  single-mode application — removed stale multi-user/SSO/RBAC/MFA descriptions,
  fixed migrated `routes/` -> `backend/routes/` paths, refreshed test baselines
  (`1769 passed, 19 skipped`), corrected the Fernet/AES-128 note to AES-256-GCM,
  and archived superseded planning docs under `docs/archive/`.
- **Single canonical README**: consolidated the duplicate `.github/README.md`
  (which GitHub rendered on the homepage) and root `README.md` into one
  source-of-truth README at the repository root, eliminating the precedence
  ambiguity that hid edits. Brought the displayed content to single-mode
  accuracy (canonical `python main.py` entry point, 6-tier escalation engine,
  removed RBAC/MFA/SSO/JWT/multi-tenant claims, dead `/auth/login` example
  replaced with desktop auto-login), added a dated status snapshot, and verified
  the Windows desktop installer rebuilds cleanly end-to-end (PyInstaller backend
  -> Next.js export -> Electron/NSIS) with the freshly built backend embedded.
- **Test suite aligned to desktop-only auth**: added a route-independent
  `seed_login_session` helper in `tests/conftest.py` and refactored the
  `authenticated_client`/admin/owner fixtures and per-file login helpers to seed a
  Flask-Login session directly (matching the desktop auto-login end state) instead
  of calling the removed public web `/register` and `/login` routes. Removed the
  obsolete `TestAuthenticationEndpoints` class and dropped the removed auth
  endpoints from the canonical-failure route contract.
- **Bandit MD5 hardening**: marked non-security MD5 content fingerprints with
  `usedforsecurity=False` in `core/simulation/pov_delta.py`,
  `core/simulation/query_analysis_system.py`, and
  `core/simulation/coordinate_system.py`, clearing the high-confidence findings in
  the Bandit delta gate.
- **RAG embedding failover tests** now set `ALLOW_MOCK_EMBEDDINGS=true` when
  exercising the development/testing mock-embedding fallback, matching the
  fail-closed production behaviour of `RAGService._default_embedding`.
- **Docs**: corrected stale paths in `docs/MCP_INTEGRATION.md`
  (`backend/mcp_api.py` -> `routes/mcp_routes.py`,
  `frontend/src/pages/MCPConsolePage.js` -> `frontend/app/mcp/page.tsx`); added
  `docs/REPO_AUDIT_LOG.md` recording the 2026-06-04 audit session and the open
  backlog for future audits.
- **Layering fix — integrity helpers moved to `core/`**: the pure, dependency-free hashing/HMAC helpers in `backend/security/integrity.py` moved to `core/security/integrity.py`. This removes two `core -> backend` import inversions (`core/simulation/trace_system.py`, `core/system/frost_service.py`), restoring the documented `backend -> core` dependency direction. `backend/security/integrity.py` is now a backwards-compatible re-export shim, so existing `from backend.security.integrity import ...` call sites (e.g. `backend/security/export_integrity.py`) continue to work unchanged. No behavior change.

### Notes
- Cross-provider failover already exists in `LLMGateway.process()`: providers are tried in priority order, and an authentication/`401`/`invalid api key` error is treated as non-retryable for that provider so the gateway immediately falls over to the next configured provider (e.g. OpenAI → Gemini). This path only works when the current backend build is deployed (see stale-backend fix above).

### Build / Tooling
- **electron-builder v26 npm collector failure on Windows + NVM**: `app-builder-lib`'s `NpmNodeModulesCollector` failed with "No JSON content found in output" / `MODULE_NOT_FOUND` because `npm` was not resolvable in the subprocess `PATH` (NVM-for-Windows layout) and the `.cmd` → `.bat` → `cmd.exe` shell wrapper mangled paths containing spaces. Resolved by pointing the collector's npm path cache to a space-free `.cmd` shim that invokes `node.exe npm-runner.js` with full absolute paths; `npm-runner.js` rewrites `process.argv[1]` so npm-cli forwards `list --json` arguments correctly.
- **Unsigned local builds**: `electron-builder.yml` now sets `verifyUpdateCodeSignature: false` so unsigned developer/local NSIS builds complete without a provisioned code-signing certificate.

### Security
- Mitigated Dependabot alert 389 / CVE-2026-45829 by pinning `chromadb` to `0.5.23`, outside the vulnerable `>=1.0.0, <=1.5.9` range while no patched 1.x release is available.
- **Dependency vulnerabilities cleared (v2.0 audit)**: after the audit dependency pass, both `pip-audit` (Python) and `npm audit` (Node) report no known advisories.

## [4.2.0] - 2026-05-12

### Added
- **User AI Preferences**: per-user `UserAIPreferences` DB model with Alembic migration; persisted via `GET/POST /api/settings/ai`; gateway wires preferred provider, preferred model, and `ai_processing_enabled` flag before routing each request.
- **AI processing toggle + chat history opt-out**: two toggle cards in Settings → AI Models backed by real DB state.
- **KA risk-tier classifier**: `backend/knowledge_algorithms/risk_classifier.py` classifies each Knowledge Algorithm as `read_only`, `write`, or `destructive`.
- **ConfirmationDialog**: reusable React dialog gated by risk tier with colour-coded badges and destructive styling (`frontend/components/ConfirmationDialog.tsx`).
- **Tool Execution History**: `/tools/history` audit log page for every KA invocation with status, tier badge, duration, triggered-by, and trace links.
- **AI provider/model badge**: each assistant chat message now shows the provider and model used.
- **Global privacy footer**: links to Privacy Policy, Cloud Services, and AI Limitations on every page.
- **Background activity disclosure**: card on `/settings/privacy` lists health checks, WebSocket keep-alives, and session refresh activity.

### Fixed
- **CI — pip-audit**: patched 12 CVEs across Flask, Authlib, PyJWT, cryptography, aiohttp, requests, langgraph, python-dotenv, markdown, Pillow, pypdf, and pytest.
- **CI — governance/frontend-build**: removed `eslint-plugin-storybook@10.3.6` (required storybook v10 peer dep, project uses v8); added `stories/**` to eslint global ignores to prevent hooks-rule violations in story files.
- **Unit tests**: updated `ApiErrorBoundary` and `ChatInterface` test assertions to match new user-facing copy.

### Changed
- `settings_routes.py` rewritten to persist AI preferences to DB (was stub/mock).
- `api-error-boundary.tsx`: improved error title ("Something went wrong") and actionable copy; retry button renamed "Try again".
- `ChatInterface.tsx`: improved API error message with actionable guidance including Settings link.

## [4.1.19] - 2026-02-17

### Changed
- Completed Phase 11 lint hardening pass for `E402` (`module-import-not-at-top-of-file`) across all remaining files.
- Normalized import placement in generated knowledge algorithm modules and logger-pattern files.
- Added explicit file-level `# ruff: noqa: E402` on bootstrap/runtime-order modules where deferred imports are intentional to prevent initialization-order regressions.
- Global lint debt is now fully cleared (`ruff check .` passes with no findings).

### Testing
- Debug/error sweep completed for this phase:
  - `.venv\Scripts\python.exe -m ruff check .` (pass)
  - `.venv\Scripts\python.exe -m py_compile` across all changed Python files (`131` files, pass)
  - `.venv\Scripts\python.exe -m pytest -q --no-cov tests/knowledge_algorithms/test_ka_bulk.py tests/truth_engine/test_layer10_emergence.py tests/truth_engine/test_layer9_meta_reasoning.py tests/truth_engine/test_truth_infrastructure.py sdk/UKG_Python_SDK/tests/test_truth_engine.py tests/integration_routes/test_app_route_wiring.py` (`271 passed`)

## [4.1.18] - 2026-02-17

### Changed
- Completed Phase 10 lint hardening pass focused on `E701` cleanup (multiple statements on one line).
- Converted all remaining single-line compound statements (`if/elif/except`) into block form across backend/core/routes/scripts/simulation/models.
- Global lint backlog reduced from `281` to `201`.
- Remaining global lint debt is now isolated to `E402` only (`module-import-not-at-top-of-file`).

### Testing
- Debug/error sweep completed for this phase:
  - `.venv\Scripts\python.exe -m ruff check . --select E701` (pass)
  - `.venv\Scripts\python.exe -m ruff check . --select E9,F63,F7,F821` (pass)
  - `.venv\Scripts\python.exe -m py_compile` across all changed Python files (`26` files, pass)
  - `.venv\Scripts\python.exe -m pytest -q --no-cov tests/knowledge_algorithms/test_ka_bulk.py tests/truth_engine/test_layer10_emergence.py tests/truth_engine/test_layer9_meta_reasoning.py tests/truth_engine/test_truth_infrastructure.py sdk/UKG_Python_SDK/tests/test_truth_engine.py` (`270 passed`)

## [4.1.17] - 2026-02-17

### Changed
- Completed an additional lint hardening pass across backend, core, simulation, demos, scripts, SDK, and tests for the active style-debt ruleset.
- Cleared all remaining violations for `E712`, `E722`, `E721`, `E711`, `E741`, `F811`, `F403`, `F401`, and `F841`.
- Reduced global lint backlog from `359` to `281`; remaining global debt is now limited to:
  - `E402`: 201
  - `E701`: 80

### Testing
- Debug/error sweep completed for this phase:
  - `.venv\Scripts\python.exe -m ruff check . --select E712,E722,E721,E711,E741,F811,F403,F401,F841` (pass)
  - `.venv\Scripts\python.exe -m ruff check . --select E9,F63,F7,F821` (pass)
  - `.venv\Scripts\python.exe -m py_compile` across all changed Python files (pass)
  - `.venv\Scripts\python.exe -m pytest -q --no-cov tests/knowledge_algorithms/test_ka_bulk.py tests/truth_engine/test_layer10_emergence.py tests/truth_engine/test_layer9_meta_reasoning.py tests/truth_engine/test_truth_infrastructure.py sdk/UKG_Python_SDK/tests/test_truth_engine.py` (`270 passed`)
- Note:
  - Running the same pytest selection with coverage enabled fails project coverage gate (`38.94%` vs required `70%`) because it is a targeted subset run, not the full coverage suite.

## [4.1.16] - 2026-02-16

### Changed
- Executed an additional cross-repo style cleanup pass on non-critical lint rules across demos, SDK, quad persona modules, deployment validator, archive scripts, and selected tests.
- Reduced global lint backlog from `553` to `359` by auto-fixing safe rule classes (unused imports/variables, selected simplifications, and redundant bindings).

### Testing
- Debug/error sweep completed for this cleanup phase:
  - `.venv\Scripts\python.exe -m py_compile` across all changed Python files (`51` files, pass)
  - `.venv\Scripts\python.exe -m ruff check . --select E9,F63,F7,F821` (pass)
  - `.venv\Scripts\python.exe -m pytest -q -o addopts='' tests/knowledge_algorithms/test_ka_logic.py sdk/UKG_Python_SDK/tests/test_truth_engine.py sdk/UKG_Python_SDK/tests/test_workflow.py` (`14 passed`)
  - `npm --prefix frontend run lint` (pass)
  - `npm --prefix frontend run typecheck` (pass)
- Remaining non-critical lint debt after this phase:
  - `E402`: 201
  - `E701`: 85
  - `F841`: 20
  - `E712`: 16
  - `E722`: 14
  - `E741`: 9
  - `E721`: 6
  - `F401`: 3
  - `E711`: 2
  - `F811`: 2
  - `F403`: 1

## [4.1.15] - 2026-02-16

### Changed
- Fixed residual global critical lint blocker in SDK truth link stub by restoring missing typing import (`sdk/UKG_Python_SDK/ukg_sdk/truth_engine/truthlink.py`).

### Testing
- `.venv\Scripts\python.exe -m py_compile sdk/UKG_Python_SDK/ukg_sdk/truth_engine/truthlink.py` (pass)
- `.venv\Scripts\python.exe -m ruff check . --select E9,F63,F7,F821` (pass)

## [4.1.14] - 2026-02-16

### Changed
- Lint phase cleanup for backend runtime/services/security modules (215 changed files under `backend/`) with safe removal of unused imports/variables and duplicate dead definitions.
- Backend lint safety subset is now clean for `F401`, `F541`, `F811`, and `F841`.
- Backend critical lint subset is now clean for `E9`, `F63`, `F7`, and `F821`.

### Testing
- Debug/error sweep completed for the backend phase:
  - `.venv\Scripts\python.exe -m ruff check backend --select F401,F541,F841,F811` (pass)
  - `.venv\Scripts\python.exe -m ruff check backend --select E9,F63,F7,F821` (pass)
  - `.venv\Scripts\python.exe -m py_compile` across all modified `backend/` files (pass)
  - `.venv\Scripts\python.exe -m pytest -q -o addopts='' tests/test_health_endpoint.py tests/integration_routes/test_app_route_wiring.py tests/security/test_request_limits.py tests/unit/test_llm_gateway_internal_units.py tests/unit/test_secret_resolver_controls.py tests/unit/test_export_authenticity_controls.py` (`25 passed`)
  - `npm --prefix frontend run lint` (pass)
  - `npm --prefix frontend run typecheck` (pass)
- Known non-blocking remaining style debt in `backend/` after this phase:
  - `E402`: 103
  - `E701`: 43
  - `E722`: 6
  - `E712`: 4
  - `E711`: 1
  - `E741`: 1

## [4.1.13] - 2026-02-16

### Changed
- Lint phase cleanup for simulation runtime modules (29 files under `simulation/`) with safe dead-binding and unused import cleanup.
- Simulation lint safety subset is now clean for `F401`, `F541`, `F811`, and `F841`.

### Testing
- Debug/error sweep completed for the simulation phase:
  - `.venv\Scripts\python.exe -m ruff check simulation --select F401,F541,F841,F811` (pass)
  - `.venv\Scripts\python.exe -m ruff check simulation --select E9,F63,F7,F821` (pass)
  - `.venv\Scripts\python.exe -m py_compile` across all modified `simulation/` files (pass)
  - `.venv\Scripts\python.exe -m pytest -q -o addopts='' tests/simulation/test_simulation_layers.py tests/simulation/test_e2e_simulation_pipeline.py tests/end_to_end/test_e2e_scenarios.py` (`51 passed`)
  - `npm --prefix frontend run lint` (pass)
  - `npm --prefix frontend run typecheck` (pass)
- Known non-blocking remaining style debt in `simulation/` after this phase:
  - `E701`: 13
  - `E402`: 4
  - `E722`: 3
  - `E741`: 1

## [4.1.12] - 2026-02-16

### Changed
- Lint phase cleanup for runtime orchestration and core intelligence modules (`app.py` + 56 files under `core/`) focused on safe, behavior-preserving reductions of unused imports/variables and duplicate dead definitions.
- Core lint safety subset is now clean for `F401`, `F541`, `F811`, and `F841`.
- Fixed undefined logger usage fallback path in QPE execution handling (`core/simulation/query_persona_engine.py`).

### Testing
- Debug/error sweep completed for the app/core phase:
  - `.venv\Scripts\python.exe -m ruff check app.py --select F401,F541,F841,F811` (pass)
  - `.venv\Scripts\python.exe -m ruff check core --select F401,F541,F841,F811` (pass)
  - `.venv\Scripts\python.exe -m ruff check app.py core --select E9,F63,F7,F821` (pass)
  - `.venv\Scripts\python.exe -m py_compile` across all modified `app.py` + `core/` files (pass)
  - `.venv\Scripts\python.exe -m pytest -q -o addopts='' tests/test_health_endpoint.py tests/integration_routes/test_app_route_wiring.py tests/unit/test_core_integration.py tests/simulation/test_simulation_layers.py` (`36 passed`)
  - `npm --prefix frontend run lint` (pass)
  - `npm --prefix frontend run typecheck` (pass)
- Known non-blocking remaining style debt in `app.py` + `core/` after this phase:
  - `E402`: 29
  - `E701`: 8
  - `E741`: 5
  - `E722`: 4
  - `E711`: 1

## [4.1.11] - 2026-02-16

### Changed
- Lint phase cleanup for automated test suites (74 files under `tests/`) focused on safe correctness-preserving fixes:
  - removed unused imports/variables and duplicate unused captures
  - normalized dead temporary bindings in fixtures and mocks
  - restored explicit simulation-engine factory import in `tests/end_to_end/test_full_simulation.py` to eliminate undefined-name lint debt
- Test lint safety subset is now clean for `F401`, `F541`, `F811`, and `F841`.

### Testing
- Debug/error sweep completed for the tests phase:
  - `.venv\Scripts\python.exe -m ruff check tests --select F401,F541,F841,F811` (pass)
  - `.venv\Scripts\python.exe -m ruff check tests --select E9,F63,F7,F821` (pass)
  - `.venv\Scripts\python.exe -m py_compile` across all modified `tests/` files (pass)
  - `.venv\Scripts\python.exe -m pytest -q -o addopts='' tests/unit/test_unified_middleware.py tests/unit/test_middleware_units.py tests/integration/test_api_endpoints.py tests/security/test_audit_logger_comprehensive.py` (`96 passed`)
  - `npm --prefix frontend run lint` (pass)
  - `npm --prefix frontend run typecheck` (pass)
- Known non-blocking remaining style debt in `tests/` after this phase:
  - `E402`: 15
  - `E712`: 10
  - `E721`: 6
  - `E401`: 1

## [4.1.10] - 2026-02-16

### Changed
- Lint phase cleanup for script utilities (29 files under `scripts/`) to remove unused imports/variables and duplicate helper definitions while preserving behavior.
- Hardened script compatibility and startup readability updates in enterprise runners and verification scripts:
  - `scripts/run_enterprise_services.py`
  - `scripts/run_enterprise_ukg.py`
  - `scripts/verify_services.py`
- Script lint safety subset is now clean for `F401`, `F541`, `F811`, and `F841`.

### Testing
- Debug/error sweep completed for the scripts phase:
  - `.venv\Scripts\python.exe -m ruff check scripts --exclude scripts/archive --select F401,F541,F841,F811` (pass)
  - `.venv\Scripts\python.exe -m ruff check scripts --exclude scripts/archive --select E9,F63,F7,F821` (pass)
  - `.venv\Scripts\python.exe -m py_compile` across all modified `scripts/` files (pass)
  - `.venv\Scripts\python.exe -m pytest tests/test_health_endpoint.py -q -o addopts=''` (`5 passed`)
  - `npm --prefix frontend run lint` (pass)
  - `npm --prefix frontend run typecheck` (pass)
- Known non-blocking remaining style debt in `scripts/` after this phase:
  - `E402`: 16
  - `E701`: 9

## [4.1.9] - 2026-02-16

### Added
- Completed Section 11 developer governance subsystem controls:
  - Repository-managed pre-commit hook flow (`.githooks/pre-commit`, `.githooks/README.md`, `scripts/dev/run_precommit_checks.py`).
  - Environment parity and lockfile governance verification scripts (`scripts/verify_environment_parity.py`, `scripts/verify_lockfiles.py`).
  - Governance CI gate (`governance` job) enforcing parity/lockfile checks and pre-commit lint/typecheck policy (`.github/workflows/ci.yml`).
  - ADR baseline structure (`docs/adr/README.md`, `docs/adr/ADR-0001-engineering-governance-baseline.md`).
  - Release checklist governance workflow (`.github/workflows/release-checklist.yml`) and PR template (`.github/pull_request_template.md`).
  - Branch/code-owner policy artifacts (`docs/BRANCH_PROTECTION_POLICY.md`, `.github/CODEOWNERS`).

### Changed
- TypeScript governance profile now enforces additional strictness in typecheck gates (`frontend/tsconfig.typecheck.json`) and corresponding override conformance fix (`frontend/components/ui/api-error-boundary.tsx`).
- Documentation versioning and release governance docs added and linked:
  - `docs/DOCUMENTATION_VERSIONING.md`
  - `docs/DOCS_VERSION.json`
  - `docs/RELEASE_CHECKLIST.md`
  - `docs/DOCUMENTATION_COVERAGE_MATRIX.md`
- Updated active docs and subsystem report to reflect sections 9-11 full completion:
  - `README.md`
  - `docs/README.md`
  - `docs/TESTING.md`
  - `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
  - `CONTRIBUTING.md`
  - `docs/CONTRIBUTING.md`

### Testing
- Section 11 debug/error sweep completed:
  - `python -m py_compile scripts/verify_environment_parity.py scripts/verify_lockfiles.py scripts/dev/run_precommit_checks.py`
  - `python scripts/verify_environment_parity.py --json-report reports/environment_parity_report_local_section11.json` (pass)
  - `python scripts/verify_environment_parity.py --strict --json-report reports/environment_parity_report_local_section11_strict.json` (expected local mismatch on Python/Node vs CI pins)
  - `python scripts/verify_lockfiles.py --json-report reports/lockfile_governance_report_local_section11.json` (pass)
  - `python scripts/dev/run_precommit_checks.py --skip-python-lint` (pass)
  - `powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Pester -Script tests/windows/installer_tests.Tests.ps1"` (`9 passed`)
  - `python scripts/verify_docs_references.py` (pass)

## [4.1.8] - 2026-02-16

### Added
- Completed Section 10 Windows desktop subsystem controls:
  - Controlled auto-update policy/runtime gating with secure IPC accessors (`frontend/electron/main.ts`, `frontend/electron/preload.ts`, `frontend/types/electron.d.ts`).
  - NSIS governance validation script with CI integration (`scripts/windows/verify_nsis_governance.ps1`, `.github/workflows/ci.yml`).
  - Silent installer wrapper for enterprise automation (`scripts/windows/install_silent.ps1`).
  - Startup port conflict auto-resolution controls (`scripts/windows/start_local_stack.ps1`).
- Expanded Windows installer governance tests (`tests/windows/installer_tests.Tests.ps1`).

### Changed
- Desktop secret persistence now uses OS-protected encryption (`safeStorage`) when available, with migration from legacy plaintext storage (`frontend/electron/main.ts`).
- Desktop runtime log persistence now writes to user data with best-effort restricted permissions (`frontend/electron/main.ts`).
- Installer script applies restricted ACL hardening to local logs/audit/vault paths and supports non-admin dry-run diagnostics (`scripts/windows/install.ps1`).
- Uninstaller now has explicit retention controls (`-KeepData`, `-DeleteData`, `-Silent`) with safe defaults for non-interactive runs (`scripts/windows/uninstall.ps1`).
- Windows/local runbooks and subsystem report updated for Section 10 status:
  - `README.md`
  - `docs/README.md`
  - `docs/WINDOWS_11_LOCAL_RUNBOOK.md`

### Testing
- Section 10 debug/error sweep completed:
  - `npm --prefix frontend run electron:build`
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run typecheck`
  - `python -m pytest -q --no-cov tests/windows/test_windows_platform.py` (`4 passed`)
  - `powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Pester -Script tests/windows/installer_tests.Tests.ps1"` (`9 passed`)
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path` (pass)
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path -Mode portable -LaunchTimeoutSeconds 10` (pass)
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/install.ps1 -DryRun -Silent` (pass)
  - `python scripts/verify_docs_references.py` (pass)

## [4.1.7] - 2026-02-16

### Added
- Completed Section 9 testing subsystem enforcement controls:
  - Local-mode parity regression suite (`tests/parity/test_local_mode_parity.py`).
  - Windows packaging smoke automation with portable launch checks and optional installer-mode validation (`scripts/windows/run_packaging_smoke.ps1`).
  - Frontend strict typecheck gate via dedicated production typecheck config (`frontend/tsconfig.typecheck.json`, `frontend/package.json`).
  - Section 9-11 control matrix completed and folded into active testing and operations docs.

### Changed
- CI enforcement pipeline now includes:
  - Explicit API contract, local-mode parity, and security regression sweeps.
  - Frontend typecheck and route E2E smoke gates.
  - Windows packaging smoke job and artifact report upload.
  - File: `.github/workflows/ci.yml`.
- API contract test module is now always enforceable without optional tooling; Schemathesis fuzzing remains opt-in (`RUN_SCHEMATHESIS=1`) (`tests/contract/test_api_contract.py`).
- Updated testing/docs entrypoints to reflect new required gates:
  - `README.md`
  - `docs/README.md`
  - `docs/TESTING.md`
  - `run_test_suite.py`

### Testing
- Debug/error sweep completed:
  - `python -m py_compile run_test_suite.py tests/contract/test_api_contract.py tests/parity/test_local_mode_parity.py`
  - `python -m pytest -q --no-cov tests/contract/test_api_contract.py tests/parity/test_local_mode_parity.py tests/security/test_security_headers.py tests/security/test_request_limits.py` (`18 passed, 1 skipped`)
  - `npm --prefix frontend run lint`
  - `npm --prefix frontend run typecheck`
  - `npm --prefix frontend run test -- tests/unit/lib/runtime/policy.test.ts` (`5 passed`)
  - `npm --prefix frontend run test:e2e -- tests/e2e/route-sidebar-smoke.spec.ts` (`5 passed`)
  - `npm --prefix frontend run test:e2e:visual` (`21 passed`)
  - `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process --json-report reports/runtime_precheck_report_local_section9.json` (fails on existing ACTION-level local setup finding, expected in strict mode)
  - `python scripts/runtime_precheck.py --skip-ports --allow-env-from-process --json-report reports/runtime_precheck_report_local_section9_non_strict.json` (pass)
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/run_packaging_smoke.ps1 -Mode portable -LaunchTimeoutSeconds 10` (pass)
  - `python scripts/verify_docs_references.py` (pass)

## [4.1.6] - 2026-02-16

### Added
- Implemented post-baseline hardening controls for Sections 5-8:
  - Postgres tenant RLS bootstrap + request-scoped tenant DB context (`backend/security/tenant_rls.py`, `app.py`).
  - Vault-aware runtime secret resolver with production secure-source enforcement (`backend/security/secret_resolver.py`, `app.py`, `config.py`, `backend/config.py`).
  - Export authenticity controls: signed manifests + optional encrypted trace export envelopes (`backend/security/export_integrity.py`, `backend/tracing/api.py`).
  - Immutable audit replica hash-chain append and verification controls (`backend/security/audit_logger.py`).
  - AI/connector latency SLO baseline and violation gauges (`backend/observability/latency_slo.py`, `backend/mcp_server/connector_metrics.py`, `app.py`).
  - Code-signing governance drill workflow + certificate health/revocation checks (`.github/workflows/code-signing-governance.yml`, `scripts/windows/verify_signing_certificate_health.ps1`).
- Added focused regression coverage:
  - `tests/unit/test_tenant_rls_controls.py`
  - `tests/unit/test_secret_resolver_controls.py`
  - `tests/unit/test_export_authenticity_controls.py`
  - `tests/security/test_audit_logger_immutable_replica.py`
  - `tests/unit/test_latency_slo_alerts.py`

### Changed
- Release signing workflow now validates certificate health/revocation before signing and verifies signature revocation during artifact checks (`.github/workflows/release-installer-signing.yml`, `scripts/windows/sign_release_installers.ps1`, `scripts/windows/verify_installer_signature.ps1`).
- Updated active docs and subsystem review to reflect post-baseline control completion:
  - `README.md`
  - `docs/README.md`
  - `docs/PRODUCT_OVERVIEW.md`
  - `docs/PRODUCTION_READINESS.md`
  - `docs/OPERATIONAL_RUNBOOKS.md`

### Testing
- Debug/error sweep completed:
  - `python -m pytest -q --no-cov tests/unit/test_tenant_rls_controls.py tests/unit/test_secret_resolver_controls.py tests/unit/test_export_authenticity_controls.py tests/unit/test_latency_slo_alerts.py tests/security/test_audit_logger_immutable_replica.py`
  - `python -m pytest -q --no-cov tests/unit/test_phase3_integrity_crash_controls.py tests/unit/test_phase2_oauth_contract_metrics.py tests/unit/test_phase1_scope_ssrf_controls.py tests/unit/test_mcp_tracing_repo_rest_coverage.py tests/unit/test_llm_gateway_internal_units.py tests/test_health_endpoint.py tests/test_unified_services.py`
  - `python scripts/runtime_precheck.py --skip-ports --allow-env-from-process`
  - `python scripts/verify_docs_references.py`

## [4.1.5] - 2026-02-16

### Added
- Completed final Sections 5-8 partial controls:
  - Snapshot + trace HMAC integrity verification (`core/system/frost_service.py`, `simulation/trace_system.py`, `backend/security/integrity.py`).
  - Crash reporting fallback IDs and telemetry (`backend/observability/crash_reporting.py`, `app.py`).
  - Windows installer code-signing workflow and signature verification tooling (`.github/workflows/release-installer-signing.yml`, `scripts/windows/sign_release_installers.ps1`, `scripts/windows/verify_installer_signature.ps1`).
- Added Phase 3 regression tests:
  - `tests/unit/test_phase3_integrity_crash_controls.py`

### Changed
- Updated deploy/security workflows with crash-reporting probe verification checks.
- Updated installer build orchestrator to enable signed mode when signing material is available (`frontend/build_installer.ps1`).
- Updated sections 5-8 subsystem report and active docs to reflect full control implementation (`33/33`).

### Testing
- Debug/error sweep completed:
  - `python -m pytest -q --no-cov tests/unit/test_phase3_integrity_crash_controls.py tests/test_unified_services.py tests/test_health_endpoint.py tests/unit/test_phase2_oauth_contract_metrics.py`
  - `python -m pytest -q --no-cov tests/unit/test_phase1_scope_ssrf_controls.py tests/unit/test_mcp_tracing_repo_rest_coverage.py tests/unit/test_llm_gateway_internal_units.py`
  - `python scripts/verify_docs_references.py`

## [4.1.4] - 2026-02-16

### Added
- Completed Sections 5-8 Phase 2 hardening controls:
  - Shared connector OAuth lifecycle manager with refresh + persisted token updates.
  - Runtime MCP connector contract validation for input/output schemas.
  - AI latency percentile telemetry (`p50`/`p95`/`p99`) exported via `/metrics`.
  - Support-bundle diagnostics generator (`scripts/generate_support_bundle.py`).
  - Deterministic startup precheck strict mode + CI/deploy release gates.
- Added focused Phase 2 regression coverage:
  - `tests/unit/test_phase2_oauth_contract_metrics.py`

### Changed
- Updated Jira/Salesforce MCP connectors to prefer managed OAuth tokens with controlled fallback.
- Updated docs and subsystem report to reflect Phase 2 completion:
  - `README.md`
  - `docs/README.md`
  - `docs/PRODUCT_OVERVIEW.md`
  - `docs/PRODUCTION_READINESS.md`
  - `docs/OPERATIONAL_RUNBOOKS.md`

### Testing
- Targeted phase hardening/debug sweep completed:
  - `python -m pytest -q --no-cov tests/unit/test_phase2_oauth_contract_metrics.py tests/unit/test_phase1_scope_ssrf_controls.py tests/unit/test_mcp_tracing_repo_rest_coverage.py tests/test_health_endpoint.py tests/unit/test_llm_gateway_internal_units.py`
  - `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process --json-report reports/runtime_precheck_report_local_phase2.json`
  - `python scripts/generate_support_bundle.py --skip-http --output-dir reports/support_bundles --max-files-per-group 3`

## [4.1.3] - 2026-02-16

### Added
- Completed Sections 5-8 Phase 1 hardening controls:
  - MCP connector scope enforcement with user/tenant execution context.
  - SSRF outbound URL guardrails for API gateway forwarding and service health probes.
  - Connector latency/error telemetry surfaced to metrics and analytics reporting.
  - SQLite/PostgreSQL schema parity validation script and CI/deploy gates.
  - Installer checksum generation and deploy-time installer integrity verification.

### Changed
- Updated active documentation set (`README.md`, `docs/README.md`, `docs/PRODUCT_OVERVIEW.md`, `docs/PRODUCTION_READINESS.md`, `docs/OPERATIONAL_RUNBOOKS.md`) to reflect the current implementation state as of 2026-02-16.

### Testing
- Targeted hardening validation completed:
  - `python -m pytest -q --no-cov tests/unit/test_phase1_scope_ssrf_controls.py tests/unit/test_mcp_tracing_repo_rest_coverage.py`
  - `python scripts/validate_schema_parity.py --report reports/schema_parity_report_local.json`
  - `python scripts/verify_installer_integrity.py --require-artifacts --report reports/installer_integrity_report_local.json`

## [4.1.2] - 2026-02-07

### Fixed
- Corrected timezone handling in token revocation by using `datetime.fromtimestamp(..., UTC)` in `backend/security/token_manager.py`, preventing naive/aware datetime subtraction errors during logout and blacklist flows.

### Added
- High-coverage test suites for previously under-tested modules:
  - Security: token manager, vulnerability scanner, compliance manager, sanitizer, context-aware drift detection.
  - APIs: methods API, security API, security scan API, regulatory API, pillar API.
  - Infrastructure/logic: MCP registry/router/tools, trace logger, node repository, REST API, TruthGate budget and compliance modules.

### Testing
- Full coverage-gated run now passes:
  - Command: `pytest tests`
  - Result: `1461 passed, 21 skipped`
  - Coverage: `70.20%` (required: `70%`).

## [4.1.1] - 2026-02-07

### Fixed
- Stabilized full-suite authentication behavior by removing global `sys.modules["models"]` pollution in `tests/unit/test_llm_gateway_internal_units.py`.
- Hardened audit logging transaction handling to rollback failed DB writes and prevent session poisoning (`PendingRollbackError`) during malformed-input fuzz scenarios.
- Updated gateway integration tests to match enforced API contract requiring `model` for `/api/v1/gateway/chat` and `/api/v1/gateway/chat/stream`.
- Improved KA resilience under full-suite execution conditions:
  - `KA-005` now handles event-loop lifecycle safely in sync contexts.
  - `KA-114` tolerates contract-test runs outside Flask app context.
  - Config/default hardening applied across infrastructure KAs (`KA-62`, `KA-71`, `KA-74`, `KA-86`).

### Testing
- Functional suite now passes end-to-end with:
  - `pytest tests --no-cov`
  - Result: `1419 passed, 21 skipped`.
- Default coverage-gated run still fails coverage threshold:
  - `pytest tests`
  - Total coverage: `64.20%` (required: `70%`).

## [4.1.0] - 2026-02-02

### Added
- **Phase 6: Enterprise Hardening complete**.
- **Public API Fuzz Testing**: 100% pass rate across 42 endpoints with robust payload validation.
- **Unified API Response Middleware**: Standardized async/sync handlers with PII redaction and production error sanitization.
- **Database Lifecycle Hardening**: Robust graceful shutdown for PostgreSQL, Redis, and Neo4j in desktop mode.
- **Security Audit Graduation**: Full documentation sweep and version alignment for production graduation.

## [4.0.0] - 2026-02-02

### Added

- Phase 4: Production Resilience complete.
- Hardened `Validator` and `Pagination` utility unit tests.
- Full unit test coverage for `mcp`, `simulation`, and `compliance` API clients.
- Simulated E2E integration test covering the 12-step Orchestrator lifecycle.

## [3.0.0] - 2026-02-02
### Added
- Phase 3: Integration & Security Hardening complete.
- Comprehensive integration tests for LLM Gateway (failover, circuit breaking).
- Reliability tests for `UkgDatabaseManager` (tenant isolation, caching).
- Full-stack compliance verification for Nurnburg/SAM logic via `RefinementOrchestrator`.
- Standardized backend test configuration via `conftest.py`.

## [2.5.0] - 2026-02-02

### Added - Phase 2 Coverage & Core Stability

- **Frontend Logic Coverage**: Reached targeted coverage for `ChatInterface.tsx` and `socket.ts` through comprehensive unit tests.
- **Backend Security Hardening**: Implemented advanced security middleware tests for path traversal and SQL injection patterns.
- **Backend Core Integration**: Added integration tests for `KAMasterController` and `TruthEngine` coordination.
- **Stability Fixes**: Resolved critical race conditions in the Chat Interface during session hydration.
- **Phase 2 Milestone**: Successfully met coverage targets for core coordination layers (~68% FE, ~50% BE).

## [2.4.0] - 2026-01-16

### Added - Multi-Mode Reasoning Engine (Cloud & Desktop)
- **Hybrid Deployment Architecture**: Transitioned to a multi-mode architecture supporting both **Enterprise Cloud** and **Local-First Windows 11 Desktop** deployments.
- **Windows 11 Desktop Support**: Native Windows 11 desktop application with deep OS integration.
- **Native Windows Services**: Implemented backend and frontend as native Windows services via WinSW.
- **Zero-Config Identity**: Added automated user identification and registration via Windows Security Identifier (SID).
- **Secure Secret Management**: Integrated Windows DPAPI for encrypted storage of LLM API keys.
- **AI Transparency & Labeling**: Implemented "AI-Generated Content" labels and a comprehensive AI Limitations disclosure page.
- **Cloud Disclosure**: Added a first-run cloud disclosure banner and a detailed "About Cloud Services" transparency page.
- **User Data Rights**: Implemented self-service Data Export (JSON) and Profile Deletion for privacy compliance (GDPR/CCPA).
- **KA-61 Adversarial Shield**: Enhanced security with a 5-point adversarial input shield (L1 Gate) to prevent prompt injection and logical traps.
- **Standalone Distribution**: Created a structured `dist_package/` with local launchers and orchestration scripts.

## [2.3.1] - 2026-01-15

### Added - SDK Synchronization & Documentation Consolidation
- **SDK Synchronization**: Updated `tenlayer.py`, `coordinates17.py`, and `frost.py` to match the functional 10-layer model and 17-axis framework.
- **Functional 10-Layer Realization**: Refactored `SimulationEngine` and `LayerController` to implement the reasoning-centric model (Context -> Materialization -> Debate -> Scenarios -> Final Gate).
- **USKD_vN Versioning**: Implemented explicit snapshot versioning in FROST for both the application and SDK.
- **Documentation Versioning**: Applied consistent `v2.3.1 - January 2026` headers to `README.md`, `ARCHITECTURE.md`, `UKG_Python_SDK/README.md`, and system whitepapers.
- **Architectural Audit**: Completed full alignment between conceptual whitepapers and production implementation.

## [2.3.0] - 2026-01-15

### Added - Phase 24: Layer 9 Meta-Reasoning & Recursion Governance
- **MetaReasoningController**: Implemented Layer 9 as the recursion governor with FINALIZE/REFINE gate logic.
- **11-KA Integration (Layer 9)**: Wired 7 L9-specific KAs and 4 canonical KAs (KA-008, KA-010, KA-022, KA-025).
- **Belief Drift Detection**: Automated semantic and numerical drift analysis between original query and final solution.
- **Persona Agreement Auditing**: Systematic audit of persona satisfaction scores (silent dissent detection).
- **Trace Integrity Analysis**: Systematic review of reasoning traces (L1-L8) for consistency.
- **Recursion Routing**: Advanced routing table to target specific layers (L2-L8) based on identified meta-reasoning issues.
- **Iteration Controls**: Hard limits (max 5) and diminishing returns detection to prevent infinite loops.
- **TruthCoreEngine Integration**: Expanded refinement pipeline to 27 steps including meta-reasoning evaluation.
- **Verification Suite**: Added 15 unit tests covering L9 schemas, controller logic, and KA integration.

## [2.2.0] - 2026-01-15

### Added - Phase 11: Enterprise Security Consolidation
- **Multi-Factor Authentication (MFA)**: Native TOTP support with guided setup, backup codes, and session verification.
- **Granular RBAC**: Permission-based access control system (`user:manage_roles`, `security:read`, etc.).
- **Field-Level Encryption**: AES-256 protection for sensitive PII (emails, simulation metadata) using a KEK/DEK pattern.
- **Infrastructure Hardening**: Forced TLS 1.3 redirection, HSTS enforcement, and strict CSP/security headers.
- **Hardened User Model**: Progressive account lockout (5 attempts), password expiry tracking, and complexity enforcement.
- **Enterprise Session Management**: Redis-backed sessions with rotation, concurrency limits, and strict idle timeouts.

### Added - Knowledge Algorithm (KA) Integration Audit
- **L1-L7 KA Wiring**: All simulation layers now invoke specific KAs from the 123-algorithm registry.
- **L1**: KA-004 (Input Validation), KA-005 (Query Classification), KA-036 (Complexity Estimator), KA-113 (Complexity Router).
- **L2**: KA-025 (Dependency Mapping), KA-018 (Source Provenance).
- **L3**: KA-009 (Evidence Validation), KA-010 (Bias Detection), KA-034 (Adversarial Reasoning).
- **L4**: KA-028 (POV Expansion), KA-057 (Persona Emotion Adaptation).
- **L5**: KA-013 (Persona Weighting), KA-026 (Contradiction Detection) added to refinement pipeline.
- **L6**: KA-039 (Anomaly Detection), KA-116 (Entropy Detection) integrated into `QuantValidationService`.
- **L7**: KA-002 (Tree-of-Thought), KA-040 (Hypothesis Generation), KA-021 (Emergence Detection) wired into `AGIPlannerService`.
- **L8**: KA-003, KA-008, KA-014, KA-016, KA-022, KA-023, KA-024, KA-025, KA-026, KA-030, KA-034 wired into `TrustValidationGateway`.
- **TruthCoreEngine**: Expanded refinement steps from 15 to 26.


### Changed
- Standardized all administrative API routes with granular permission checks.
- Upgraded `User.email` and `SimulationSession` fields with automatic encryption properties.

## [2.1.2] - 2025-11-22

- COMPLETED Phase 6: Universal A11y & UX Consolidation.
- REDESIGNED Chat, Auth, and Profile pages with Enterprise Glassmorphism.
- IMPLEMENTED Copy-to-Clipboard and Axis Visualization in Chat.
- ACHIEVED 100% ARIA coverage across all landing and internal pages.

## [2.1.1] - 2025-11-21

- HARDENED frontend with full ARIA accessibility and focus-visible indicators.
- IMPLEMENTED custom Toast notification system and dynamic Breadcrumbs.
- SYNCHRONIZED all compliance backend endpoints for production readiness.

## [2.1.0] - 2025-11-20

- COMPLETED Phase 5: Enterprise UI & Analytics Migration.
- REFACTORED Dashboard into a Fluent 2 Compliance Hub with real-time Recharts trends.
- IMPLEMENTED Horizontal Axis Selector and Collapsible Sidebars in Graph Explorer.
- HARDENED Analytics Backend with real-time DB metrics.
- STANDARDIZED Command Bar across all dashboard views.

## [2.0.0] - 2026-01-15

### Added - Intelligence & Ops (v2.0 Milestone)

- **Multi-Persona Consensus Engine**: Implemented weighted semantic voting (KA-038) and expert arbitration (KA-030) in the Truth Engine.
- **Local ML Model Serving**: Integrated `LocalSLMProvider` for vLLM/Ollama with automatic tier-based routing optimization.
- **UKG K8s Operator**: Introduced a custom Kubernetes operator with CRDs for `KnowledgeAlgorithm` and `TraceRun`, support for custom scaling metrics, and DR orchestration.
- **Federated Knowledge Sharing**: Launched `FederatedSyncEngine` (KA-114/115) for secure, ZKP-verified cross-tenant knowledge exchange.
- **Enterprise Hardening**: Refactored the core Intelligence Layer for high-concurrency, isolated tenant operations.

### Removed

- **Mobile Native Track**: Scoped out of v2.0 to focus on premium Desktop/Enterprise experience.

### Added - Enterprise KA Resilience & Hardening

- **100% KA Hardening**: All 116 Knowledge Algorithms refactored with Pydantic validation schemas.
- **Enterprise Error Framework**: Standardized exception hierarchy (`KAError`, `KAValidationError`, etc.) in `core/knowledge_algorithm/exceptions.py`.
- **Resilience Pass**: Implemented `_fallback_logic` hooks for critical Security, Data, and Infrastructure KAs.
- **Structured Error Reporting**: Enhanced `KAResult` with machine-readable error codes and detailed metadata.
- **Unified Registry**: Consolidated algorithm discovery into `knowledge_algorithms/ka_registry.yaml`.

### Documentation

- Updated all core documentation (README, Architecture, Production Readiness) to reflect 116 KA count and resilience features.
- Expanded error handling guide with backend exception framework details.

## [1.3.0] - 2026-01-08

### Added - Enterprise Traceability Chatbot

- Full traceability chatbot UI with end-to-end visibility
- 10 SQLAlchemy models for trace data (TraceRun, TraceStage, TraceEvidence, etc.)
- 15+ REST API endpoints for trace access (`/api/v1/trace/*`)
- 10 new template pages for trace visualization
- DAG viewer with D3.js for execution pipeline visualization
- Persona workbench with consensus flow and weight distribution
- Evidence panel with claim-to-source mapping
- 17-axis coordinate inspector with visual grid
- KA trace page with layer mapping
- Memory viewer with writeback gating
- Policy/compliance page with control mapping
- Metrics dashboard with latency/token charts
- Export bundle functionality for audit
- RBAC-aware trace filtering

### UI/UX Enhancements

- Enterprise chatbot at `/chat` with full tracing panels
- Run explorer at `/runs` with search and filters
- Run detail at `/runs/:id` with timeline and tabbed panels
- User journey review documentation

### Documentation

- Updated README with new routes and features
- Created FRONTEND_REVIEW.md
- Created USER_JOURNEY_REVIEW.md

## [1.2.0] - 2026-01-06

### Added - Enterprise Readiness

- Flask-Compress for response compression (gzip/brotli)
- Database indexes on frequently queried columns
- GAP_ANALYSIS.md documenting 17 identified gaps
- ENTERPRISE_ROADMAP.md with 5-phase implementation plan
- Consolidated TODO.md as single source of truth

### Changed

- Updated README.md with current project state and structure
- Reorganized project structure (moved demos, scripts, configs)
- Consolidated old task documents into the root TODO.

### Fixed

- Removed duplicate Flask-Migrate from requirements.txt
- Security scan issues addressed

### Security

- Verified PostgreSQL connection pooling (pool_size=20, max_overflow=40)
- Verified Redis configuration for rate limiting
- Bandit security scan passed

### Documentation

- Updated all documentation to reflect current state
- Added documentation links table to README

## [1.1.0] - 2025-12-23

### Added - Security Hardening & Production Readiness

- CSRF protection with Flask-WTF across all forms and endpoints
- Production credential validation (blocks insecure defaults in production)
- MCP endpoint authorization (admin-only for create/delete operations)
- Correlation ID middleware for request tracing (`X-Correlation-ID` header)
- CSRF meta tag in base template for JavaScript form submissions

### Fixed

- Blocking asyncio.run() calls replaced with shared event loop helper
- Export function properly handles missing session_id attribute

### Changed

- Updated ARCHITECTURE.md to reflect actual monolithic Flask architecture
- Updated API.md to document session-based authentication (not JWT)
- Standardized project naming to "Universal Knowledge Graph (UKG) System"

### Removed

- Dead Next.js code in `pages/` directory
- Unused `node_modules_old/` directory

### Security

- Added @admin_required decorator to MCP server management endpoints
- Added production validation to block default credentials
- Added correlation ID tracking for audit trail

## [1.0.0] - 2024-12-19

### Added - Production Release

- Split routes.py (736 lines) into 4 modular blueprint files:
  - `routes/auth_routes.py` - Authentication (login, logout, register)
  - `routes/page_routes.py` - Page rendering (dashboard, knowledge, graph, etc.)
  - `routes/api_routes.py` - API endpoints
  - `routes/admin_routes.py` - Admin routes with @admin_required decorator
- Created `@admin_required` decorator in `backend/decorators.py`
- Created `@role_required` and `@api_key_required` decorators
- Backward-compatible endpoint aliases for seamless template compatibility

### Changed

- Routes now organized in `routes/` package instead of single file
- Admin routes use new `@admin_required` decorator
- Test pass rate improved from 47% to 93% (150/161 tests)
- Fixed test assertion field name mismatches (confidence, unified_memory, external_knowledge)

### Fixed

- Blueprint registration now happens in `app.py` for consistent test behavior
- Test method name mismatches for persona axes and KA master controller

## [0.5.0] - 2024-12-19

### Added - Phase 5: Frontend-Database Integration

- Connected Knowledge Browser to real database data
- Updated `/api/graph` endpoint to return nodes, edges, pillars, sectors, domains
- Added tabbed interface to Knowledge Browser showing 17-axis framework
- Real-time display of pillars (Axis 1), sectors (Axis 2), and domains (Axis 3)
- Stat cards showing counts of knowledge entities

### Changed

- Knowledge Browser now displays actual seeded data instead of placeholders
- Graph API enriched with pillar/sector/domain context for visualization

## [0.4.0] - 2024-12-19

### Added - Phase 4: Database Seeding & API Documentation

- Database seeding script (`seed_data.py`) with 86 reference records
- 17 knowledge pillars (PL-1 through PL-17)
- 15 worldwide sectors with NAICS mappings
- 13 knowledge domains
- 25 knowledge graph nodes representing 17-axis framework
- 16 edges connecting axis nodes
- Swagger UI API documentation at `/api/docs`
- OpenAPI 3.0 specification (`static/swagger.json`)

### Changed

- Updated app.py to use SESSION_SECRET as mandated
- Added flask-swagger-ui dependency

## [0.3.1] - 2024-12-18

### Added - Phase 3B: Admin Features

- Audit Log page (`/admin/audit`) with event filtering and compliance info
- System Settings page (`/admin/settings`) with 6 configuration tabs
- RBAC role field added to User model (admin/analyst/user/viewer)
- User Management page (`/admin/users`) with role assignment

### Changed

- Updated navigation with Admin section
- Enhanced admin dashboard with system metrics

## [0.3.0] - 2024-12-17

### Added - Phase 3: Testing Infrastructure

- 161 tests covering all Phase 2 components
- Integration tests for API endpoints
- Unit tests for simulation engine layers

## [0.2.0] - 2024-12-15

### Added - Phase 2: Core Implementation

- 10-Layer Simulation Stack (all layers implemented)
- Quad Persona Engine (Analyst, Expert, Critic, Synthesizer)
- Knowledge Algorithms (KA-001 to KA-058+)
- Truth Engine v7.3 components (TruthCore, TruthGate, TruthMemory, TruthLink)

## [0.1.1] - 2024-12-10

### Added - Phase 1: Security Hardening

- Security headers middleware
- Request size limits
- Rate limiting
- CSRF protection

### Fixed

- Removed debug mode in production
- Secured secret key configuration

## [0.1.0.1] - 2024-12-08

### Fixed - Phase 0: Emergency Security Fixes

- Removed default credentials (admin/admin123)
- Disabled debug mode in production
- Removed secrets from version control
- Added environment variable validation

## [0.1.0] - 2024-11-21 (Legacy - Initial Release)

### Added

#### Core Features (Initial Architecture)

- 17-axis knowledge framework implementation (expanded from initial 13-axis)
  - Axis 1: Pillar Levels (knowledge pillars)
  - Axis 2: Industry Sectors
  - Axis 3: Honeycomb System
  - Axis 4: Branch System
  - Axis 5: Node System
  - Axis 6: Octopus Node (Regulatory)
  - Axis 7: Spiderweb Node (Compliance)
  - Axes 8-11: Expert Personas
  - Axis 12: Location Context
  - Axis 13: Temporal/Causal Logic
  - Axes 14-17: Extended Enterprise (added later)

#### Knowledge Algorithms

- 56+ knowledge algorithms (KA-01 through KA-56)
- Semantic mapping and coordinate projection
- Honeycomb expansion algorithm
- Regulatory and compliance expert simulation
- Neural reconstruction and tree-of-thought processing

#### Simulation Engines

- Layer 1-3: Memory simulation and propagation
- Layer 5: Integration engine
- Layer 7: AGI simulation system
- Layer 8: Quantum simulation
- Layer 9-10: Recursive processing

#### Frontend

- Next.js 14.0.4 web application
- Interactive chat interface with UKG integration
- D3.js knowledge graph visualization
- 3D honeycomb structure viewer
- Compliance dashboard
- Pillar mapping interface
- Timeline visualization
- Location-based mapping
- Unified cross-axis mapping

#### Backend

- Flask 3.1.1 microservices architecture
- PostgreSQL 16 database integration
- SQLAlchemy ORM with comprehensive models
- RESTful API with Swagger documentation
- Microservices pattern:
  - API Gateway (port 5000)
  - Webhook Server (port 5001)
  - Model Context Service (port 5002)
  - Core UKG Service (port 5003)

#### Security & Authentication

- JWT token-based authentication
- Azure AD (Entra ID) integration
- Flask-Login session management
- API key authentication
- Role-based access control (RBAC)
- Comprehensive security logging

#### Compliance & Audit

- SOC2 compliance reporting
- Audit logging system
- Compliance framework mapping
- Security event tracking
- Regulatory framework support

#### Expert Persona System

- Knowledge Expert simulation
- Sector Expert simulation
- Regulatory Expert simulation
- Compliance Expert simulation
- Quad Persona integration

#### Data & Configuration

- PostgreSQL primary database
- JSON storage fallback
- YAML configuration files
- Environment-based configuration
- Regulatory frameworks data
- Location gazetteer data

#### Developer Tools

- Multiple startup scripts (enterprise, UKG, standalone)
- Database initialization scripts
- Health check utilities
- Demo scripts for all major features
- Development and production configurations

### Changed

- Refactored React hook dependencies for optimization
- Enhanced code structure for improved readability
- Updated navigation components in Sidebar

### Fixed

- Resolved application initialization conflicts
- Fixed React hook dependency issues
- Improved error handling across services

### Infrastructure

- Replit deployment configuration
- Gunicorn production server
- Development server with hot reload
- Multi-service orchestration
- Environment variable management

### Documentation

- Comprehensive gap analysis
- Microsoft Fluent UI style guide
- Environment variable template
- Service architecture documentation

## [0.0.1] - Initial Development

### Added

- Initial project structure
- Basic Flask application setup
- Next.js frontend initialization
- Database models foundation
- Core knowledge graph components

---

## Release Notes

### Version 0.1.0

This is the first official release of DataLogicEngine, featuring a complete implementation of the Universal Knowledge Graph system with 13-axis framework, 56+ knowledge algorithms, and enterprise-grade security features.

**Key Highlights:**

- Complete 13-axis knowledge framework
- Multi-layer simulation engines (10 layers)
- Expert persona simulation system
- Enterprise security with Azure AD integration
- SOC2 compliance features
- Interactive web interface with advanced visualizations

**Known Issues:**

- See [TODO.md](TODO.md) for identified gaps and outstanding items
- Port conflict resolution needed for multi-service deployments
- Database migration strategy in development
- Some API endpoints need enhanced authentication

**Migration Notes:**

- No migrations needed for first release
- Follow installation guide in README.md

**Upgrade Path:**

- N/A for initial release

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute changes and updates to this changelog.

## Links

- [Repository](https://github.com/kherrera6219/DataLogicEngine)
- [Issue Tracker](https://github.com/kherrera6219/DataLogicEngine/issues)
- [Documentation](docs/)

---

[Unreleased]: https://github.com/kherrera6219/DataLogicEngine/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kherrera6219/DataLogicEngine/releases/tag/v0.1.0
[0.0.1]: https://github.com/kherrera6219/DataLogicEngine/releases/tag/v0.0.1
