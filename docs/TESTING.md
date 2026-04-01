# Testing Standards and Execution Guide

## Purpose

Define enterprise testing standards, required quality gates, and execution workflows for DataLogicEngine.

## Audience

1. Backend engineers
2. Frontend engineers
3. QA engineers
4. Release managers

## Document control

1. Owner: Quality Engineering
2. Last updated: 2026-03-31
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `pyproject.toml` (pytest and coverage configuration)
2. `docs/PRODUCTION_READINESS.md`
3. `docs/DEPLOYMENT.md`
4. `README.md`
5. `docs/RELEASE_CHECKLIST.md`
6. `docs/BRANCH_PROTECTION_POLICY.md`

## Current quality baseline (verified 2026-02-17)

1. Full backend suite baseline remains `1518 passed, 21 skipped` (last full-cov baseline run: 2026-02-08).
2. Coverage gate baseline remains `71.47%` (required: `>=70%`) from the last full-cov baseline run.
3. Python lint gate is fully clean: `.venv\Scripts\python.exe -m ruff check .` passes (2026-02-17).
4. Latest targeted regression sweep: `271 passed` with `--no-cov` (2026-02-17).

## 2026-02-17 lint and regression stabilization update

1. Completed lint phases 9-11 and reduced remaining style debt to zero.
2. Validation commands executed:
   - `.venv\Scripts\python.exe -m ruff check .`
   - `.venv\Scripts\python.exe -m py_compile` across changed Python files
   - `.venv\Scripts\python.exe -m pytest -q --no-cov tests/knowledge_algorithms/test_ka_bulk.py tests/truth_engine/test_layer10_emergence.py tests/truth_engine/test_layer9_meta_reasoning.py tests/truth_engine/test_truth_infrastructure.py sdk/UKG_Python_SDK/tests/test_truth_engine.py tests/integration_routes/test_app_route_wiring.py`
3. Phase reports:
   - `docs/archive/assessments/2026-02/LINT_STYLE_SWEEP_PHASE9_2026-02-17.md`
   - `docs/archive/assessments/2026-02/LINT_STYLE_SWEEP_PHASE10_2026-02-17.md`
   - `docs/archive/assessments/2026-02/LINT_STYLE_SWEEP_PHASE11_2026-02-17.md`

## 2026-03-31 Phase 4 contract hardening update

1. Added canonical `/api/v1/*` route contract tests in `tests/contract/test_canonical_v1_route_contracts.py`.
2. The contract suite now asserts JSON `401` behavior for unauthenticated canonical endpoints instead of tolerating redirect semantics.
3. The same suite now locks deterministic malformed-request behavior:
   - `/api/v1/query` -> `422 VALIDATION_ERROR`
   - `/api/v1/simulation/run` -> `422 VALIDATION_ERROR`
   - `/api/v1/simulations` with no parameters -> `400 Missing parameters`
4. Canonical simulation happy-path behavior is now covered with strict `201/200/200/200` expectations for create, list, run, and fetch operations.
5. `tests/integration/test_api_endpoints.py` now enforces exact status semantics for canonical `/api/v1/auth/*` flows and the supported legacy `/api/simulations` compatibility path instead of accepting redirect-style or server-error buckets.
6. Session-only canonical auth routes now have explicit regression coverage for JSON `401` failures on `/api/v1/auth/logout`, `/api/v1/auth/mfa/setup`, `/api/v1/auth/mfa/confirm`, and `/api/v1/auth/step-up`.

## Section 9 subsystem coverage (updated 2026-02-16)

1. Unit test framework: `pytest` (backend) and `vitest` (frontend) enforced in CI.
2. Integration test framework: `tests/integration` and `tests/integration_routes` enforced in CI.
3. API contract tests: `tests/contract/test_api_contract.py` now enforces static OpenAPI contract assertions and runtime contract smoke checks.
4. End-to-end automation: Playwright route smoke and visual regression suites are both CI-enforced.
5. Visual snapshot testing: baseline snapshots in `frontend/tests/e2e/theme-visual-smoke.spec.ts-snapshots`.
6. Security regression tests: targeted CI security regression sweep (`security headers` + `request limits`) plus broader security suites.
7. Local mode parity tests: dedicated parity suite at `tests/parity/test_local_mode_parity.py`.
8. Packaging smoke tests (clean VM): Windows CI job runs `scripts/windows/run_packaging_smoke.ps1` and NSIS policy governance checks via `scripts/windows/verify_nsis_governance.ps1`.
9. CI enforcement pipeline: lint, typecheck, unit/integration/contract/parity/security tests, build, accessibility, E2E, visual regression, and dependency audit gates.

