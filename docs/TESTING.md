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
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `pyproject.toml` (pytest and coverage configuration)
2. `docs/PRODUCTION_READINESS.md`
3. `docs/DEPLOYMENT.md`
4. `README.md`
5. `docs/RELEASE_CHECKLIST.md`
6. `docs/BRANCH_PROTECTION_POLICY.md`

## Current quality baseline (verified 2026-02-08)

1. Backend test suite: `1518 passed, 21 skipped`
2. Coverage gate: `71.47%` (required: `>=70%`)
3. Frontend lint gate: passing

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
  unit/
  integration/
  integration_routes/
  end_to_end/
  security/
  simulation/
  windows/
frontend/
  tests/
    unit/
    e2e/
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

