# Code Scanning Alert Report

Date: 2026-07-08

Repository: `kherrera6219/DataLogicEngine`

## Live GitHub Code Scanning State

Queried with GitHub CLI:

```powershell
gh api --paginate -H "Accept: application/vnd.github+json" "/repos/kherrera6219/DataLogicEngine/code-scanning/alerts?per_page=100"
```

Results:

| State | Count |
| --- | ---: |
| Open | 8 |
| Fixed | 404 |
| Dismissed | 189 |

## Open Alerts

All open alerts are CodeQL `py/stack-trace-exposure` findings with medium security severity.

| Alert | File | Line | Created | URL |
| --- | --- | ---: | --- | --- |
| #601 | `backend/routes/storage_routes.py` | 265 | 2026-07-09 03:02 UTC | <https://github.com/kherrera6219/DataLogicEngine/security/code-scanning/601> |
| #600 | `backend/routes/storage_routes.py` | 245 | 2026-07-09 03:02 UTC | <https://github.com/kherrera6219/DataLogicEngine/security/code-scanning/600> |
| #599 | `backend/security_api.py` | 236 | 2026-07-09 03:02 UTC | <https://github.com/kherrera6219/DataLogicEngine/security/code-scanning/599> |
| #598 | `backend/routes/retention_routes.py` | 178 | 2026-07-09 03:02 UTC | <https://github.com/kherrera6219/DataLogicEngine/security/code-scanning/598> |
| #596 | `backend/routes/search_routes.py` | 171 | 2026-07-06 01:18 UTC | <https://github.com/kherrera6219/DataLogicEngine/security/code-scanning/596> |
| #595 | `backend/routes/search_routes.py` | 143 | 2026-07-06 01:18 UTC | <https://github.com/kherrera6219/DataLogicEngine/security/code-scanning/595> |
| #594 | `backend/routes/search_routes.py` | 115 | 2026-07-06 01:18 UTC | <https://github.com/kherrera6219/DataLogicEngine/security/code-scanning/594> |
| #593 | `backend/routes/search_routes.py` | 85 | 2026-07-06 01:18 UTC | <https://github.com/kherrera6219/DataLogicEngine/security/code-scanning/593> |

## Recommended Next-Session Remediation

1. Inspect each route and identify public responses that expose `str(exc)`, traceback text, or raw exception details.
2. Replace public responses with stable generic errors and keep detailed exception data in server logs only.
3. Add route regressions proving exception details are not exposed to callers.
4. Run targeted validation:

```powershell
python -m ruff check backend\routes\search_routes.py backend\routes\retention_routes.py backend\routes\storage_routes.py backend\security_api.py
python -m pytest tests\integration_routes tests\security -q
```

5. Re-query GitHub code scanning after push to confirm the alerts move to fixed after CodeQL reruns.
