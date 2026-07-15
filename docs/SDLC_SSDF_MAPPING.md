# Secure SDLC: NIST SSDF Mapping

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.8.0 |
| Last updated | 2026-07-14 |
| Status | Active |
| Owner | Security Engineering + Release Engineering |
| Review cadence | Every 60 days |

## Purpose

Map DataLogicEngine secure-development practices to the NIST Secure Software Development Framework (SSDF) model.

This document is an internal alignment artifact, not a formal attestation. It identifies the implementation evidence that supports secure development, CI governance, release validation, supply-chain protection, AI control-plane safety, and vulnerability response.

## Audience

1. Security engineers
2. Platform engineers
3. Release engineers
4. Compliance/audit reviewers
5. Technical judges and enterprise evaluators

## Related documents

1. `docs/SECURITY.md`
2. `docs/TESTING.md`
3. `docs/PRODUCTION_READINESS.md`
4. `docs/DEPLOYMENT.md`
5. `docs/RELEASE_CHECKLIST.md`
6. `docs/OPERATIONAL_RUNBOOKS.md`
7. `docs/BRANCH_PROTECTION_POLICY.md`
8. `.github/workflows/ci.yml`
9. `.github/workflows/deploy.yml`
10. `.github/workflows/release-installer-signing.yml`

---

## SSDF alignment overview

| SSDF group | DataLogicEngine implementation theme |
|---|---|
| Prepare the Organization | documented owners, review cadence, secure architecture docs, release checklist, branch policy, CI governance. |
| Protect the Software | repository controls, lockfile governance, release signing, installer signature verification, artifact reports. |
| Produce Well-Secured Software | DMRF/TruthGate controls, secure API contracts, tests, schema parity, runtime precheck, frontend/backend validation. |
| Respond to Vulnerabilities | operational runbooks, support bundles, security regression tests, post-incident remediation, release blocking criteria. |

---

## 1. Prepare the Organization (PO)

| Practice | DataLogicEngine implementation | Evidence |
|---|---|---|
| PO.1 Define security requirements | Security, production readiness, testing, deployment, and runbook documents define security and release criteria. | `docs/SECURITY.md`, `docs/PRODUCTION_READINESS.md`, `docs/TESTING.md` |
| PO.2 Assign roles and responsibilities | Active docs include owner and review cadence metadata; single-mode OS-level auth defines the single owner (application RBAC removed). | document metadata, `frontend/app/admin/`, `backend/auth/api_decorators.py` |
| PO.3 Implement supporting toolchain | CI validates backend, frontend, contract, parity, security, packaging, governance, and Docker builds. | `.github/workflows/ci.yml` |
| PO.4 Define criteria for software security checks | Release gates include runtime precheck, schema parity, docs validation, tests, backend packaging, installer integrity, packaging smoke, lockfile governance. | `docs/RELEASE_CHECKLIST.md`, `docs/TESTING.md` |
| PO.5 Collect and share vulnerability information | Security/runbooks define escalation; support evidence requires preview, confirmation, allowlisting, re-redaction, hashes, and optional encryption. | `docs/SECURITY.md`, `docs/OPERATIONAL_RUNBOOKS.md`, `scripts/generate_support_bundle.py` |

---

## 2. Protect the Software (PS)

| Practice | DataLogicEngine implementation | Evidence |
|---|---|---|
| PS.1 Protect code from unauthorized access/tampering | Branch protection policy, CI required checks, controlled release workflow, repository governance. | `docs/BRANCH_PROTECTION_POLICY.md`, `.github/workflows/ci.yml` |
| PS.2 Provide mechanism to verify software release integrity | Windows installer signing workflow and signature verification scripts. | `.github/workflows/release-installer-signing.yml`, `scripts/windows/verify_installer_signature.ps1` |
| PS.3 Archive and protect releases | Release checklist and signing workflow require signed artifacts and report uploads. | `docs/RELEASE_CHECKLIST.md`, signing workflow artifacts |
| PS.4 Protect build pipeline inputs | Lockfile governance, environment parity, dependency audit, runtime precheck. | `scripts/verify_lockfiles.py`, `scripts/verify_environment_parity.py`, `scripts/runtime_precheck.py` |
| PS.5 Protect artifacts and evidence | Packaging smoke reports, signature reports, runtime/schema/environment reports, trace export integrity manifests. | `reports/`, `backend/security/export_integrity.py` |

---

## 3. Produce Well-Secured Software (PW)