## Test taxonomy

1. Unit tests: fast isolated tests for modules and classes.
2. Integration tests: API routes, service interactions, and policy behaviors.
3. End-to-end tests: cross-service workflow behavior.
4. Security tests: auth, session, RBAC, sanitization, and attack-surface controls.
5. Platform tests: Windows-specific behavior and desktop-mode checks.

## Directory model

```text
tests/
  unit/                   # Isolated module tests
  integration/            # Service interaction and API route tests
  integration_routes/     # App-level route wiring tests
  end_to_end/             # Cross-service workflow tests
  security/               # Auth, RBAC, sanitization, attack-surface tests
  simulation/             # Simulation engine layer tests
  knowledge_algorithms/   # KA execution and contract tests
  truth_engine/           # Truth Engine layer tests
  compliance/             # GDPR, SOC 2, regulatory tests
  parity/                 # Local-mode parity tests
  contract/               # OpenAPI contract assertion tests
  performance/            # Load and latency tests (Locust)
  axes/                   # 17-axis system tests
  quad_persona/           # Quad-persona engine tests
  windows/                # Windows-specific and desktop-mode tests
  utils/                  # Test utilities and helpers
frontend/
  tests/
    unit/                 # React component unit tests (Vitest)
    e2e/                  # Playwright end-to-end and visual regression tests
```

## Prerequisites

1. Python virtual environment created at `.venv`
2. Dependencies installed from `requirements.txt`
3. Frontend dependencies installed (`frontend/package-lock.json`)
4. Local env variables configured for test mode where needed

## Standard execution commands

### Bootstrap smoke check

```powershell
.\.venv\Scripts\python .\scripts\test_smoke.py
```

### Backend

```powershell
.\.venv\Scripts\python -m pytest tests --maxfail=20
```

### Backend (targeted)

```powershell
.\.venv\Scripts\python -m pytest tests\unit\test_simulation_engine_unit.py -q --no-cov
```

### Backend contract + parity + security sweeps

```powershell
.\.venv\Scripts\python -m pytest -q --no-cov tests\contract\test_api_contract.py
.\.venv\Scripts\python -m pytest -q --no-cov tests\parity\test_local_mode_parity.py
.\.venv\Scripts\python -m pytest -q --no-cov tests\security\test_security_headers.py tests\security\test_request_limits.py
```

### Frontend lint and tests

```powershell
cd frontend
npm run lint
npm run typecheck
npm test
```

### Frontend E2E + visual regression

```powershell
cd frontend
npm run test:e2e -- tests/e2e/route-sidebar-smoke.spec.ts
npm run test:e2e:visual
```

### Windows packaging smoke (installer clean-runner check)

```powershell
npm --prefix frontend run electron:dist
powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1
```

### Documentation reference validation

```powershell
.\.venv\Scripts\python .\scripts\verify_docs_references.py
```

### Governance and parity checks

```powershell
python .\scripts\verify_environment_parity.py
python .\scripts\verify_lockfiles.py
python .\scripts\dev\run_precommit_checks.py
```

## Required release gates

1. All required CI jobs pass on protected branch.
2. Backend coverage remains at or above configured threshold.
3. No medium/high security regression in enforced security scans.
4. No failing migration or startup checks in deployment workflows.
5. Frontend typecheck must pass.
6. Contract/parity/security regression sweeps must pass.
7. Windows packaging smoke job must pass.

## Test authoring standards

1. Name tests by behavior, not implementation detail.
2. Use deterministic fixtures and isolate external dependencies with mocks.
3. Keep unit tests side-effect free (no network, no external services).
4. Add regression tests for every production bug/security fix.
5. Use explicit assertions for security controls and error semantics.

## Failure triage protocol

1. Reproduce locally with targeted test command.
2. Identify whether failure is test defect, product defect, or environment defect.
3. Fix with minimal blast radius and add/adjust regression coverage.
4. Re-run targeted tests, then relevant suite, then full suite for high-risk changes.
5. Document notable failures/remediations in release notes or incident reports when needed.

## CI parity guidelines

1. Use same Python and Node major versions as CI (`3.11`, `20`).
2. Keep local commands aligned with workflow commands in:
   - `.github/workflows/ci.yml`
   - `.github/workflows/deploy.yml`
3. Avoid adding undocumented local-only test flags for critical flows.

