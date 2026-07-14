# Documentation Coverage Matrix

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.10.1 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Purpose

Track source-of-truth documents across all core DataLogicEngine areas and identify documentation ownership, status, and reviewer entry points.

This matrix covers active documentation only. Archived whitepapers, historical notes, research spikes, and old planning material are reference inputs, not operational source-of-truth.

---

## Coverage matrix

| Area | Source-of-truth document | Status | Notes |
|---|---|---|---|
| Product overview | `README.md`, `docs/PRODUCT_OVERVIEW.md` | Active | Entry point and product narrative. |
| Product design and UX | `docs/PRODUCT_DESIGN.md` | Active | UX thesis, routes, user journeys, trace-first product model. |
| End-user guide | `docs/USER_GUIDE.md` | Active | First-run and day-to-day workflows. |
| Engineer onboarding | `docs/ENGINEER_ONBOARDING.md` | Active | New engineer/reviewer onboarding path. |
| Architecture | `docs/ARCHITECTURE.md` | Active | System architecture and implementation model. |
| Architecture map | `docs/ARCHITECTURE_MAP.md` | Active | Runtime mode, trust boundaries, code-path mapping, doc map. |
| Data flow diagrams | `docs/DATA_FLOW_DIAGRAMS.md` | Active | Current DMRF/Truth Engine/data/privacy/export flows. |
| Decision logic | `docs/DECISION_LOGIC.md` | Active | Current decision points and implementation paths. |
| Workflow | `docs/WORKFLOW.md` | Active | Governed request lifecycle. |
| API contract | `docs/API.md`, `docs/openapi.yaml`, `docs/GATEWAY_COMPATIBILITY.md` | Active | Native/SDK/bounded-OpenAI contract, machine-readable surface, and checked v1 compatibility baseline. |
| API versioning | `docs/API_VERSIONING.md` | Active | Canonical `/api/v1/*`, compatibility aliases, deprecation policy. |
| Data/storage | `docs/DATABASE_SCHEMA.md` | Active | Multi-store data and memory architecture. |
| Security controls | `docs/SECURITY.md`, root `SECURITY.md` | Active | IAM, desktop auth, export integrity, AI security, release security. |
| Privacy/legal | `docs/PRIVACY_POLICY.md` | Active | Local-first privacy, provider/connector disclosure, export/delete. |
| HTTPS/TLS | `docs/SSL_CONFIGURATION.md` | Active | Web/cloud TLS and local desktop trust distinction. |
| CIS-style hardening | `docs/CIS_BENCHMARKS.md` | Active | Evidence-guided hardening map, not attestation. |
| Secure SDLC | `docs/SDLC_SSDF_MAPPING.md` | Active | NIST SSDF-style mapping. |
| AI management mapping | `docs/AI_MANAGEMENT_SYSTEM_42001.md` | Active | ISO/IEC 42001-style AIMS mapping, not certification claim. |
| Supply chain roadmap | `docs/SLSA_LEVEL_3_ATTESTATION.md` | Active / roadmap | Current-state/target-state supply-chain roadmap. |
| Testing standards | `docs/TESTING.md` | Active | Quality gates and validation architecture. |
| Deployment | `docs/DEPLOYMENT.md` | Active | Local Windows/same-host operation and explicitly gated private Windows profile. |
| Private gateway qualification | `docs/PRIVATE_GATEWAY_RUNBOOK.md` | Active gate | Disabled profile, TLS/certificate/firewall/two-machine acceptance and incident response. |
| Windows local operations | `docs/WINDOWS_11_LOCAL_RUNBOOK.md` | Active | Local-first Windows operation and packaging. |
| Operational runbooks | `docs/OPERATIONAL_RUNBOOKS.md` | Active | Incident response and operational recovery. |
| Release governance | `docs/RELEASE_CHECKLIST.md` | Active | Release evidence and approval controls. |
| Production readiness | `docs/PRODUCTION_READINESS.md` | Active | Readiness scorecard and production caveats. |
| File structure/inventory | `docs/FILE_STRUCTURE.md`, `docs/FILE_INVENTORY.csv`, `docs/GENERATED_STRUCTURE.md` | Active/generated | Repository map and generated inventory. |
| Documentation standards | `docs/DOCUMENTATION_STANDARDS.md` | Active | Documentation requirements and quality gates. |
| Documentation versioning | `docs/DOCUMENTATION_VERSIONING.md`, `docs/DOCS_VERSION.json` | Active | Docs version/lifecycle policy. |
| Production docs baseline | `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md` | Active | Baseline coverage and evidence rules. |
| Top-level markdown review | `docs/TOP_LEVEL_MARKDOWN_REVIEW_2026-07-06.md` | Active audit artifact | Direct top-level markdown review status and cleanup candidates before subfolder review. |
| Subfolder markdown review | `docs/SUBFOLDER_MARKDOWN_REVIEW_2026-07-06.md` | Active audit artifact | Direct `docs/` subfolder Markdown review status, updates, and cleanup candidates. |
| Root cleanup review | `docs/ROOT_CLEANUP_REVIEW_2026-07-06.md` | Active audit artifact | Root document/artifact cleanup status and cleanup candidates. |
| Audit-folder markdown review | `docs/audits/AUDITS_MARKDOWN_REVIEW_2026-07-06.md` | Active audit artifact | Audit-folder status, supersession notes, and approved deletion record. |
| Archive markdown review | `docs/archive/ARCHIVE_MARKDOWN_REVIEW_2026-07-06.md` | Historical/reference governance | Per-file archive catalog and cleanup candidates; not operational source-of-truth. |
| Branch governance | `docs/BRANCH_PROTECTION_POLICY.md` | Active | Required checks, review gates, branch policy. |
| Architecture decisions | `docs/adr/*` | Active/reference | Architecture decision records. |
| Contribution workflow | `CONTRIBUTING.md`, `docs/CONTRIBUTING.md` | Active | Contributor process and doc update policy. |
| Documentation archive | `docs/archive/*` | Historical/reference | Not operational source-of-truth. Use as input for future combined papers. |

---

## Maintenance rules

1. Add new active docs to this matrix.
2. Do not add archived exploratory docs as source-of-truth unless promoted to active docs.
3. Keep root `TODO.md` as the active backlog for doc follow-up work.
4. Update this matrix when product, architecture, security, release, or governance docs are added, renamed, or retired.
5. Keep document metadata consistent with `docs/DOCUMENTATION_VERSIONING.md`.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Expanded coverage to include DATA_FLOW_DIAGRAMS, DECISION_LOGIC, API_VERSIONING, SSL/TLS, CIS, SLSA roadmap, and production baseline docs.
3. Clarified archive/reference status.
4. Added maintenance rules.

## Change notes for v2.7.0

1. Documented that `docs/openapi.yaml` is the active machine-readable API reference and that stale duplicate exports were moved under `docs/archive/api/`.

## Change notes for v2.8.0

1. Added the 2026-07-06 top-level markdown review report as an active audit artifact.

## Change notes for v2.9.0

1. Updated the matrix version for the strict production top-level docs pass and `docs/DOCS_VERSION.json` refresh.

## Change notes for v2.10.0

1. Added subfolder, audit-folder, and archive Markdown review artifacts to the coverage matrix.
2. Clarified that archive review artifacts catalog historical files without promoting them to source-of-truth status.

## Change notes for v2.10.1

1. Added the root cleanup review artifact to the documentation coverage matrix.
