# Dependency alert remediation - 2026-08-01

## Scope and result

The live GitHub query before this batch reported 31 open Dependabot alerts: 19
high and 12 moderate. Five affected direct Python pins and advisories were
represented by `pypdf` and `web3`; 26 Node alerts affected direct or transitive
packages in `frontend/package-lock.json`.

All reported vulnerable ranges are absent from the regenerated authorities.
The Python release lock is regenerated with hashes, the Node lock is refreshed,
and no alert was dismissed or waived. After the patched default-branch
authorities were indexed, the live GitHub query reported zero open Dependabot
alerts.

## Reviewed changes

- Python: `pypdf` 6.13.3 -> 6.14.2 and `web3` 7.14.0 -> 7.15.0.
- Product/frontend: Next 16.2.12 and patched `postcss`/`sharp` resolutions.
- Desktop tooling: Electron Builder 26.15.3, Electron Updater 6.8.9,
  `app-builder-lib` 26.15.3, and `builder-util-runtime` 9.7.0.
- Development/runtime transitives: patched `adm-zip`, `axios`,
  `brace-expansion`, `fast-uri`, `js-yaml`, `shell-quote`, and `tar` versions.
- Accessibility/concurrency/readiness tooling was updated to current compatible
  releases so their dependency ranges admit the patched transitive versions.

## Verification

- `.venv311/Scripts/python -m pip_audit -r requirements.txt --format json`:
  no known vulnerabilities.
- `npm --prefix frontend audit --json`: zero vulnerabilities.
- `python scripts/verify_lockfiles.py`: pass; 80 Python direct pins, 290
  hash-locked Python packages, and current Node lock/root parity.
- `gh api --paginate repos/kherrera6219/DataLogicEngine/dependabot/alerts
  -f state=open`: zero open hosted alerts after the default-branch rescan.
- Frontend lint: zero errors and one unchanged unused-test-parameter warning.
- Frontend type checking, 426 tests, production Next build, and Electron
  TypeScript compilation: pass.
- Current full source suite: 2,588 passed, 18 skipped, 35 known warnings.

## Release boundary

This is source dependency remediation. It does not satisfy CP19-L clean-source
qualification, authorize a rebuild, replace installed-system scanning, or
change the production/public release NO-GO decision.
