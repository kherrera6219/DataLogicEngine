# Production Readiness Guide

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.17.0 |
| Last updated | 2026-07-14 |
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

Current status: **Phase 15 release-candidate engineering is complete and Phase
16 controlled-document replacement is active, but signed production release
remains NO-GO until retained installed, security, provider, recovery,
accessibility, soak, signing, legal, pilot, and independent-review evidence is
complete.**

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
10. Windows backend rebuild, installer integrity, packaging smoke, installer-mode install/uninstall smoke, and NSIS governance checks.
11. Privacy controls, cloud/AI disclosures, local-first product copy, and admin/compliance surfaces.
12. Frontend accessibility automation path and visual/E2E testing path.
13. First-run QC evidence covering local backend/service/database connectivity, desktop API-key save/test CSRF repair, removal of idle DSQP provider polling, and a rebuilt local installer with integrity/NSIS governance passing.
14. Versioned `dle-gateway.v1` native sync, governed SSE, durable async,
    idempotency, owned trace, capabilities, stable errors, and bounded
    OpenAI-compatible contracts.
15. Explicit client scopes and copy-once key lifecycle, Redis atomic admission,
    PostgreSQL virtual-model/job/idempotency authority, encrypted object-backed
    large results, split Client Gateway administration, SDKs, and contract-diff CI.
16. Secure app-owned source acquisition, durable ingestion authorities,
    PostgreSQL/Neo4j/Chroma/S3 corpus reconciliation, causal retrieval,
    UnifiedMemory v2 trust/lifecycle controls, and truthful Knowledge/Graph UI.
17. One `dle-simulation.v1` authority with exact call/token/tool/time/cost
    budgets, durable lifecycle records, verified restart checkpoints, required
    S3 artifacts, evidence-aware validation, and truthful Simulation UI.
18. One MCP `2025-11-25` local-stdio connector boundary with exact fingerprint/
    scope consent, DPAPI credentials, durable PostgreSQL authority, content-free
    Redis live state, governed object-backed results, cancellation, Windows Job
    Object containment, hostile fixtures, and truthful owner controls.
19. Validated correlation, shared backend/Electron `dle.log.v1`, explicit
    telemetry opt-in, authenticated Diagnostics, previewed/confirmed/hashed
    support bundles, typed failure semantics, evidence-backed compliance
    outputs, and stress24/idle72 evaluators.
20. Product 4.3.0 authority, hashed Python release lock, exact Node/Electron
    inputs, versioned Windows artifacts, immutable workflow references,
    fail-closed signing/update/distribution policy, SBOM/content inventory/
    release-manifest/attestation gates, and legacy installer exclusion.
21. Candidate/production workflow separation, a clean 299,129,416-byte unsigned
    qualification installer, zero payload-leakage findings across the 6,151-file
    backend, and a packaged-runtime probe that fails closed when protected-volume
    readiness cannot be proved.
22. Two same-commit GitHub candidate builds complete successfully with matching
    file counts; their differing normalized hashes truthfully retain the byte-
    reproducibility gate.

### Remaining release blockers before signed production distribution

1. Manual NVDA or equivalent assistive-technology evidence for accessibility release signoff.
2. Provisioned trusted production signing credentials.
3. Signed release artifact validation.
4. Final provider-configured staging run for gateway-backed query/simulation paths.
5. Reinstall validation of the rebuilt desktop installer with real OpenAI/Google provider save/test flows.
6. Final release checklist completion with generated reports attached.
7. Confirmation that no production build uses default secrets, `AUTO_CREATE_SCHEMA=true`, or desktop-only trust in cloud mode.
8. Phase 8 installed same-host/private Windows, TLS/firewall/certificate,
   two-machine, real OpenAI/Google, expanded backup/restore/restart/deletion,
   packaged UI, failure/load/soak, and privacy/security acceptance.
9. Closure or explicit time-bounded owner disposition of Dependabot alert 389
   after a reviewed patched ChromaDB release and adversarial qualification.
