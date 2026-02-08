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
| API contract and usage | `docs/API.md`, `docs/openapi.yaml` | Active | Human + machine-readable API references |
| Security controls | `docs/SECURITY.md` | Active | IAM, encryption, audit, runtime controls |
| Compliance mapping | `docs/SDLC_SSDF_MAPPING.md`, `docs/AI_MANAGEMENT_SYSTEM_42001.md` | Active | SSDF and AI management alignment |
| Deployment operations | `docs/DEPLOYMENT.md` | Active | Cloud and desktop deployment procedures |
| Production readiness | `docs/PRODUCTION_READINESS.md` | Active | Readiness, reliability, scale, DR |
| Windows local operations | `docs/WINDOWS_11_LOCAL_RUNBOOK.md` | Active | Local bring-up and validation |
| Incident response runbooks | `docs/OPERATIONAL_RUNBOOKS.md` | Active | Security and operational incidents |
| Testing standards | `docs/TESTING.md` | Active | Quality gate execution standards |
| Developer onboarding | `docs/DEVELOPER_GUIDE.md` | Active | Local setup and development workflows |
| Contribution workflow | `docs/CONTRIBUTING.md` | Active | Branching, review, and doc update policy |
| Workflow reasoning model | `docs/WORKFLOW.md` | Active | High-level query pipeline workflow |
| Privacy/legal policy | `docs/PRIVACY_POLICY.md` | Active | User data handling and policy disclosure |
| Historical records | `docs/archive/*` | Archived | Not source-of-truth |
| Research whitepapers | `docs/whitepapers/*` | Reference | Not operational source-of-truth |

## Gaps and follow-up items

1. Add named owners per source document (team/role) in each file.
2. Add explicit review cadence to all active docs.
3. Consolidate any duplicate guidance that conflicts between root docs and `docs/`.

## Document control

1. Owner: Platform Engineering
2. Last updated: 2026-02-08
3. Status: Active
4. Review cadence: Every 30 days
