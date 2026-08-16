# CI quality policy

| Field | Value |
|---|---|
| Date | 2026-08-12 |
| Applies to | `.github/workflows/ci.yml` |

## Coverage

| Context | Policy |
|---|---|
| **CI** (`backend-test`) | `pytest tests/ --no-cov` — functional pass/fail is the gate |
| **Local phased runner** | `python run_test_suite.py` may still run a full-suite coverage pass at the end |
| **Threshold enforcement** | Not a hard CI fail-under today (avoids flaky gates on a large solo monorepo) |

When enabling CI fail-under later, set a realistic floor after measuring a clean main baseline.

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