10. Phase 9 installed restart/recovery, populated-store parity, hostile-corpus,
    causal-answer, deletion, and packaged Knowledge/Graph acceptance.
11. Phase 10 installed live-provider budget, restart/cancellation, Redis event,
    PostgreSQL/S3/Neo4j/Chroma reconciliation, artifact, result-validity, and
    packaged Simulation UI acceptance.
12. Phase 11 rebuilt-installed file/network containment, lifecycle/reboot,
    PostgreSQL/Redis/object backup/restore, hostile connector, and Electron
    add/discover/call/cancel/stop/restart/remove acceptance.
13. Phase 12 installed handler-to-store workflow reconciliation, packaged
    visual/scaling/high-contrast checks, and manual NVDA acceptance.
14. Phase 13 installed multi-process/store correlation reconstruction, complete
    failure injection, all-output redaction/no-egress proof, Diagnostics/support
    acceptance, and full 24-hour stress plus 72-hour idle/normal-use soaks.
15. Phase 14 canonical rebuilt/signed installer, two-build repeatability, full
    install/repair/0.1.1-upgrade/rollback/uninstall/Windows matrix, approved
    publisher/signing boundary, adversarial signed updates, final SBOM/provenance/
    AV/license evidence, ten legal/authority actions, approved notices, and full
    legacy reachability proof.
16. Phase 15 CP15-A through CP15-H signed clean lifecycle/Windows matrix,
    five-service/provider functionality, fault recovery, performance/24/72-hour
    soak, security/privacy, accessibility/document walkthrough, two-machine
    human pilot, and gateway interoperability against one exact RC artifact.

Keep tactical task tracking in `TODO.md`; keep this guide focused on release criteria and validation controls.

---

## Production readiness scorecard

| Domain | Status | Required evidence |
|---|---|---|
| Architecture | Ready for review | `docs/ARCHITECTURE.md`, diagram set, DMRF/Truth Engine files. |
| API contract | Engineering checkpoint complete | `dle-gateway.v1`, OpenAPI compatibility diff, native/compatible contract tests, SDK and examples parity. |
| Security | Ready with release caveats | Security tests, runtime precheck, desktop auth tests, secret validation, signing evidence. |
| Data/storage | Phase 11 engineering checkpoint complete | 86 PostgreSQL entities, 31 logical contracts, nine object buckets, migration head `e0f1a2b3c4d5`; installed populated reconciliation remains gated. |
| Testing | Strong | Phase 13 baseline: 2,135 backend passed/18 skipped, 419 frontend passed, 28 axe-clean routes, and 10/10 browser readiness workflows. |
| Frontend/product | Phase 13 source workflows complete; installed proof remains | Gateway, ingestion, Graph, memory, Simulation, MCP, Session Library, Diagnostics, support, and accessibility contracts are tested. |
| Desktop packaging | Strong but signing-dependent | backend rebuild, NSIS governance, installer integrity, packaging smoke, installer-mode install/uninstall smoke, signed artifact verification. |
| Accessibility | Automated path present; manual evidence pending | Playwright/a11y sweep plus manual screen-reader evidence. |
| Observability | Phase 13 engineering checkpoint complete | Validated correlation, `dle.log.v1`, `/health`, `/live`, `/ready`, `/metrics`, authenticated Diagnostics/support, trace review; installed reconstruction/soaks pending. |
| Private gateway | Disabled pending qualification | Loopback is the default; TLS/mTLS, firewall, certificate, client policy, real providers, and two-machine acceptance must pass before enablement. |

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
10. PyInstaller backend rebuild completes before Electron/NSIS packaging for desktop release.
11. Windows packaging smoke passes for desktop release.
12. NSIS governance passes for installer release.
13. Installer integrity verification passes for generated root installer artifacts.
14. Installer-mode install/uninstall smoke passes where release scope requires install behavior evidence.
15. Docker build verification passes where applicable.
16. Release governance verifier passes.
17. No default secrets are present in production config.
18. `AUTO_CREATE_SCHEMA=true` is not enabled in production.
19. Production cloud mode does not rely on desktop loopback auth.
20. Trace export integrity path is verified.
21. Health/readiness/metrics endpoints are verified in target runtime.

