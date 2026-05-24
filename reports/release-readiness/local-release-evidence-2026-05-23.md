# Local Release Evidence

Date: 2026-05-23

## Repo-Verifiable Commands

| Command | Result | Notes |
| --- | --- | --- |
| `python scripts/dev_doctor.py --skip-ports` | Passed | Warnings: not running inside a virtual environment; `templates/` directory is missing. Action item: initialize local schema via `scripts/windows/start_local_stack.ps1`. |
| `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process` | Passed | Strict mode reports 0 blockers and 0 action items after local SQLite schema initialization. Warnings remain: not running inside a virtual environment; `templates/` directory is missing. |
| `python scripts/verify_lockfiles.py` | Passed | Report written to `reports/lockfile_governance_report.json`. |
| `python scripts/verify_docs_references.py` | Passed | Documentation references are valid after the TODO and README consolidation. |
| `python scripts/validate_schema_parity.py` | Passed | Report written to `reports/schema_parity_report.json`. |
| `python scripts/verify_release_governance.py` | Passed | Report written to `reports/release_governance_report.json`. |

## Release-Runner Or Manual Evidence Still Required

1. Review current CI results for the release branch or tag.
2. Review security scan output for the release branch or tag.
3. Produce signed installer artifacts through `.github/workflows/release-installer-signing.yml`.
4. Attach code-owner approval, rollback plan, disaster recovery review, and artifact signing evidence to the release ticket.