| Practice | DataLogicEngine implementation | Evidence |
|---|---|---|
| PW.1 Design software to meet security requirements | Architecture includes API/security envelope, DMRF, TruthGate, local-first security, data protection, export integrity. | `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, diagrams |
| PW.2 Review software design for security | Security reviewer paths identify implementation files and tests for desktop auth, TruthGate, injection defense, export integrity. | `docs/SECURITY.md`, `docs/diagrams/06_local_first_security_model.md` |
| PW.4 Reuse well-secured software | Uses standard frameworks/libraries for Flask, SQLAlchemy, Next.js, pytest, Playwright, ChromaDB, Neo4j, Windows DPAPI helper where applicable. | dependency files, code modules |
| PW.5 Configure build process securely | CI performs deterministic installs, lockfile verification, lint/test gates, frontend build, backend packaging, installer integrity, packaging smoke, Docker build. | `.github/workflows/ci.yml` |
| PW.6 Produce secure executable artifacts | Electron/NSIS packaging path includes backend rebuild, governance, installer integrity, and smoke tests; production path includes signing and signature verification. | `scripts/build_backend.py`, `scripts/verify_installer_integrity.py`, `scripts/windows/verify_nsis_governance.ps1`, `scripts/windows/run_packaging_smoke.ps1` |
| PW.7 Review/test code for security | Security/contract/parity/route tests, runtime precheck, redaction canaries, typed-error and exception/import regression gates. | `tests/security/`, `tests/contract/`, `tests/parity/`, `scripts/check_exception_boundaries.py`, `scripts/check_circular_deps.py` |
| PW.8 Configure software to have secure settings by default | Production blocks unsafe `AUTO_CREATE_SCHEMA`; `SESSION_SECRET` is required; canonical auth errors are JSON-native; cloud mode cannot rely on desktop auth. | `app.py`, `scripts/runtime_precheck.py`, `docs/API.md` |
| PW.9 Protect data at rest and in transit | HTTPS/cloud guardrails, CSRF/CORS/trusted hosts, desktop DPAPI helper, encryption manager, export integrity. | `backend/security/`, `docs/SECURITY.md` |

---

## 4. Respond to Vulnerabilities (RV)

| Practice | DataLogicEngine implementation | Evidence |
|---|---|---|
| RV.1 Identify and confirm vulnerabilities | Security tests, audit logs, metrics, TruthMemory, support bundles, operational incident triggers. | `tests/security/`, `/metrics`, `docs/OPERATIONAL_RUNBOOKS.md` |
| RV.2 Assess, prioritize, and remediate vulnerabilities | Severity model in runbooks, production readiness blockers, release gates, incident postmortems. | `docs/OPERATIONAL_RUNBOOKS.md`, `docs/PRODUCTION_READINESS.md` |
| RV.3 Analyze root causes | Failure triage protocol requires defect classification, regression test additions, post-incident report. | `docs/TESTING.md`, `docs/OPERATIONAL_RUNBOOKS.md` |
| RV.4 Report vulnerability status | Release checklist, incident records, support bundles, CI reports, signed release reports. | `docs/RELEASE_CHECKLIST.md`, `reports/` |

### Phase 13 operational-security evidence

1. Correlated backend/Electron `dle.log.v1` and authenticated Diagnostics keep
   local failure evidence content-free and external telemetry disabled by
   default.
2. Support export is explicit, previewed, confirmed, allowlisted, re-redacted,
   hashed, retained, and optionally encrypted.
3. Typed failure categories and critical fail semantics prevent missing policy,
   persistence, corruption, provider/tool, timeout, or cancellation state from
   becoming synthetic success.
4. Compliance framework outputs are evidence maps/self-assessments rather than
   certification claims.
5. Stress24/idle72 evaluators and incident runbooks define installed acceptance;
   the full-duration installed evidence remains open.

---

## DataLogicEngine-specific secure SDLC enhancements

### AI control-plane security

DataLogicEngine adds AI-specific controls beyond normal application SDLC checks:

1. DMRF `InjectionDefense` blocks prompt injection, logical traps, obfuscation, persona hijack, and resource-exhaustion patterns.
2. TruthGate evaluates security, budget, compliance, priority, trust, and PII markers.
3. TierClassifier routes high-risk requests to deeper workflows.
4. Axis 15 and Axis 16 model risk/threat and ethics/trust/criticality.
5. Axis 17 maps tier to FROST depth and TruthCore mode.
6. EvidenceModel and ConvergencePolicy apply freshness and confidence controls.
7. Trace Explorer exposes evidence, claims, personas, policy decisions, and memory events.

### Local-first desktop security

1. Desktop loopback auth uses per-install secret, nonce challenge, HMAC signatures, timestamp skew checks, and constant-time comparison.
2. DPAPI helper protects local secrets where available.
3. Desktop auth is not valid as a public cloud trust boundary.
4. Packaging smoke, installer integrity, installer-mode smoke, and NSIS governance validate installer behavior.
5. Trusted Windows signing workflow validates production release artifacts.

### Multi-store data security

1. SQL schema parity validation prevents uncontrolled drift.
2. Object store rejects null bytes, absolute paths, traversal, and containment violations.
3. ChromaDB uses local persistent path behavior.
4. USKD graph and UnifiedMemory persistence are local-first by default.
5. TruthMemory supports audit/explainability artifacts.
6. Export integrity protects trace bundles with hashes, optional HMAC signatures, and optional encryption.

---

## Evidence register

| Evidence | Location |
|---|---|
| Secure architecture | `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/diagrams/` |
| CI controls | `.github/workflows/ci.yml` |
| Deploy controls | `.github/workflows/deploy.yml` |
| Release signing controls | `.github/workflows/release-installer-signing.yml` |
| Runtime precheck | `scripts/runtime_precheck.py` |
| Lockfile governance | `scripts/verify_lockfiles.py` |
| Environment parity | `scripts/verify_environment_parity.py` |
| Schema parity | `scripts/validate_schema_parity.py` |
| Docs validation | `scripts/verify_docs_references.py` |
| Installer integrity | `scripts/verify_installer_integrity.py` |
| Packaging smoke | `scripts/windows/run_packaging_smoke.ps1` |
| NSIS governance | `scripts/windows/verify_nsis_governance.ps1` |
| Security tests | `tests/security/` |
| Contract tests | `tests/contract/` |
| Parity tests | `tests/parity/` |
| AI security controls | `backend/dmrf/`, `backend/truth_engine/` |
| Export integrity | `backend/security/export_integrity.py` |
| Incident response | `docs/OPERATIONAL_RUNBOOKS.md` |
| Phase 13 operations evidence | `reports/production-readiness/2026/phase-13/` |

---

## Known gaps and caveats

1. This document is an internal mapping, not a formal NIST SSDF attestation.
2. Verify actual CI scanners before claiming specific tools such as CodeQL, Bandit, Safety, SAST, DAST, SBOM, or Sigstore/cosign. Current evidence should be tied to workflow files, not assumptions.
3. Production Windows distribution still requires trusted signing credentials and signed artifact validation.
4. Manual accessibility evidence is still required for production release signoff.
5. Field-level encryption is implemented with AES-256-GCM for new payloads, with legacy `Fernet-AES-128-CBC` entries kept decryptable for backward compatibility; active docs describe AES-256-GCM as implemented, not target-state.
6. Phase 13 source gates do not replace installed failure-injection, all-output
   redaction/no-egress, support, and 24/72-hour soak evidence.

---

## Reviewer verification path

A secure-SDLC reviewer should inspect:

1. `.github/workflows/ci.yml`
2. `.github/workflows/deploy.yml`
3. `.github/workflows/release-installer-signing.yml`
4. `docs/SECURITY.md`
5. `docs/TESTING.md`
6. `docs/PRODUCTION_READINESS.md`
7. `docs/RELEASE_CHECKLIST.md`
8. `docs/OPERATIONAL_RUNBOOKS.md`
9. `scripts/runtime_precheck.py`
10. `scripts/verify_lockfiles.py`
11. `scripts/verify_environment_parity.py`
12. `scripts/validate_schema_parity.py`
13. `scripts/build_backend.py`
14. `scripts/verify_installer_integrity.py`
15. `scripts/windows/run_packaging_smoke.ps1`
16. `scripts/windows/verify_nsis_governance.ps1`
17. `backend/dmrf/injection_defense.py`
18. `backend/truth_engine/truth_gate/gateway.py`
19. `backend/security/export_integrity.py`
20. `tests/security/`
21. `tests/contract/`
22. `tests/parity/`

---

## Change notes for v2.8.0

1. Added the Phase 13 correlation, Diagnostics/support, redaction, typed-failure,
   exception/import regression, incident, and soak evidence mapping.

## Change notes for v2.7.0

1. Added backend packaging, installer integrity, and installer-mode smoke to SSDF-style release evidence and reviewer paths.
2. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Reframed the document as an internal NIST SSDF alignment artifact, not an attestation.
3. Updated SSDF mapping to match actual CI, governance, runtime precheck, schema parity, packaging, signing, and release evidence.
4. Added DataLogicEngine-specific AI control-plane, local-first desktop, and multi-store data security enhancements.
5. Added evidence register, known caveats, and reviewer verification path.
6. Removed overclaims about unverified tools and replaced them with evidence-driven workflow references.