### Required before signed Windows production distribution

1. Release trust policy authorizes production signing and distribution.
2. Approved publisher subject and protected managed/hardware signing boundary exist.
3. Signing certificate health, rotation, revocation, and incident ownership pass.
4. Installer and all applicable app-owned executable payloads are signed.
5. Signature chain, timestamp, publisher, hash, and revocation verification pass.
6. Final installer/service/JRE SBOM and content inventories are complete.
7. GitHub artifact/SBOM attestations are generated and verified.
8. Signed installer, reports, notices, scans, and approvals are archived together.
9. Packaging and installed lifecycle run against the exact signed artifact.
10. No local certificate or normal-runner exportable PFX is accepted as evidence.

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
5. backend package build evidence;
6. installer integrity report;
7. packaging smoke report;
8. installer-mode install/uninstall smoke report where scoped;
9. NSIS governance report;
10. release checklist evidence;
11. accessibility report/evidence;
12. signed artifact verification report for production distribution.

---

## Deployment architecture

Production readiness must be evaluated by target.

| Target | Readiness requirements |
|---|---|
| Windows desktop | local stack, Electron shell, backend loopback service, desktop local auth, internal storage, backend rebuild, installer integrity, packaging smoke, install/uninstall smoke, signing. |
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
14. backend desktop bundle rebuild before Electron/NSIS packaging;
15. Windows packaging smoke;
16. installer integrity verification;
17. installer-mode install/uninstall smoke where scoped;
18. NSIS governance;
19. environment parity;
20. lockfile governance;
21. release governance verifier;
22. Docker build verification where applicable.

See `docs/TESTING.md` for commands and quality baseline.

---

## Production code-signing path

The Release Installer Signing workflow is gated engineering scaffolding; it is
not yet the approved production signing boundary. Production authorization
requires config/release-trust-policy.json to name the approved publisher subject,
managed service or hardware-protected credential boundary, signing owner,
rotation/revocation process, protected environment, and distribution authority.

Required final workflow path:

1. Build the clean tagged version-consistent installer from locked inputs.
2. Generate integrity reports, final SBOMs, notices, and release manifest.
3. Sign the installer and every applicable app-owned executable with SHA-256 and
   a trusted timestamp inside the approved signing boundary.
4. Verify publisher, chain, timestamp, hash, and revocation for all binaries.
5. Generate GitHub provenance and SBOM attestations.
6. Verify the attestations before promotion.
7. Archive artifacts, hashes, signatures, SBOMs, attestations, scans, notices,
   installed qualification, and approval together.

Local development certificates and an exportable PFX on a normal hosted runner
are not production release evidence.

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
9. every pass/fail status includes claim type, check version, execution time,
   scope, result, source record, and evidence reference;
10. framework maps and application self-checks never imply independent audit,
    attestation, legal conclusion, or certification; missing evidence is Not
    measured.

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
12. installer integrity or packaging smoke failure.
13. installer-mode install/uninstall smoke failure.
14. disk exhaustion and bounded log/support retention;
15. memory, handle, thread, and child-process growth;
16. support-bundle redaction/hash/encryption failure;
17. unexpected telemetry or diagnostic egress;
18. cancellation, timeout, persistence, corruption, and partial deletion.

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

## Change notes for v2.17.0

1. Recorded the Phase 15 release-candidate engineering checkpoint, clean payload
   and integrity evidence, candidate/production authority separation, and the
   protected-volume fail-closed runtime result while retaining CP15-A through
   CP15-H as signed/installed/manual release gates.

## Change notes for v2.15.0

1. Recorded the Phase 13 structured observability, Diagnostics/support,
   compliance-evidence, error-semantics, runbook, and soak engineering checkpoint
   while retaining every installed acceptance gate.

## Change notes for v2.13.0

1. Recorded the Phase 10 simulation engineering checkpoint, updated validation
   baselines and data authority counts, and retained installed simulation gates.

