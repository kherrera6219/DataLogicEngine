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
2. Last updated: 2026-02-08
3. Status: Active
4. Review cadence: Every 30 days

## Related documents

1. `pyproject.toml` (pytest and coverage configuration)
2. `docs/PRODUCTION_READINESS.md`
3. `docs/DEPLOYMENT.md`
4. `README.md`

## Current quality baseline (verified 2026-02-08)

1. Backend test suite: `1518 passed, 21 skipped`
2. Coverage gate: `71.47%` (required: `>=70%`)
3. Frontend lint gate: passing

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

### Backend

```powershell
.\.venv\Scripts\python -m pytest tests --maxfail=20
```

### Backend (targeted)

```powershell
.\.venv\Scripts\python -m pytest tests\unit\test_simulation_engine_unit.py -q --no-cov
```

### Frontend lint and tests

```powershell
cd frontend
npm run lint
npm test
```

## Required release gates

1. All required CI jobs pass on protected branch.
2. Backend coverage remains at or above configured threshold.
3. No medium/high security regression in enforced security scans.
4. No failing migration or startup checks in deployment workflows.

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

