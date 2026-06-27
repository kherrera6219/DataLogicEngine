# Production Readiness Guide

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.8.0 |
| Last updated | 2026-06-26 |
| Status | Active |
| Owner | Platform Operations |
| Review cadence | Every 30 days |

## Purpose

Provide production acceptance criteria, operational controls, validation checkpoints, and release-readiness scoring for DataLogicEngine.

This version aligns production readiness with the current architecture: DMRF control plane, Truth Engine v7.3, local-first desktop/VM deployment, canonical `/api/v1/*` routes, multi-store data architecture, trace/export integrity, security controls, packaging smoke tests, and release-governance validation.

## Audience

1. Platform and release engineers
2. SRE and operations teams
3. Security/compliance stakeholders
4. Engineering managers
5. Desktop packaging maintainers
6. Technical judges and external reviewers

## Related documents

1. `docs/ARCHITECTURE.md`
2. `docs/API.md`
3. `docs/DEPLOYMENT.md`
4. `docs/DATABASE_SCHEMA.md`
5. `docs/TESTING.md`
6. `docs/RELEASE_CHECKLIST.md`
7. `docs/OPERATIONAL_RUNBOOKS.md`
8. `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
9. `docs/diagrams/08_testing_validation_and_release_governance.md`
10. `docs/diagrams/12_end_to_end_request_lifecycle.md`

---

## Production readiness status

Current status: **application-readiness validation is strong for local-first/desktop and engineering review, but signed production release still requires final external evidence and credential validation.**

### Ready / substantially implemented

1. Local-first desktop architecture.
2. Canonical `/api/v1/*` API route policy.
3. JSON-native auth/error behavior for tested canonical routes.
4. DMRF control-plane lifecycle.
5. Truth Engine modules: TruthGate, TruthCore, TruthMemory, TruthLink.
6. Multi-store data architecture: SQL, Redis, Neo4j, ChromaDB, object store, USKD memory graph, UnifiedMemory, TruthMemory.
7. Trace Explorer and export integrity architecture.
8. Runtime precheck, docs reference validation, schema parity, environment parity, and lockfile governance.
9. CI jobs for backend, frontend, packaging, governance, and Docker build verification.
10. Windows packaging smoke and NSIS governance checks.
11. Privacy controls, cloud/AI disclosures, local-first product copy, and admin/compliance surfaces.
12. Frontend accessibility automation path and visual/E2E testing path.

### Remaining release blockers before signed production distribution

1. Manual NVDA or equivalent assistive-technology evidence for accessibility release signoff.
2. Provisioned trusted production signing credentials.
3. Signed release artifact validation.
4. Final provider-configured staging run for gateway-backed query/simulation paths.
5. Final release checklist completion with generated reports attached.
6. Confirmation that no production build uses default secrets, `AUTO_CREATE_SCHEMA=true`, or desktop-only trust in cloud mode.

Keep tactical task tracking in `TODO.md`; keep this guide focused on release criteria and validation controls.

---

## Production readiness scorecard

| Domain | Status | Required evidence |
|---|---|---|
| Architecture | Ready for review | `docs/ARCHITECTURE.md`, diagram set, DMRF/Truth Engine files. |
| API contract | Mostly ready | Contract tests, canonical `/api/v1/*` docs, route governance headers. |
| Security | Ready with release caveats | Security tests, runtime precheck, desktop auth tests, secret validation, signing evidence. |
| Data/storage | Ready for local-first | Schema parity report, storage mode verification, object/vector/graph health. |
| Testing | Strong | Backend/frontend/contract/parity/security/governance/packaging CI. |
| Frontend/product | Strong | Dashboard, chat, trace, graph, Truth Engine, MCP, admin, privacy/disclosure surfaces. |
| Desktop packaging | Strong but signing-dependent | NSIS governance, packaging smoke, signed artifact verification. |
| Accessibility | Automated path present; manual evidence pending | Playwright/a11y sweep plus manual screen-reader evidence. |
| Observability | Strong baseline | `/health`, `/live`, `/ready`, `/metrics`, DMRF/Truth status, trace review. |
| Production cloud | Controlled/conditional | HTTPS, trusted hosts, CORS, secrets, provider staging test, no desktop trust assumptions. |

---

## Production checklist

### Required before any release candidate

1. `docs/API.md`, `docs/ARCHITECTURE.md`, `docs/DEPLOYMENT.md`, `docs/DATABASE_SCHEMA.md`, `docs/TESTING.md`, and this document have current version/date metadata.
2. `scripts/runtime_precheck.py --strict` passes.
3. `scripts/verify_docs_references.py` passes.
4. `scripts/validate_schema_parity.py` passes.
5. `scripts/verify_environment_parity.py --strict` passes.
6. `scripts/verify_lockfiles.py` passes.
7. Backend pytest suite passes.
8. API contract, local-mode parity, and security sweeps pass.
9. Frontend lint, typecheck, tests, build, E2E, accessibility, and visual regression checks pass or have documented accepted exceptions.
10. Windows packaging smoke passes for desktop release.
11. NSIS governance passes for installer release.
12. Docker build verification passes where applicable.
13. Release governance verifier passes.
14. No default secrets are present in production config.
15. `AUTO_CREATE_SCHEMA=true` is not enabled in production.
16. Production cloud mode does not rely on desktop loopback auth.
17. Trace export integrity path is verified.
18. Health/readiness/metrics endpoints are verified in target runtime.

### Required before signed Windows production distribution

1. Trusted signing certificate is available.
2. `WINDOWS_CODESIGN_CERT_BASE64` is configured.
3. `WINDOWS_CODESIGN_CERT_PASSWORD` is configured.
4. Signing certificate health/rotation validation passes.
5. Installer signing completes.
6. Installer signature verification passes.
7. Signed installer and reports are uploaded as artifacts.
8. Packaging smoke is run against the signed artifact when practical.

---

## Security hardening

Required production security controls:

1. Strong `SESSION_SECRET`.
2. Strong JWT/API-key secrets where enabled.
3. HTTPS enforcement in web/cloud mode.
4. Trusted host validation.
5. CORS allowlist with no production wildcard.
6. CSRF token/origin validation.
7. Secure session cookies.
8. Rate limiting enabled.
9. API JSON error behavior for canonical routes.
10. TruthGate enabled for governed reasoning paths.
11. DMRF injection defense enabled for DMRF routes.
12. Desktop local auth restricted to local/hybrid desktop runtime.
13. DPAPI helper available for Windows-local protected data where applicable.
14. Trace export integrity enabled for export workflows.
15. Production logs must not expose secrets, provider keys, or raw credentials.

Implementation note: `EncryptionManager` writes new field-level encrypted payloads with AES-256-GCM and records `AES-256-GCM` in the key registry; legacy `Fernet-AES-128-CBC` entries remain decryptable for backward compatibility.

---

## Operational readiness

Required endpoints:

1. `/health` — process/database/session-secret health.
2. `/live` — liveness.
3. `/ready` — readiness.
4. `/metrics` — Prometheus-format metrics.
5. `/api/v1/truth/health` — Truth Engine health where route is enabled.

Required operational reports:

1. runtime precheck report;
2. schema parity report;
3. environment parity report;
4. lockfile governance report;
5. packaging smoke report;
6. NSIS governance report;
7. release checklist evidence;
8. accessibility report/evidence;
9. signed artifact verification report for production distribution.

---

## Deployment architecture

Production readiness must be evaluated by target.

| Target | Readiness requirements |
|---|---|
| Windows desktop | local stack, Electron shell, backend loopback service, desktop local auth, internal storage, packaging smoke, signing. |
| Windows VM | same internal app stack as desktop, VM-local storage, health/readiness checks, no managed cloud DB substitution by default. |
| Web/cloud | HTTPS, trusted host/CORS/CSRF/session hardening, provider staging tests, explicit database/storage approval, no desktop trust assumption. |

See `docs/DEPLOYMENT.md` for deployment procedures.

---

## Data and storage readiness

Required data checks:

1. SQL migrations are current where migration-managed DB is used.
2. SQLite/PostgreSQL schema parity validation passes where applicable.
3. `AUTO_CREATE_SCHEMA=true` is not used in production.
4. Object store buckets initialize correctly.
5. ChromaDB local vector path is writable where vector search is enabled.
6. Neo4j graph store is reachable where configured.
7. USKD memory graph loads from configured source.
8. UnifiedMemory JSON persistence path is writable.
9. TruthMemory audit/artifact/metrics paths work.
10. Trace export integrity can generate valid manifest and hashes.

See `docs/DATABASE_SCHEMA.md` for the current data architecture.

---

## Testing and release validation

Required testing gates:

1. backend pytest;
2. backend coverage gate;
3. API contract tests;
4. canonical `/api/v1/*` route tests;
5. local-mode parity tests;
6. security regression tests;
7. Truth Engine tests;
8. Knowledge Algorithm tests;
9. 17-axis tests;
10. frontend lint/typecheck/unit/build;
11. Playwright route smoke;
12. accessibility sweep;
13. visual regression;
14. Windows packaging smoke;
15. NSIS governance;
16. environment parity;
17. lockfile governance;
18. release governance verifier;
19. Docker build verification where applicable.

See `docs/TESTING.md` for commands and quality baseline.

---

## Production code-signing path

The trusted Windows signing path is the `Release Installer Signing` GitHub Actions workflow.

Required secrets:

1. `WINDOWS_CODESIGN_CERT_BASE64`
2. `WINDOWS_CODESIGN_CERT_PASSWORD`

Expected workflow path:

1. Build unsigned installer.
2. Validate certificate health and rotation threshold using `scripts/windows/verify_signing_certificate_health.ps1`.
3. Sign installers using `scripts/windows/sign_release_installers.ps1`.
4. Verify signatures using `scripts/windows/verify_installer_signature.ps1`.
5. Upload signed installers and reports.

Local development certificates are valid only for workstation validation and must not be treated as production signing evidence.

---

## Accessibility readiness

Automated accessibility checks are part of the frontend validation path, but production release still requires manual assistive-technology evidence.

Required evidence:

1. automated a11y sweep output;
2. keyboard navigation evidence;
3. screen-reader evidence such as NVDA manual pass/fail notes;
4. documented exceptions with remediation plan;
5. no critical blocker for desktop auto-login, dashboard, chat, trace review, settings/privacy, and admin/compliance flows.

---

## Compliance and audit readiness

Required compliance/audit controls:

1. audit logs available for security-relevant events;
2. TruthMemory audit/explainability data generated for Truth Engine sessions;
3. trace runs visible through Trace Explorer;
4. trace exports include integrity metadata;
5. privacy settings and export/delete flows are present;
6. cloud-service and AI-limitation disclosures are present;
7. admin/compliance surfaces are protected by the single-owner auth check (single-mode OS-level auth);
8. release evidence is attached to release checklist.

---

## Failure-mode readiness

A release candidate must demonstrate safe behavior for:

1. missing provider credentials;
2. provider outage;
3. runtime precheck failure;
4. schema parity mismatch;
5. failed auth/session;
6. desktop auth nonce/signature failure;
7. TruthGate block;
8. DMRF injection-defense block;
9. local object-store path rejection;
10. trace export/signature failure;
11. frontend API error boundary recovery;
12. packaging smoke failure.

Failures must be explicit, logged, and triageable. Do not silently return synthetic success for production paths.

---

## Reviewer verification path

A production reviewer should inspect these files in order:

1. `docs/diagrams/08_testing_validation_and_release_governance.md`
2. `docs/diagrams/12_end_to_end_request_lifecycle.md`
3. `docs/ARCHITECTURE.md`
4. `docs/DEPLOYMENT.md`
5. `docs/DATABASE_SCHEMA.md`
6. `docs/TESTING.md`
7. `docs/RELEASE_CHECKLIST.md`
8. `.github/workflows/ci.yml`
9. `.github/workflows/deploy.yml`
10. `.github/workflows/release-installer-signing.yml`
11. `scripts/runtime_precheck.py`
12. `scripts/verify_release_governance.py`
13. `scripts/verify_environment_parity.py`
14. `scripts/verify_lockfiles.py`
15. `scripts/validate_schema_parity.py`
16. `scripts/windows/run_packaging_smoke.ps1`
17. `scripts/windows/verify_nsis_governance.ps1`
18. `scripts/windows/verify_installer_signature.ps1`
19. `backend/security/desktop_local_auth.py`
20. `backend/security/export_integrity.py`
21. `backend/dmrf/orchestrator.py`
22. `backend/truth_engine/api.py`
23. `frontend/app/layout.tsx`
24. `frontend/components/layout/AppSidebar.tsx`

---

## Current release decision

For contest, architecture review, technical demonstration, and sponsor/employer review:

```text
Recommended status: Ready to present with caveats
```

For signed Windows production distribution:

```text
Recommended status: Not final until trusted signing credentials, signed artifact validation, and manual accessibility evidence are complete
```

For public cloud production:

```text
Recommended status: Conditional; requires cloud-specific security/storage approval and staging provider validation
```

---

## Change notes for v2.8.0

1. Updated document version to v2.8.0 and last-updated date to 2026-06-26.
2. v2.0 single-mode consolidation audit complete (A1–A32, all four phases): multi-user RBAC/MFA/SSO/OIDC/tenancy removed in favor of single-owner OS-level desktop auth + desktop auto-login; `OAuthAccount` table dropped (migration `d6e7f8a9b0c1`); dead modules and one-off scripts retired.
3. All Python and Node dependency vulnerabilities cleared (`pip-audit` + `npm audit` report no known advisories).
4. Documentation set (`docs/`, `docs/diagrams/`, root docs) reconciled to the current single-mode architecture; the duplicate `.github/README.md` was consolidated into a single canonical root `README.md`.
5. Windows desktop installer rebuilt and validated end-to-end 2026-06-26 (PyInstaller backend → Next.js static export → Electron/NSIS) with the freshly built backend embedded. Local validation: backend **1769 passed, 19 skipped**; frontend **378 passed**. (Test count is lower than v2.7.0's 1865 because the single-mode audit removed the multi-user auth/connector test suites along with those features.)
6. New open desktop-packaging item: the installer does not bundle a JRE for Neo4j (`databases/jre` source reported missing during electron-builder packaging) — confirm intended (external/system JRE) or add the bundle before signed distribution.
7. New open frontend item: dead `/login` + `/register` pages still ship despite single-mode backend auth removal — flagged for cleanup.

## Change notes for v2.7.0

1. Updated document version to v2.7.0 and last-updated date to 2026-06-08.
2. Sprint 5a–5f completed: chat interface deep audit and fix (rate-limit circuit-breaker cascade, Live Trace panel stability, API key encryption, frontend error handling). Test suite: **1865 passed, 21 skipped, 0 failed**.
3. Windows installer rebuilt and stamped 2026-06-08 14:08. LLM Gateway 429 rate-limit handling now returns directly to the client rather than silently queuing.
4. Failure-mode item "provider rate limiting" now has explicit, logged, user-visible handling (Sprint 5f).
5. Remaining release blocker: E2E chat verification on the 2026-06-08 installer with a configured provider key.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Reframed this guide as a production readiness scorecard rather than a chronological phase log.
3. Added target-specific readiness status for desktop, Windows VM, and web/cloud deployments.
4. Added current release blockers and signed Windows distribution requirements.
5. Added architecture, API, data, testing, security, accessibility, compliance, and failure-mode readiness sections.
6. Added reviewer verification path tied to actual workflows, scripts, and implementation files.
7. Preserved key readiness themes while removing long stale phase-history detail from the active guidance path.
