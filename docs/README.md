# DataLogicEngine — Documentation Portal

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Overview

This portal is the authoritative entry point for active DataLogicEngine documentation.

DataLogicEngine is documented as a local-first governed AI platform with a Windows/Electron desktop runtime, Flask API/security envelope, DMRF control plane, Truth Engine, 17-axis routing, DSQP persona construction, trace/export review surfaces, MCP governance, and multi-store data/memory architecture.

Active documents listed here are the operational source of truth. Historical whitepapers, old release notes, wireframes, research spikes, and exploratory documents under `docs/archive/` are reference-only and should not be treated as implementation authority unless promoted into active documentation.

Current planning belongs in root `TODO.md`.

---

## Start here by role

| Role | Read first |
|---|---|
| New user / evaluator | `docs/PRODUCT_OVERVIEW.md`, `docs/USER_GUIDE.md` |
| New engineer | `docs/ENGINEER_ONBOARDING.md`, `docs/DEVELOPER_GUIDE.md` |
| Architect | `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_MAP.md`, `docs/DATA_FLOW_DIAGRAMS.md`, `docs/DECISION_LOGIC.md` |
| API integrator | `docs/API.md`, `docs/API_VERSIONING.md`, `docs/openapi.yaml` |
| Security reviewer | `docs/SECURITY.md`, `docs/PRIVACY_POLICY.md`, `docs/CIS_BENCHMARKS.md` |
| Operator / SRE | `docs/DEPLOYMENT.md`, `docs/OPERATIONAL_RUNBOOKS.md`, `docs/WINDOWS_11_LOCAL_RUNBOOK.md` |
| Release reviewer | `docs/RELEASE_CHECKLIST.md`, `docs/PRODUCTION_READINESS.md`, `docs/SLSA_LEVEL_3_ATTESTATION.md` |
| Documentation owner | `docs/DOCUMENTATION_STANDARDS.md`, `docs/DOCUMENTATION_VERSIONING.md`, `docs/DOCUMENTATION_COVERAGE_MATRIX.md` |

---

## Core source-of-truth documents

### Product

| Document | Purpose |
|---|---|
| `docs/PRODUCT_OVERVIEW.md` | Product narrative, capability map, deployment modes, reviewer path. |
| `docs/PRODUCT_DESIGN.md` | Product surface, UX model, trace-first workflow design. |
| `docs/USER_GUIDE.md` | End-user workflows and feature usage. |
| `docs/WINDOWS_11_LOCAL_RUNBOOK.md` | Windows local-first setup, operation, and troubleshooting. |

### Architecture and engineering

| Document | Purpose |
|---|---|
| `docs/ARCHITECTURE.md` | Current system architecture. |
| `docs/ARCHITECTURE_MAP.md` | Implementation-mapped architecture, trust boundaries, validation matrix. |
| `docs/WORKFLOW.md` | Governed request lifecycle. |
| `docs/DATA_FLOW_DIAGRAMS.md` | Data flows across DMRF, Truth Engine, storage, privacy, export, providers, MCP. |
| `docs/DECISION_LOGIC.md` | Major decision points and implementation paths. |
| `docs/DATABASE_SCHEMA.md` | Multi-store data and memory architecture. |
| `docs/FILE_STRUCTURE.md` | Repository structure and reviewer navigation. |
| `docs/ENGINEER_ONBOARDING.md` | Structured engineer onboarding path. |
| `docs/DEVELOPER_GUIDE.md` | Developer setup and daily workflow. |

### API and integration

| Document | Purpose |
|---|---|
| `docs/API.md` | API reference and security/auth behavior. |
| `docs/API_VERSIONING.md` | Canonical `/api/v1/*`, compatibility aliases, deprecation policy. |
| `docs/openapi.yaml` | Machine-readable API contract where applicable. |

### Security, privacy, and governance

