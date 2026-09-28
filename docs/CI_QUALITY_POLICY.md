# CI quality policy

| Field | Value |
|---|---|
| Last reviewed | 2026-09-27 |
| Applies to | `.github/workflows/ci.yml` |

## Coverage

| Context | Policy |
|---|---|
| **CI** (`backend-test`) | Complete `pytest tests/` run with `backend/` and `core/` instrumentation, followed by the independent Python scope gate |
| **CI** (`frontend-build`) | Complete Vitest V8 coverage run with independent statements, branches, functions, and lines gates |
| **Threshold enforcement** | Hard minimum of 80.00% for every scope and metric listed below |

Historical 2026-08-27 4.4.3 coverage measurement (not a current PR #91 measurement):

| Denominator | Result |
|---|---:|
| Python `backend/` | 80.29% |
| Python `backend/security/` | 80.67% |
| Python `core/` | 81.07% |
| Frontend statements | 89.54% (2,474 / 2,763) |
| Frontend branches | 80.69% (1,902 / 2,357) |
| Frontend functions | 86.11% (701 / 814) |
| Frontend lines | 91.36% (2,337 / 2,558) |

Commands:

```powershell
.\.venv311\Scripts\python.exe -m pytest tests -q --cov=backend --cov=core --cov-report=json:coverage-python.json
python scripts/verify_python_coverage.py --report coverage-python.json --minimum 80
npm --prefix frontend run test:coverage
```

There is no truthful single combined application percentage because Python and
V8 use different coverage models. The gate therefore requires each named Python
scope and each V8 metric to pass independently; one strong result cannot conceal
a failing result elsewhere. That clean qualification passed 3,317 Python tests
with 19 skipped and 484 frontend tests. At historical commit `43fd86df...`,
Deploy run `33039993475`, Security run `33039993480`, and CI/CD run
`33039993472` passed; those runs do not establish current-source readiness.

At the 2026-09-27 [PR #91 source checkpoint](https://github.com/kherrera6219/DataLogicEngine/pull/91),
frontend-build, governance, lint, Windows packaging smoke, and npm audit passed.
The [backend-test job](https://github.com/kherrera6219/DataLogicEngine/actions/runs/36345725446/job/108694356022)
stopped at its Python security audit before the test suite, and the separate
[Dependency Security Scan](https://github.com/kherrera6219/DataLogicEngine/actions/runs/36345725461/job/108694356125)
also failed. Both found locked transitive `nltk==3.10.3` affected by
`PYSEC-2026-3740` / `CVE-2026-81726`; this finding is not suppressed. The
[advisory](https://github.com/advisories/GHSA-8mgp-746c-j5xp) lists no patched
version as of this checkpoint. A repository-source merge does not convert
these red gates to green, waive the finding, or approve an installed release.
Production/public release remains **NO-GO** pending a resolved security gate
and exact-source installed qualification.

The post-merge `main` [Deploy run](https://github.com/kherrera6219/DataLogicEngine/actions/runs/36378632388)
is a separate negative test result: its Linux Python suite reported one
failing refinement-workflow test (3,355 passed, 26 skipped). The local Windows
pass does not close that result. Diagnose and retest the current source without
skipping or weakening the test before treating the source gate as green.

## Accessibility (a11y)

| Context | Policy |
|---|---|
| **CI** (`frontend-build` a11y sweep) | `continue-on-error: true` — soft gate |
| **Release claims** | Hard a11y fail only when product claims formal a11y conformance for that build |

The frontend CI job now installs Playwright Chromium and its system dependencies
before the sweep. The sweep remains `continue-on-error: true` (a soft gate);
browser setup does not constitute formal a11y conformance. A sweep failure is
not an approved release claim and must be dispositioned before such a claim.

## Structural guards (hard in CI)

| Check | Script / test |
|---|---|
| Orphan `.pyc` | `python scripts/scan_orphan_pyc.py --fail-on-orphan` |
| Route uniqueness | `python scripts/verify_route_uniqueness.py` |
| Single governed path | `tests/governed_execution/test_single_path.py` (suite) |
| Security wiring | `tests/security/test_security_module_wiring.py` (suite) |

## Packaging smoke

Windows job builds the installer and runs `scripts/windows/run_packaging_smoke.ps1`.
Resource presence (backend exe, policies, release JSON) is checked by
`scripts/windows/verify_packaging_resources.ps1` before portable launch smoke.
