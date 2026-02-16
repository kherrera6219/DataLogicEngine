# Documentation Coverage Matrix

## Purpose

Track source-of-truth documents across all core application areas and identify documentation ownership/status.

## Coverage matrix

| Area | Source-of-truth document | Status | Notes |
|---|---|---|---|
| Product overview | `README.md`, `docs/PRODUCT_OVERVIEW.md` | Active | Root entry point plus explicit product narrative |
| Product design and UX | `docs/PRODUCT_DESIGN.md` | Active | Information architecture, interaction model, lazy-loading strategy |
| End-user operations guide | `docs/USER_GUIDE.md` | Active | Task-oriented usage and workflow guidance |
| Architecture and design | `docs/ARCHITECTURE.md` | Active | Logical and deployment architecture |
| Architecture implementation map | `docs/ARCHITECTURE_MAP.md` | Active | Runtime mode map, trust boundaries, code-path mapping |
| API contract and usage | `docs/API.md`, `docs/openapi.yaml` | Active | Human + machine-readable API references |
| Security controls | `docs/SECURITY.md` | Active | IAM, encryption, audit, runtime controls |
| Compliance mapping | `docs/SDLC_SSDF_MAPPING.md`, `docs/AI_MANAGEMENT_SYSTEM_42001.md` | Active | SSDF and AI management alignment |
| Deployment operations | `docs/DEPLOYMENT.md` | Active | Cloud and desktop deployment procedures |
| Production readiness | `docs/PRODUCTION_READINESS.md` | Active | Readiness, reliability, scale, DR |
| Windows local operations | `docs/WINDOWS_11_LOCAL_RUNBOOK.md` | Active | Local bring-up and validation |
| Incident response runbooks | `docs/OPERATIONAL_RUNBOOKS.md` | Active | Security and operational incidents |
| Testing standards | `docs/TESTING.md` | Active | Quality gate execution standards |
| Documentation versioning | `docs/DOCUMENTATION_VERSIONING.md`, `docs/DOCS_VERSION.json` | Active | Documentation lifecycle and semantic version metadata |
| Release governance | `docs/RELEASE_CHECKLIST.md` | Active | Release gate checklist and approval controls |
| Branch governance | `docs/BRANCH_PROTECTION_POLICY.md` | Active | Required checks, review gates, and code-owner policy |
| Architecture decisions | `docs/adr/*` | Active | Immutable architecture decision records |
| Developer onboarding | `docs/DEVELOPER_GUIDE.md` | Active | Local setup and development workflows |
| Contribution workflow | `docs/CONTRIBUTING.md` | Active | Branching, review, and doc update policy |
| Documentation standard baseline | `docs/DOCUMENTATION_STANDARDS.md`, `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md` | Active | Production documentation requirements with vendor alignment |
| File inventory and repository map | `docs/FILE_INVENTORY.csv`, `docs/GENERATED_STRUCTURE.md`, `docs/FILE_STRUCTURE.md` | Active | Generated inventory, structure map, and naming policy |
| Workflow reasoning model | `docs/WORKFLOW.md` | Active | High-level query pipeline workflow |
| Privacy/legal policy | `docs/PRIVACY_POLICY.md` | Active | User data handling and policy disclosure |
| Historical records | `docs/archive/*` | Archived | Not source-of-truth |
| Research whitepapers | `docs/whitepapers/*` | Reference | Not operational source-of-truth |

## Gaps and follow-up items

1. Keep generated inventory docs (`docs/FILE_INVENTORY.csv`, `docs/GENERATED_STRUCTURE.md`) refreshed after repository cleanup/refactors.
2. Continue consolidating any conflicting instructions between legacy `docs/archive/` files and active source-of-truth docs.
3. Expand CI docs enforcement to include markdown linting for active files.
4. Keep vendor guidance baseline (`docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`) reviewed at least monthly.

## Document control

1. Owner: Platform Engineering
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days
