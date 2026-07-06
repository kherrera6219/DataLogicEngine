# Release Checklist

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.7.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Release Engineering |
| Review cadence | Every release cycle |

## Purpose

Provide the release governance checklist for tagged builds, desktop installer distribution, controlled production deployment, and public release approvals.

This checklist ties together current architecture, security, testing, deployment, production readiness, local-first desktop packaging, artifact signing, trace/export integrity, and operational evidence.

## Related documents

1. `docs/ARCHITECTURE.md`
2. `docs/API.md`
3. `docs/SECURITY.md`
4. `docs/TESTING.md`
5. `docs/DEPLOYMENT.md`
6. `docs/PRODUCTION_READINESS.md`
7. `docs/OPERATIONAL_RUNBOOKS.md`
8. `docs/SDLC_SSDF_MAPPING.md`
9. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
10. `.github/workflows/ci.yml`
11. `.github/workflows/deploy.yml`
12. `.github/workflows/release-installer-signing.yml`

---

## Release scope classification

Before applying the checklist, classify the release:

| Release type | Description | Required evidence level |
|---|---|---|
| Local engineering release | Internal development/test build. | local validation, smoke, targeted tests. |
| Contest/demo release | Repository presentation, judge review, technical demo. | docs current, CI evidence, reproducible build/test path, caveats documented. |
| Desktop release candidate | Installer/package candidate before signed distribution. | packaging smoke, NSIS governance, local-first runbook evidence. |
| Signed Windows production release | Public or customer-distributed Windows installer. | trusted signing, signature verification, packaging smoke, release approval. |
| Web/cloud production release | Hosted production deployment. | production security config, provider staging validation, health/readiness/metrics, rollback plan. |

---

## Local-first status

Local-first desktop Phase 1 completion evidence is recorded in:

```text
reports/release-readiness/local-first-phase1-completion-2026-05-25.md
```

The latest local desktop rebuild evidence is tracked through the root installer artifacts, `reports/installer_integrity_report.json`, `reports/installer_signature_report.json`, and `reports/packaging_smoke_report.json`. Local unsigned builds may report `NotSigned`; that is acceptable for workstation validation but not for public/customer signed distribution.

Unchecked items in this checklist should be interpreted as production/public release gates unless explicitly scoped to local engineering or contest/demo release.

---

## Pre-release gate

1. [ ] Release scope selected and recorded.
2. [ ] `CHANGELOG.md` updated with release entry.
3. [ ] `docs/DOCS_VERSION.json` version and `updated_at` updated if docs changed.
4. [ ] Updated docs include version/date metadata.
5. [ ] Architecture, API, Security, Testing, Deployment, Database/Data, Production Readiness, Operational Runbooks, and Release Checklist docs are current.
6. [ ] Known caveats and release blockers are documented in the release ticket.

---

## Required local/repo-verifiable evidence

Run and attach evidence for:

```powershell
python scripts/dev_doctor.py --skip-ports
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
python scripts/verify_lockfiles.py
python scripts/verify_docs_references.py
python scripts/validate_schema_parity.py --report reports/schema_parity_report_release.json
python scripts/verify_environment_parity.py --strict --json-report reports/environment_parity_report_release.json
python scripts/verify_release_governance.py
```

Checklist:

1. [ ] `dev_doctor` passes.
2. [ ] runtime precheck passes in strict mode.
3. [ ] lockfile governance passes.
4. [ ] documentation references pass.
5. [ ] schema parity passes.
6. [ ] environment parity passes.
7. [ ] release governance verifier passes.
8. [ ] No production profile uses `AUTO_CREATE_SCHEMA=true`.
9. [ ] Production secrets are not defaults.

---

## CI gate

Required CI jobs:

1. [ ] `lint`
2. [ ] `backend-test`
3. [ ] `frontend-build`
4. [ ] `windows-packaging-smoke`
5. [ ] `governance`
6. [ ] `docker-build` where applicable

Required test coverage areas:

1. [ ] backend tests.
2. [ ] API contract tests.
3. [ ] canonical `/api/v1/*` route tests.
4. [ ] local-mode parity tests.
5. [ ] security regression tests.
6. [ ] Truth Engine tests.
7. [ ] Knowledge Algorithm tests.
8. [ ] 17-axis tests.
9. [ ] frontend lint/typecheck/unit/build.
10. [ ] Playwright route smoke.
11. [ ] accessibility sweep.
12. [ ] visual regression smoke.

---

## Security and supply-chain gate

1. [ ] Dependency audit reviewed.
2. [ ] Secret scan or equivalent repository secret review completed.
3. [ ] Security regression suite reviewed.
4. [ ] Desktop auto-login challenge/security tests reviewed.
5. [ ] Trace/export integrity regressions reviewed.
6. [ ] Desktop-auth route contract tests reviewed (single-mode / OS-level auth).
7. [ ] Object-store path traversal/security tests reviewed where changed.
8. [ ] MCP scope/contract tests reviewed where connector changes are included.
9. [ ] Lockfile changes reviewed.
10. [ ] No unverified claims are added to security/compliance docs.

