# AI Production Documentation Baseline

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Platform Engineering + Documentation Governance |
| Review cadence | Every 30 days |

## Purpose

Define the production documentation baseline for DataLogicEngine as an AI governance, local-first, and knowledge-reasoning platform.

This baseline summarizes the current documentation set after modernization across architecture, API, security, privacy, testing, deployment, release, operations, product, engineering onboarding, ISO-style AI management mapping, SSDF mapping, and supply-chain roadmap documents.

This document is not a certification claim. It is a documentation control artifact that identifies source-of-truth documents, expected evidence, and remaining caveats.

## Audience

1. Engineering leadership
2. Security and compliance teams
3. Platform and release engineers
4. Documentation owners
5. Technical judges, sponsors, and enterprise reviewers

---

## Current product documentation posture

DataLogicEngine documentation now describes the platform as:

1. a local-first Windows/Electron application;
2. a controlled web/cloud-capable application where configured;
3. a governed AI lifecycle platform;
4. a DMRF control-plane implementation;
5. a Truth Engine v7.3 implementation;
6. a 17-axis routing and DSQP persona-construction system;
7. a trace/evidence/export review platform;
8. a multi-store data and memory architecture;
9. a release-governed desktop packaging and production readiness system.

The documentation no longer treats the product as a generic LLM chat wrapper or only as an early UKG concept.

---

## Source-of-truth documentation map

| Area | Source-of-truth documents | Status |
|---|---|---|
| Product overview | `docs/PRODUCT_OVERVIEW.md` | Updated to v2.6.0 |
| Product UX/design | `docs/PRODUCT_DESIGN.md` | Updated to v2.6.0 |
| User operation | `docs/USER_GUIDE.md` | Updated to v2.6.0 |
| Engineer onboarding | `docs/ENGINEER_ONBOARDING.md` | Updated to v2.6.0 |
| Architecture | `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_MAP.md`, `docs/diagrams/` | Updated to v2.6.0 |
| API | `docs/API.md`, `docs/API_VERSIONING.md`, `docs/openapi.yaml` | Updated to v2.6.0 where applicable |
| Workflow | `docs/WORKFLOW.md` | Updated to v2.6.0 |
| Data architecture | `docs/DATABASE_SCHEMA.md` | Updated to v2.6.0 |
| Security | `docs/SECURITY.md`, `SECURITY.md` | Updated to v2.6.0 where applicable |
| Privacy | `docs/PRIVACY_POLICY.md` | Updated to v2.6.0 |
| HTTPS/TLS | `docs/SSL_CONFIGURATION.md` | Updated to v2.6.0 |
| Testing | `docs/TESTING.md` | Updated to v2.6.0 |
| Deployment | `docs/DEPLOYMENT.md` | Updated to v2.6.0 |
| Windows local operations | `docs/WINDOWS_11_LOCAL_RUNBOOK.md` | Updated to v2.6.0 |
| Operations | `docs/OPERATIONAL_RUNBOOKS.md` | Updated to v2.6.0 |
| Release governance | `docs/RELEASE_CHECKLIST.md` | Updated to v2.6.0 |
| Production readiness | `docs/PRODUCTION_READINESS.md` | Updated to v2.6.0 |
| Secure SDLC | `docs/SDLC_SSDF_MAPPING.md` | Updated to v2.6.0 |
| AI management mapping | `docs/AI_MANAGEMENT_SYSTEM_42001.md` | Updated to v2.6.0 |
| Supply chain roadmap | `docs/SLSA_LEVEL_3_ATTESTATION.md` | Updated to v2.6.0 roadmap/current-state format |
| Documentation standards | `docs/DOCUMENTATION_STANDARDS.md`, `docs/DOCUMENTATION_VERSIONING.md`, `docs/DOCUMENTATION_COVERAGE_MATRIX.md` | Active governance references |

---

## Cross-vendor baseline expectations

Production AI platform documentation should cover:

1. clear setup and quickstart guidance;
2. product overview and user workflows;
3. architecture and request lifecycle;
4. API contract and versioning guidance;
5. security controls and vulnerability reporting;
6. privacy, data residency, export, and deletion behavior;
7. AI safety, governance, traceability, and limitations;
8. data architecture, storage, retention, and audit behavior;
9. testing and release gates;
10. operational runbooks and incident response;
11. supply-chain and artifact integrity guidance;
12. production readiness status and caveats.

DataLogicEngine now has active documentation coverage for each area.

---

## Baseline coverage matrix