| Document | Purpose |
|---|---|
| `SECURITY.md` | Vulnerability reporting policy. |
| `docs/SECURITY.md` | Security architecture and controls. |
| `docs/PRIVACY_POLICY.md` | Local-first privacy, provider/connector data movement, export/delete. |
| `docs/SSL_CONFIGURATION.md` | HTTPS/TLS guidance and local desktop trust distinction. |
| `docs/CIS_BENCHMARKS.md` | Evidence-guided CIS-style hardening map. |
| `docs/SDLC_SSDF_MAPPING.md` | Secure SDLC / SSDF-style mapping. |
| `docs/AI_MANAGEMENT_SYSTEM_42001.md` | AI management system mapping; not a certification claim. |
| `docs/SLSA_LEVEL_3_ATTESTATION.md` | Supply-chain current-state/target-state roadmap. |

### Testing, operations, and release

| Document | Purpose |
|---|---|
| `docs/TESTING.md` | Test architecture, quality gates, validation commands. |
| `docs/DEPLOYMENT.md` | Deployment modes and operational deployment guidance. |
| `docs/OPERATIONAL_RUNBOOKS.md` | Operational and incident runbooks. |
| `docs/RELEASE_CHECKLIST.md` | Release evidence and approval checklist. |
| `docs/PRODUCTION_READINESS.md` | Readiness scorecard, current caveats, release posture. |

### Documentation governance

| Document | Purpose |
|---|---|
| `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md` | Production documentation baseline and evidence rules. |
| `docs/DOCUMENTATION_COVERAGE_MATRIX.md` | Source-of-truth coverage map. |
| `docs/DOCUMENTATION_STANDARDS.md` | Documentation standards and quality gates. |
| `docs/DOCUMENTATION_VERSIONING.md` | Versioning and lifecycle policy. |
| `docs/DOCS_VERSION.json` | Documentation manifest where maintained. |
| `docs/CONTRIBUTING.md` | Documentation-specific contribution guide. |

---

## Diagram navigation

Current active architecture diagrams are maintained under `docs/diagrams/`.

Recommended read order:

1. `docs/diagrams/01_master_system_architecture.md`
2. `docs/diagrams/12_end_to_end_request_lifecycle.md`
3. `docs/diagrams/09_dmrf_control_plane_deep_dive.md`
4. `docs/diagrams/05_truth_engine_architecture.md`
5. `docs/diagrams/10_dsqp_persona_construction_architecture.md`
6. `docs/diagrams/07_data_storage_and_memory_architecture.md`
7. `docs/diagrams/06_local_first_security_model.md`
8. `docs/diagrams/08_testing_validation_and_release_governance.md`

Use `docs/ARCHITECTURE_MAP.md` as the master map for diagram purpose and reviewer navigation.

---

## Archive policy

`docs/archive/*` contains historical material. This can include early research, whitepapers, old release notes, wireframes, and prior planning documents.

Rules:

1. Archive material is reference-only.
2. Archive material must be validated against active docs and current code before reuse.
3. Archive material should be used as input to future combined papers, not as active implementation guidance.
4. Active source-of-truth docs must stay outside the archive.

---

## Validation

Documentation validation:

```powershell
python scripts/verify_docs_references.py
python scripts/generate_docs.py
```

Architecture/release-adjacent validation:

```powershell
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
python scripts/verify_release_governance.py
```

Schema/data validation when docs reference data behavior:

```powershell
python scripts/validate_schema_parity.py
```

---

## Current documentation posture

The active documentation set has been normalized around:

1. v2.6.0 document metadata;
2. local-first desktop and controlled web/cloud modes;
3. DMRF as the governed control plane;
4. Truth Engine as the policy/reasoning/memory layer;
5. 17-axis routing and DSQP persona construction;
6. trace, evidence, privacy, export, and release governance;
7. evidence-based security and compliance claims.

## Change notes for v2.6.0

1. Replaced older portal structure and stale capability counts with the current source-of-truth hierarchy.
2. Added explicit metadata, role-based navigation, active-doc classification, archive policy, and validation commands.
3. Aligned the portal with the updated architecture, security, API, operations, release, and documentation-governance documents.
