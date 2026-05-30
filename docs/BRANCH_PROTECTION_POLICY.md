# Branch Protection and Review Policy

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Purpose

Define minimum branch governance requirements for protected branches and establish review controls for architecture, security, release, and documentation changes.

## Protected branches

Default protected branches:

1. `main`
2. `develop` (where used)
3. release branches where configured

---

## Required protection settings

1. Require pull request before merge.
2. Require at least one approval.
3. Require code-owner approval where applicable.
4. Dismiss stale approvals when new commits are pushed.
5. Require all configured status checks to pass.
6. Require conversation resolution before merge.
7. Restrict direct pushes to approved maintainers and automation.
8. Require branch to be up to date before merge where supported.

---

## Required status checks

Representative protected checks:

1. lint/typecheck;
2. backend tests;
3. frontend build/tests;
4. contract/parity/security tests where configured;
5. governance validation;
6. documentation validation;
7. Windows packaging smoke checks;
8. release-signing validation where applicable.

The exact set may evolve with CI workflow names.

---

## Code-owner governance

`CODEOWNERS` is the source of review ownership.

The following categories should receive code-owner review:

1. authentication and authorization;
2. security controls;
3. release governance;
4. deployment and infrastructure;
5. DMRF and Truth Engine core behavior;
6. privacy/export controls;
7. documentation governance and production-readiness claims.

---

## Documentation governance

Changes to active source-of-truth documentation should:

1. follow `docs/DOCUMENTATION_STANDARDS.md`;
2. follow `docs/DOCUMENTATION_VERSIONING.md`;
3. update `docs/DOCUMENTATION_COVERAGE_MATRIX.md` where required;
4. avoid unsupported compliance, certification, or benchmark claims;
5. distinguish active docs from archived research.

---

## Validation

```powershell
python scripts/verify_docs_references.py
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
```

Release-impacting changes should also pass:

```powershell
python scripts/verify_release_governance.py
```

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Expanded governance coverage to include DMRF, Truth Engine, privacy/export, and documentation governance.
3. Updated status-check language to align with current CI and release validation model.
4. Added validation guidance.
