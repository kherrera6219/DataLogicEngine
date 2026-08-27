# CI quality policy

| Field | Value |
|---|---|
| Date | 2026-08-27 |
| Applies to | `.github/workflows/ci.yml` |

## Coverage

| Context | Policy |
|---|---|
| **CI** (`backend-test`) | Complete `pytest tests/` run with `backend/` and `core/` instrumentation, followed by the independent Python scope gate |
| **CI** (`frontend-build`) | Complete Vitest V8 coverage run with independent statements, branches, functions, and lines gates |
| **Threshold enforcement** | Hard minimum of 80.00% for every scope and metric listed below |

Fresh 2026-08-27 4.4.3 coverage measurement:

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
a failing result elsewhere. The clean qualification passed 3,317 Python tests
with 19 skipped and 484 frontend tests. At commit `43fd86df...`, Deploy run
`33039993475`, Security run `33039993480`, and CI/CD run `33039993472` pass.

## Accessibility (a11y)

| Context | Policy |
|---|---|
| **CI** (`frontend-build` a11y sweep) | `continue-on-error: true` — soft gate |
| **Release claims** | Hard a11y fail only when product claims formal a11y conformance for that build |

Soft fail keeps packaging/test CI green while a11y tooling or browser deps are incomplete on runners.

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
