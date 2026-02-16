# DataLogicEngine Documentation Portal

## Purpose

Single entry point for active documentation and source-of-truth documents.

## Current Documentation Scope

1. Product and user documentation
2. Engineering and architecture documentation
3. Security, compliance, deployment, and operational runbooks
4. Windows local runtime and desktop packaging workflows

## Current App Status Snapshot (February 16, 2026)

1. Core app routes are operational in web and desktop modes.
2. Desktop mode supports no-login startup to internal dashboard.
3. API key save/test, AI model controls, and storage lifecycle controls are wired.
4. Sections 5-8 controls are fully implemented (Phase 1-3), and post-baseline hardening is also implemented: Postgres tenant RLS controls, production vault-backed secret enforcement paths, export signing/encryption + immutable audit replication, code-signing rotation/revocation governance drills, and AI/connector p95-p99 latency SLO gauges.
5. Section 9 testing controls now include enforced contract tests, local-mode parity tests, frontend typecheck gates, route E2E smoke, and Windows packaging smoke validation in CI.
6. Section 10 Windows desktop controls now include governed NSIS policy checks, controlled auto-update runtime gating, silent install/uninstall controls, secure desktop secret/log storage paths, and startup port conflict auto-resolution.
7. Section 11 governance controls now include repository pre-commit hooks, ADR baseline, environment parity and lockfile verification gates, release checklist workflow, and branch/code-owner policy docs.
8. Some settings/admin/MCP UX areas remain partial (see `docs/PRODUCT_OVERVIEW.md`).
9. Documentation governance now includes vendor-aligned AI production standards, architecture mapping, and deterministic repository inventory generation.

## Start Here

1. Product overview: `docs/PRODUCT_OVERVIEW.md`
2. User guide: `docs/USER_GUIDE.md`
3. Developer guide: `docs/DEVELOPER_GUIDE.md`
4. Windows local runbook: `docs/WINDOWS_11_LOCAL_RUNBOOK.md`
5. Architecture: `docs/ARCHITECTURE.md`
6. Architecture map: `docs/ARCHITECTURE_MAP.md`
7. API reference: `docs/API.md`
8. Security controls: `docs/SECURITY.md`
9. Deployment guide: `docs/DEPLOYMENT.md`
10. Testing standards: `docs/TESTING.md`
11. Operational runbooks: `docs/OPERATIONAL_RUNBOOKS.md`
12. Release checklist: `docs/RELEASE_CHECKLIST.md`
13. Branch protection policy: `docs/BRANCH_PROTECTION_POLICY.md`
14. Documentation versioning: `docs/DOCUMENTATION_VERSIONING.md`
15. AI documentation baseline: `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`
16. Architecture decision records: `docs/adr/README.md`

## Repository inventory and map artifacts

1. File inventory (generated): `docs/FILE_INVENTORY.csv`
2. Structure summary (generated): `docs/GENERATED_STRUCTURE.md`
3. File structure and naming policy: `docs/FILE_STRUCTURE.md`
4. Documentation coverage matrix: `docs/DOCUMENTATION_COVERAGE_MATRIX.md`

## Current assessments

1. `docs/APPLICATION_REVIEW_RECOMMENDED_IMPROVEMENTS_2026-02-10.md`
2. `docs/SUBSYSTEMS_SECTIONS_1_TO_4_UPDATED_REPORT_2026-02-16.md`
3. `docs/SUBSYSTEMS_SECTIONS_5_TO_8_REVIEW_2026-02-16.md`
4. `docs/SUBSYSTEMS_SECTIONS_9_TO_11_REVIEW_2026-02-16.md`

## Documentation Standards

1. `docs/DOCUMENTATION_STANDARDS.md`
2. `docs/DOCUMENTATION_COVERAGE_MATRIX.md`
3. `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`

## Active vs Historical

1. Active: documents referenced in this portal and coverage matrix.
2. Historical: `docs/archive/` (retained for traceability, not source-of-truth).
3. Reference research: `docs/whitepapers/` (informational, not operational runbooks).

## Document Control

1. Owner: Platform Engineering
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days
