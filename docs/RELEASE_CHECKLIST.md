# Release Checklist

## Purpose

Provide a release governance checklist for tagged builds and production deployment approvals.

## Pre-Release Gate

1. [ ] `CHANGELOG.md` updated with release entry.
2. [ ] `docs/DOCS_VERSION.json` version and `updated_at` updated if docs changed.
3. [ ] Local and CI release-governance evidence captured:
   - `python scripts/dev_doctor.py --skip-ports`
   - `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process`
   - `python scripts/verify_lockfiles.py`
   - `python scripts/verify_docs_references.py`
   - `python scripts/validate_schema_parity.py`
   - `python scripts/verify_release_governance.py`
4. [ ] CI jobs pass:
   - lint
   - backend tests
   - frontend build/lint/typecheck/tests
   - governance (parity + lockfiles)
   - windows packaging smoke
5. [ ] Security scans reviewed (dependency audit, CodeQL, Bandit delta, secret scan).
6. [ ] Targeted release-security regressions reviewed:
   - desktop auto-login challenge/security tests
   - trace/export integrity regressions
7. [ ] Installer integrity/signing checks completed for release artifacts:
   - `python scripts/verify_installer_integrity.py --require-artifacts`
   - `powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts -CheckRevocation`

## Evidence Split

Use this split so release evidence stays honest about what can be automated locally versus what requires release artifacts or a live environment.

### Repo-verifiable before tag or promotion

1. `python scripts/dev_doctor.py --skip-ports`
2. `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process`
3. `python scripts/verify_lockfiles.py`
4. `python scripts/verify_docs_references.py`
5. `python scripts/validate_schema_parity.py`
6. `python scripts/verify_release_governance.py`

### Release-runner or artifact-only evidence

1. `python scripts/verify_installer_integrity.py --require-artifacts`
2. `powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts -CheckRevocation`
3. Windows packaging smoke artifact review
4. Release workflow artifact retention confirmed

### Manual approval evidence

1. Code-owner approval recorded on the release PR/tag.
2. Branch protection requirements satisfied on `main`.
3. Rollback plan linked in the release ticket.
4. Disaster recovery restore drill reviewed within the last 30 days.

## Release Approval

1. [ ] At least one code-owner review approved.
2. [ ] Branch protection requirements satisfied (required checks + review count).
3. [ ] Production rollback plan confirmed.
4. [ ] Artifact signing evidence attached to the release ticket.
5. [ ] Disaster recovery restore drill reviewed within the last 30 days.

## Post-Release

1. [ ] Deployment health checks validated.
2. [ ] Metrics/alerts reviewed for first 30 minutes after rollout.
3. [ ] Release notes published.
4. [ ] Rollback command and artifact pointers captured in the release record.
5. [ ] Any production-only gaps or waivers documented before the release is closed.

## Document Control

1. Owner: Release Engineering
2. Last updated: 2026-05-23
3. Status: Active
4. Review cadence: Every release cycle
