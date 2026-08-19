# DataLogicEngine 80% Coverage Execution Plan

| Field | Value |
|---|---|
| Date | 2026-08-16 |
| Status | Complete; clean independent-scope qualification passed |
| Scope | Python `backend/`, Python `backend/security/`, Python `core/`, and frontend V8 statements/branches/functions/lines |
| Rule | Every listed scope and metric must independently meet or exceed 80%; combined percentages cannot mask a failing scope |

## Objective

Raise the maintained application test suites to a truthful 80% minimum across
the backend, core reasoning engine, security package, and every frontend V8
coverage metric. Coverage exclusions must not be added merely to change the
denominator. Gains must come from executable contract, error-boundary, state,
and UI behavior tests, or from a separately justified removal of dead code.

## Measured starting point

| Scope | Starting result | Initial gap to 80% |
|---|---:|---:|
| Python backend | 76.82% (35,728 / 46,511) | 1,481 statements |
| Python security | 79.26% (1,624 / 2,049) | 16 statements |
| Python core | 36.75% initial audit baseline; 76.01% after the first remediation batch | 6,497 statements initially; 611 statements after first batch |
| Frontend statements | 76.29% (2,108 / 2,763) | 103 statements |
| Frontend branches | 65.71% (1,549 / 2,357) | 337 branches |
| Frontend functions | 71.37% (581 / 814) | 71 functions |
| Frontend lines | 78.53% (2,009 / 2,558) | 38 lines |

The core initial-gap shorthand is intentionally not used as release evidence;
the authoritative numerator and denominator come from the final clean report.

## Execution phases

1. Measure each denominator with the complete repository test suite.
2. Add focused core contracts for orchestration, simulation, graph, POV,
   coordinate, axis, refinement, and advanced reasoning paths.
3. Add focused backend contracts for database, API, entrypoint, coordination,
   compliance, security, logging, persona, and queue behavior.
4. Add frontend interaction and failure-path tests for the largest uncovered
   settings, trace, queue, MCP, and client-gateway components.
5. Run exact union checks, then rerun clean full-suite reports for release
   evidence.
6. Enable blocking gates only after all independent scopes pass.
7. Synchronize the production plan, TODO, handoff, testing policy, changelog,
   and generated documentation inventories.
8. Rebuild and smoke-check the local Windows installer. Do not publish or push
   unless the owner separately authorizes it.

## Gate design

- `scripts/verify_python_coverage.py` reads Coverage.py JSON and independently
  enforces backend, backend/security, and core at 80%.
- `frontend/vitest.config.ts` independently enforces V8 statements, branches,
  functions, and lines at 80%.
- CI runs the complete Python suite with backend/core instrumentation and the
  complete frontend suite with V8 coverage.
- Local focused reports may be unioned for diagnostic qualification, but final
  release evidence must include a clean complete-suite run.

## Current evidence checkpoint

| Scope | Current measured result | State |
|---|---:|---|
| Python backend complete suite | 80.30% (37,348 / 46,511) | Pass |
| Python security complete suite | 80.67% (1,653 / 2,049) | Pass |
| Frontend complete suite | statements 89.54%, branches 80.69%, functions 86.11%, lines 91.36% | Pass |
| Python core complete suite | 80.89% (12,374 / 15,298) | Pass |

The final runs passed 3,287 Python tests with 18 skipped and 482 frontend tests.
The Python verifier and Vitest hard thresholds both exit successfully at an
80.00% minimum.

## Final local rebuild

The coverage-qualified local artifact is `DataLogicEngine Setup 4.4.0.exe`
(358,859,969 bytes; SHA-256
`1da8b8d6a10b1ce72993448baf0c18d2eb41749f7aa7d76b43d4d085983be521`).
Installer integrity, NSIS governance, packaged resources, and package-owned
portable backend readiness pass; `/ready` completed in 30,790 ms. The artifact
is unsigned and was built immediately before source checkpoint `5e8733b3` was
committed to `main` (based on `b3132966`). It was not rebuilt from that clean
commit and does not satisfy CP19-M signed/clean-source or installed acceptance.

## Completion criteria

- All independent scopes and metrics are at least 80.00%.
- All tests pass without coverage exclusions added to manufacture the result.
- Frontend lint, typecheck, unit coverage, and production build pass.
- Python documentation/reference gates pass.
- The local installer is rebuilt and packaging smoke/integrity reports are
  refreshed.
- `HANDOFF.md`, `TODO.md`, `PRODUCTION_COMPLETION_PLAN_2026.md`, and
  `docs/CI_QUALITY_POLICY.md` contain the final exact measurements and any
  remaining non-coverage blockers.