## Change notes for v2.10.0

1. Made backend rebuild, installer integrity verification, and installer-mode install/uninstall smoke first-class production-readiness evidence throughout the checklist, reports, deployment target, testing gates, and failure-mode sections.
2. Corrected the `/login` and `/register` source-tree wording: the tracked Next.js pages are redirect stubs under `frontend/app/(auth)/`, not absent pages.

## Change notes for v2.9.2

1. Documented the July 2026 local rebuild lock-in: backend package, Electron/NSIS installer, installer integrity, NSIS governance, portable packaging smoke, installer-mode install/uninstall smoke, Deploy workflow, Security Scan, and CI/CD Pipeline passed on `main`.
2. Kept the release decision unchanged for public signed distribution: trusted code-signing credentials, signed artifact verification, and manual accessibility evidence remain required.

## Change notes for v2.9.1

1. Updated document version to v2.9.1 and last-updated date to 2026-07-06.
2. Remediated selected CodeQL reflected-output and exception-disclosure alerts in KA, search, MCP, and trace export routes by replacing reflected/raw exception responses with stable public errors and server-side exception logging.
3. Confirmed the stale `/login` and `/register` frontend-page cleanup item is resolved by redirect stubs under `frontend/app/(auth)/login/page.tsx` and `frontend/app/(auth)/register/page.tsx`; both redirect to `/dashboard` in the local-first desktop shell.

## Change notes for v2.9.0

1. Updated document version to v2.9.0 and last-updated date to 2026-06-27; the 2026-07-04 documentation audit refreshed model-provider wording without changing the readiness decision.
2. **LLM layer simplified to a single cloud model.** Removed the 6-tier
   local-Ollama escalation engine and the `backend/local_model_acceleration/`
   subsystem; the app now uses one user-selected cloud model (OpenAI `gpt-5.5`
   or Google `gemini-3.1-pro-preview`).
3. **Readiness impact:** reasoning now requires a cloud API key + internet — the
   app is no longer air-gapped/offline-capable for inference (data still stays
   local). Any "offline LLM / air-gapped" acceptance criteria no longer apply;
   provider-backed staging validation is now a baseline requirement, not just a
   pre-release gate.

## Change notes for v2.8.0

1. Updated document version to v2.8.0 and last-updated date to 2026-06-26.
2. v2.0 single-mode consolidation audit complete (A1–A32, all four phases): multi-user RBAC/MFA/SSO/OIDC/tenancy removed in favor of single-owner OS-level desktop auth + desktop auto-login; `OAuthAccount` table dropped (migration `d6e7f8a9b0c1`); dead modules and one-off scripts retired.
3. All Python and Node dependency vulnerabilities cleared (`pip-audit` + `npm audit` report no known advisories).
4. Documentation set (`docs/`, `docs/diagrams/`, root docs) reconciled to the current single-mode architecture; the duplicate `.github/README.md` was consolidated into a single canonical root `README.md`.
5. Windows desktop installer rebuilt and validated end-to-end 2026-06-26 (PyInstaller backend → Next.js static export → Electron/NSIS) with the freshly built backend embedded. Local validation: backend **1769 passed, 19 skipped**; frontend **378 passed**. (Test count is lower than v2.7.0's 1865 because the single-mode audit removed the multi-user auth/connector test suites along with those features.)
6. ~~New open desktop-packaging item: the installer does not bundle a JRE for Neo4j (`databases/jre` source reported missing during electron-builder packaging)~~ — **Resolved**: JRE bundling removed from `electron-builder.yml`; the backend's `_find_java_home()` discovers system-installed JREs (Temurin, Corretto, etc.) automatically, saving ~180 MB in installer size.
7. ~~New open frontend item: dead `/login` + `/register` pages still ship despite single-mode backend auth removal — flagged for cleanup.~~ — **Resolved**: the tracked `frontend/app/(auth)/login/page.tsx` and `frontend/app/(auth)/register/page.tsx` pages are disabled-by-design redirect stubs that immediately send users to `/dashboard`.

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
