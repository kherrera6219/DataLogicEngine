# Dependabot Alert Remediation Report

Date: 2026-07-07

Repository: `kherrera6219/DataLogicEngine`

## Live GitHub Alert State

Queried with GitHub CLI:

```powershell
gh api --paginate -H "Accept: application/vnd.github+json" "/repos/kherrera6219/DataLogicEngine/dependabot/alerts?per_page=100"
```

Results:

| State | Count |
| --- | ---: |
| Open | 0 |
| Fixed | 418 |
| Dismissed | 5 |

## Dismissed Alerts Remediated

All dismissed alerts had dismissal reason `fix_started` and pointed at stale `uv.lock` transitive package versions.

| Alert | Package | Manifest | Patched Version | Resolution |
| --- | --- | --- | --- | --- |
| #377 | `urllib3` | `uv.lock` | `2.7.0` | Updated lock entry to `2.7.0` |
| #363 | `urllib3` | `uv.lock` | `2.7.0` | Updated lock entry to `2.7.0` |
| #360 | `Mako` | `uv.lock` | `1.3.12` | Updated lock entry to `1.3.12` |
| #335 | `Mako` | `uv.lock` | `1.3.11` | Updated lock entry to `1.3.12` |
| #274 | `werkzeug` | `uv.lock` | `3.1.6` | Updated lock entry to `3.1.8` |

## Local Remediation

Command:

```powershell
.\.venv\Scripts\uv.exe lock --upgrade-package urllib3 --upgrade-package mako --upgrade-package werkzeug
```

Updated packages:

- `mako` `1.3.10` -> `1.3.12`
- `urllib3` `2.6.3` -> `2.7.0`
- `werkzeug` `3.1.5` -> `3.1.8`

## Follow-Up

GitHub may need a short re-scan window before the dismissed historical alerts move from `dismissed` to `fixed` or remain historical-only. There are no open Dependabot alerts at the time of this report.
