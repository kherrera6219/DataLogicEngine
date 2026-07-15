# Root Cleanup Review - 2026-07-06

> **Document metadata**
> - Document version: v1.0.0
> - Last reviewed: 2026-07-06
> - Status: Active cleanup review artifact
> - Owner: Documentation Governance / Platform Engineering
> - Scope: Direct repository-root documents, tracked root artifacts, and ignored local root files.

## Review Scope

This pass reviewed direct root files and root-level documentation after the production documentation refresh. It did not review source subdirectories, `docs/` content, or build-output directories except where root cleanup decisions depend on them.

## Root Document Classification

| File | Status | Cleanup decision |
|---|---|---|
| `README.md` | Active source of truth | Keep. Public/root entry point. |
| `TODO.md` | Active source of truth | Keep. Canonical backlog and release-readiness queue. |
| `HANDOFF.md` | Active continuity record | Compacted on 2026-07-12 to the current checkpoint and exact next action; prior session history moved to `docs/archive/session-history/`. |
| `CHANGELOG.md` | Active release history | Keep. Historical model/Kubernetes/Azure references are acceptable as changelog history. |
| `REPO_AUDIT_LOG.md` | Active audit history | Keep. Large by design; root audit references point here. |
| `CONTRIBUTING.md` | Active contributor policy | Keep. |
| `DEVELOPMENT.md` | Active quick-entry guide | Keep. It complements `docs/DEVELOPER_GUIDE.md`. |
| `TESTING.md` | Thin root pointer | Keep for discoverability unless all root links are later moved to `docs/TESTING.md`. |
| `SECURITY.md` | Active security policy | Keep. |
| `SUPPORT.md` | Active support pointer | Keep. |
| `CODE_OF_CONDUCT.md` | Active community policy | Keep. |
| `COMMERCIAL_LICENSE.md` | Active licensing note | Keep. |

## Tracked Root Artifact Cleanup

| File | Finding | Action |
|---|---|---|
| `.bandit-baseline.json` | Required by `.github/workflows/security.yml`, but stale baseline metadata still referenced deleted files. | Regenerated in place with `python -m bandit -r backend/ core/ --exit-zero -f json -o .bandit-baseline.json`. |
| `pip-audit-report.json` | Generated scan snapshot. CI creates and uploads this report as an artifact; the root tracked copy can drift from accepted-risk suppressions and current dependency state. | Deleted from source control and added to `.gitignore`. |
| `.env.template` | Active setup reference. | Keep. |
| `backend.spec` | Active PyInstaller/backend packaging config. | Keep. |
| `uv.lock` | Active dependency lock artifact. | Keep. |

## Ignored Local Root Files

The following ignored local root files are cleanup-safe because they are generated runtime/test/build outputs:

- `.coverage`
- `coverage.json`
- `backend_test.log`
- `build_electron_builder.log`
- `build_electron_ts.log`
- `build_fix_eb.log`
- `build_nextjs_build.log`
- `build_nextjs.log`
- `deployment.log`
- `ukg_system.log`
- `ukg_system.log.1`
- `ukg_system.log.2`
- `ukg_system.log.3`
- `ukg_system.log.4`

The following ignored local root files were intentionally not deleted in this pass:

- `.env` — local secret/config file.
- `DataLogicEngine Setup Latest.exe`, `.blockmap`, `.sha256` — latest installer artifacts referenced by release/install docs.
- `g.bat`, `cleanup.bat` — local helper scripts; delete only with explicit approval if no longer used.

## Future Cleanup Candidates

| Candidate | Recommendation |
|---|---|
| `HANDOFF.md` | After the production rebuild/release lock, compact older session history into `docs/archive/` and keep only the current handoff block in root. |
| `TESTING.md` | Keep until root references are deliberately migrated; then consider replacing it with a one-line redirect or deleting it after link validation. |
| Root installer artifacts | Keep while they are the latest local release artifacts. Move to `reports/release-artifacts/` or an external release store once signed-release packaging is finalized. |
| Local helper scripts `g.bat` and `cleanup.bat` | Confirm owner/use, then delete if obsolete. |

## Validation

After this cleanup:

```powershell
python scripts/generate_docs.py
python scripts/verify_docs_references.py
git diff --check
```