Note: only claim CodeQL, Bandit, Safety, SBOM, Sigstore/cosign, DAST, or SAST evidence when the current workflow artifacts directly prove those checks ran.

---

## Desktop installer gate

Required for desktop release candidate and signed Windows production release:

```powershell
.\.venv\Scripts\python.exe scripts\build_backend.py
$env:CSC_SKIP = "true"
npm --prefix frontend run electron:dist
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
.\.venv\Scripts\python.exe scripts\verify_installer_integrity.py --require-artifacts
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path -Mode installer
```

Checklist:

1. [ ] Electron installer build completed.
2. [ ] backend executable build completed before Electron packaging.
3. [ ] NSIS governance passed.
4. [ ] installer integrity verification passed.
5. [ ] portable packaging smoke passed.
6. [ ] installer-mode install/uninstall smoke passed where release scope requires install behavior evidence.
7. [ ] installer artifact paths captured.
8. [ ] checksum/blockmap sidecars captured where generated.
9. [ ] packaging reports attached to release record.

---

## Signed Windows release gate

Required for public/customer Windows installer distribution:

1. [ ] `WINDOWS_CODESIGN_CERT_BASE64` configured.
2. [ ] `WINDOWS_CODESIGN_CERT_PASSWORD` configured.
3. [ ] signing certificate health/rotation check passed.
4. [ ] installer signing completed.
5. [ ] installer signature verification passed.
6. [ ] signed artifacts uploaded.
7. [ ] signature reports attached.
8. [ ] local dev certificates were not used as production evidence.

Verification command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts -CheckRevocation
```

---

## Web/cloud production gate

Required only for web/cloud deployment:

1. [ ] HTTPS enforced.
2. [ ] trusted hosts configured.
3. [ ] CORS allowlist configured with no production wildcard.
4. [ ] CSRF origin/token behavior verified.
5. [ ] secure cookies enabled.
6. [ ] rate limiting enabled.
7. [ ] desktop local-auth trust is disabled/not accepted as cloud trust.
8. [ ] provider-backed staging run completed.
9. [ ] `/health`, `/live`, `/ready`, and `/metrics` validated.
10. [ ] rollback plan validated.
11. [ ] production secrets sourced securely.

---

## Accessibility and privacy gate

1. [ ] automated accessibility sweep reviewed.
2. [ ] keyboard navigation evidence reviewed.
3. [ ] manual screen-reader evidence completed or waiver documented.
4. [ ] privacy settings flow reviewed.
5. [ ] user export/delete flows reviewed.
6. [ ] AI/cloud/provider disclosures reviewed.
7. [ ] AI limitations page reviewed.
8. [ ] no critical accessibility/privacy blocker remains open.

---

## Manual approval evidence

1. [ ] Code-owner approval recorded on release PR/tag.
2. [ ] Branch protection requirements satisfied.
3. [ ] Release scope and risk accepted by owner.
4. [ ] Production rollback plan linked.
5. [ ] Disaster recovery restore drill reviewed within the required window, where applicable.
6. [ ] Known caveats/waivers explicitly accepted.
7. [ ] Release notes approved.

---

## Post-release validation

1. [ ] Deployment health checks validated.
2. [ ] `/health`, `/live`, `/ready`, `/metrics` checked.
3. [ ] Core auth path validated.
4. [ ] Gateway/DMRF request path validated.
5. [ ] Trace Explorer path validated.
6. [ ] Error rates and latency reviewed for first 30 minutes after rollout.
7. [ ] Release notes published.
8. [ ] Rollback command and artifact pointers captured.
9. [ ] Production-only gaps or waivers documented before release closure.

---

## Release decision template

```text
Release name/tag:
Release type:
Release owner:
Release date:
Commit SHA:

Decision:
[ ] Approved
[ ] Approved with caveats
[ ] Blocked

Required caveats/waivers:
- 

Evidence attached:
- runtime precheck:
- schema parity:
- docs validation:
- environment parity:
- lockfile governance:
- CI run:
- packaging smoke:
- signing report:
- accessibility evidence:
- release notes:
```

---

## Change notes for v2.7.0

1. Updated the desktop installer gate to require the backend build before Electron/NSIS packaging.
2. Added installer integrity verification and installer-mode install/uninstall smoke to release-candidate evidence.
3. Clarified that unsigned local `NotSigned` reports are workstation validation evidence only, not public release evidence.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Added release scope classification.
3. Expanded local/repo-verifiable evidence gates.
4. Added CI, security, supply-chain, desktop installer, signed Windows release, web/cloud, accessibility/privacy, and post-release gates.
5. Added evidence-driven caveat against overclaiming unverified scanner/SBOM/signing tools.
6. Added release decision template.