| Baseline requirement | DataLogicEngine coverage | Evidence |
|---|---|---|
| Setup and local run | Implemented | `README.md`, `docs/DEVELOPER_GUIDE.md`, `docs/WINDOWS_11_LOCAL_RUNBOOK.md` |
| Product explanation | Implemented | `docs/PRODUCT_OVERVIEW.md`, `docs/PRODUCT_DESIGN.md`, `docs/USER_GUIDE.md` |
| Architecture | Implemented | `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_MAP.md`, `docs/diagrams/` |
| Request workflow | Implemented | `docs/WORKFLOW.md`, `docs/diagrams/12_end_to_end_request_lifecycle.md` |
| API documentation | Implemented | `docs/API.md`, `docs/API_VERSIONING.md`, `docs/openapi.yaml` |
| AI governance | Implemented through architecture/control docs | `docs/AI_MANAGEMENT_SYSTEM_42001.md`, `docs/SDLC_SSDF_MAPPING.md`, `docs/SECURITY.md` |
| Security | Implemented | `docs/SECURITY.md`, `SECURITY.md`, `tests/security/` |
| Privacy | Implemented | `docs/PRIVACY_POLICY.md`, privacy/settings routes |
| Data/storage | Implemented | `docs/DATABASE_SCHEMA.md`, `backend/storage/`, `backend/memory/` |
| Testing/quality | Implemented | `docs/TESTING.md`, `.github/workflows/ci.yml` |
| Deployment | Implemented | `docs/DEPLOYMENT.md`, deploy workflow |
| Local desktop operations | Implemented | `docs/WINDOWS_11_LOCAL_RUNBOOK.md`, `scripts/windows/` |
| Operations/incident response | Implemented | `docs/OPERATIONAL_RUNBOOKS.md`, support bundle script |
| Release readiness | Implemented | `docs/RELEASE_CHECKLIST.md`, `docs/PRODUCTION_READINESS.md` |
| Supply chain | Partial / roadmap | `docs/SLSA_LEVEL_3_ATTESTATION.md`, signing workflow, release checklist |
| Documentation governance | Implemented | docs standards/versioning/coverage matrix and docs validation script |

---

## Evidence-driven documentation rules

Documentation should follow these rules:

1. Do not claim certification unless certification evidence exists.
2. Do not claim SLSA Level 3, SBOM, Sigstore, Rekor, CodeQL, DAST, or similar controls unless workflow artifacts prove them.
3. Distinguish current implementation from target-state roadmap.
4. Treat archived whitepapers as exploratory unless an active source-of-truth document adopts the claim.
5. Update docs and diagrams when architecture changes.
6. Keep version/date metadata in active docs.
7. Avoid saying local-first means air-gapped.
8. Avoid saying desktop local-auth is valid for cloud/web trust boundaries.
9. Tie release claims to release checklist evidence.
10. Tie API claims to contract tests and current route behavior.

---

## Validation checklist

Run documentation and governance checks:

```powershell
python scripts/verify_docs_references.py
python scripts/generate_docs.py
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
python scripts/verify_release_governance.py
```

When docs reference schema/data behavior, also run:

```powershell
python scripts/validate_schema_parity.py
```

When docs reference Windows packaging/release behavior, also run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
```

---

## Production documentation caveats

Current caveats:

1. This document is a documentation baseline, not a certification or compliance attestation.
2. SLSA Level 3 remains a roadmap/current-state supply-chain document unless formal SLSA evidence is generated and verified.
3. Public Windows distribution still requires trusted signing credentials and signed artifact verification evidence.
4. Manual accessibility evidence remains required before final production distribution claims.
5. Provider-backed flows require configured provider credentials and network access.
6. Field-level encryption now writes AES-256-GCM payloads; legacy Fernet-encrypted values remain decryptable for backward compatibility.
7. Archived whitepapers may contain exploratory or historical architecture that is not current source of truth.

---

## Operating practices

1. Update active docs during the same change that modifies architecture, security, API, storage, deployment, or release behavior.
2. Regenerate documentation inventory/structure when repository structure changes.
3. Keep architecture diagrams synchronized with implementation.
4. Keep `docs/DOCS_VERSION.json` updated when required by release governance.
5. Keep release checklist evidence attached to tagged releases.
6. Move obsolete conceptual documents to archive or mark them as historical.
7. Use active docs as source of truth for judges, sponsors, enterprise reviewers, and new engineers.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Reframed the baseline around the current documentation modernization state.
3. Added source-of-truth documentation map and baseline coverage matrix.
4. Added evidence-driven documentation rules and caveats.
5. Added validation commands and operating practices.
