# DataLogicEngine — Documentation Portal

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.30.0 |
| Last updated | 2026-07-14 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Overview

This portal is the authoritative entry point for active DataLogicEngine documentation.

DataLogicEngine is documented as local-first governed LLM middleware whose primary integration surface is a versioned same-host/private API gateway. Its Windows/Electron frontend is the production control, configuration, administration, audit, observability, support, and validation application, with a built-in reference chat client. The platform also includes a Flask API/security envelope, DMRF control plane, Truth Engine, 17-axis routing, DSQP persona construction, trace/export review surfaces, MCP governance, and multi-store data/memory architecture.

Active documents listed here are the operational source of truth. Historical whitepapers, old release notes, wireframes, research spikes, and exploratory documents under `docs/archive/` are reference-only and should not be treated as implementation authority unless promoted into active documentation.

Current implementation status belongs in root `TODO.md`. The active phased
production program is root `PRODUCTION_COMPLETION_PLAN_2026.md`.

The current execution checkpoint is Phase 15 release-candidate engineering
complete, with Phase 16 controlled-document replacement active. Product 4.3.0
has one version and lock authority; candidate and production release modes are
separate; the 299,129,416-byte local candidate passes integrity and payload
checks; and its 6,151-file backend contains no forbidden source/test/cache or
stale Electron-test payload. The first drifted build is retained only as negative
evidence.

Two independent GitHub candidate builds completed with matching file counts but
different backend, portable, and installer hashes. Reproducibility remains a
release gate; the comparison is not treated as a pass.

The candidate is unsigned and its packaged backend correctly refuses production
startup when protected-volume readiness cannot be proved. The signed installer,
installed lifecycle/update/Windows and five-service/provider matrices, final
supply-chain dossier, publisher/distribution authority, accessibility/manual
acceptance, pilot, and 24/72-hour soaks remain open. ADR-0009 keeps the truthful
Session Library model; ADR-0008's installed MCP acceptance remains deferred.
Production/public release remains **NO-GO**.

SeaweedFS is a qualification-only candidate under Proposed ADR-0004 and has not
replaced MinIO in the production architecture.

That program now contains 19 phases (0-18). Phases 8-11 productize the external
gateway, knowledge, simulation, and MCP connector contracts. Phase 16 replaces the accumulated
documentation with a 30-or-fewer controlled hand-maintained production set plus
generated contracts/evidence and a professional/Microsoft review dossier; Phase
17 performs final authority consolidation and release lock. Documents listed
below remain transitional authorities only until the Phase 16 old-to-new
crosswalk records their merge, generated replacement, archive, or deletion.

The Phase 16 inventory is generated from `config/documentation-authority.json`:
all 151 root and documentation-tree Markdown files have one owner-approved
disposition, and the selected canonical set is exactly 30 hand-maintained
documents (27 existing, three planned). All 27 existing canonical documents pass
the controlled-header verifier. See `docs/DOCUMENTATION_BOM.md` and
`docs/DOCUMENTATION_CROSSWALK.md`. CP16-A and the CP16-B content checkpoint are
complete; CP16-C content construction is complete with signed/manual/independent
evidence retained, and CP16-D/CP16-E external-review content is active. The
approval authorizes no archive or deletion until target content and links pass.

---

## Start here by role

| Role | Read first |
|---|---|
| New user / evaluator | root `README.md`, `docs/PRODUCT_REQUIREMENTS.md`, `docs/INSTALLATION_GUIDE.md`, `docs/USER_GUIDE.md` |
| New engineer | `docs/SOFTWARE_LIFECYCLE_PLAN.md`, `docs/DEVELOPER_GUIDE.md`, `docs/ARCHITECTURE.md` |
| Production completion owner | `docs/audits/DataLogicEngine_Design_vs_Implementation_Audit_2026-07-12.md`, root `PRODUCTION_COMPLETION_PLAN_2026.md`, root `TODO.md`, root `HANDOFF.md` |
| Architect | `docs/ARCHITECTURE.md`, `docs/DATA_ARCHITECTURE.md`, `docs/INTERFACE_INTEGRATION.md`, `docs/SECURITY_ARCHITECTURE.md` |
| API integrator | `docs/INTERFACE_INTEGRATION.md`, `docs/openapi.yaml` |
| Security reviewer | root `SECURITY.md`, `docs/SECURITY_ARCHITECTURE.md`, `docs/PRIVACY_AI_NOTICE.md` |
| AI/privacy/accessibility assurance | `docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md`, `docs/PRIVACY_IMPACT_ASSESSMENT.md`, `docs/ACCESSIBILITY_CONFORMANCE_REPORT.md` |
| Operator / SRE | `docs/INSTALLATION_GUIDE.md`, `docs/ADMINISTRATOR_OPERATIONS_GUIDE.md`, `docs/TROUBLESHOOTING_SUPPORT_GUIDE.md` |
| Release reviewer | `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/VERIFICATION_VALIDATION_REPORT.md`, `docs/THIRD_PARTY_SOFTWARE_INDEX.md`, `docs/RELEASE_READINESS_RECORD.md` |
| Documentation owner | `docs/DOCUMENTATION_STANDARDS.md`, `docs/DOCUMENTATION_VERSIONING.md`, `docs/DOCUMENTATION_COVERAGE_MATRIX.md` |

---

## Canonical documents and transitional source inputs

### Product

| Document | Purpose |
|---|---|
| `docs/PRODUCT_REQUIREMENTS.md` | Canonical product boundary, requirements, exclusions, acceptance evidence, and release status. |
| `docs/USER_GUIDE.md` | End-user workflows and feature usage. |
| `docs/INSTALLATION_GUIDE.md` | Canonical Windows installation, repair, upgrade, rollback, update, and uninstall lifecycle. |
| `docs/ADMINISTRATOR_OPERATIONS_GUIDE.md` | Canonical owner/operator service, backup, recovery, gateway, connector, diagnostics, and incident controls. |
| `docs/TROUBLESHOOTING_SUPPORT_GUIDE.md` | Canonical safe troubleshooting, evidence collection, and support channels. |
| `docs/PRIVACY_AI_NOTICE.md` | Canonical local-first data, provider/connector, retention/deletion, telemetry, and AI-limitations notice. |
| `docs/PRODUCT_OVERVIEW.md`, `docs/PRODUCT_DESIGN.md`, `docs/WINDOWS_11_LOCAL_RUNBOOK.md` | Transitional inputs retained until CP16-F link/content verification and archive approval. |

### Architecture and engineering

| Document | Purpose |
|---|---|
| `docs/ARCHITECTURE.md` | Current system architecture. |
| `docs/DATA_ARCHITECTURE.md` | Canonical stores, schemas, classification, migration, protection, retention, backup/restore, deletion, and integrity specification. |
| `docs/INTERFACE_INTEGRATION.md` | Canonical API, authentication, versioning, gateway/SDK, streaming/jobs, and MCP integration contract. |
| `docs/SECURITY_ARCHITECTURE.md` | Canonical trust boundaries, protected assets, threat/control map, release trust, and assurance status. |
| `docs/SOFTWARE_LIFECYCLE_PLAN.md` | Canonical requirements-to-release, configuration management, V&V, documentation, maintenance, and retirement lifecycle. |
| `docs/MAINTENANCE_DISASTER_RECOVERY.md` | Canonical maintenance, coordinated backup, isolated restore, rollback, disaster, and recovery acceptance plan. |
| `docs/ARCHITECTURE_MAP.md` | Implementation-mapped architecture, trust boundaries, validation matrix. |
| `docs/WORKFLOW.md` | Governed request lifecycle. |
| `docs/diagrams/12_end_to_end_request_lifecycle.md` | Canonical `governed.v1` causal lifecycle, failure behavior, and trace boundary. |
| `docs/DATA_FLOW_DIAGRAMS.md` | Data flows across DMRF, Truth Engine, storage, privacy, export, providers, MCP. |
| `docs/DECISION_LOGIC.md` | Major decision points and implementation paths. |
| `docs/DATABASE_SCHEMA.md` | Multi-store data and memory architecture. |
| `docs/KNOWLEDGE_ALGORITHM_CATALOG.md` | Production classification, guarantees, limitations, and enablement policy for all registered KAs. |
| `docs/MIGRATION_SUPPORT_MATRIX.md` | Per-store versions, startup migration policy, and supported-upgrade status. |
| `docs/DATA_CLASSIFICATION_REGISTER.md` | Sensitivity, location, protection, and retention register. |
| `docs/DATA_AT_REST_AND_KEY_MANAGEMENT.md` | Protected-volume, DPAPI, portable-backup, and key-recovery standard. |
| `docs/FILE_STRUCTURE.md` | Repository structure and reviewer navigation. |
| `docs/ENGINEER_ONBOARDING.md` | Structured engineer onboarding path. |
| `docs/DEVELOPER_GUIDE.md` | Developer setup and daily workflow. |

### API and integration

| Document | Purpose |
|---|---|
| `docs/INTERFACE_INTEGRATION.md` | Canonical client/API integration and compatibility authority. |
| `docs/API.md` | API reference and security/auth behavior. |
| `docs/GATEWAY_COMPATIBILITY.md` | Native/SDK/OpenAI compatibility, streaming, durable-job, and qualification matrix. |
| `docs/API_VERSIONING.md` | Canonical `/api/v1/*`, compatibility aliases, deprecation policy. |
| `docs/openapi.yaml` | Machine-readable API contract where applicable. |
| `docs/PRIVATE_GATEWAY_RUNBOOK.md` | Transitional input merged into the canonical administrator/operations guide; retained pending CP16-F evidence/link review. |

### Security, privacy, and governance

| Document | Purpose |
|---|---|
| `SECURITY.md` | Vulnerability reporting policy. |
| `docs/SECURITY_ARCHITECTURE.md` | Canonical security architecture, threat model, trust boundaries, controls, residual risks, and assurance state. |
| `docs/SECURITY.md` | Security architecture and controls. |
| `docs/PRIVACY_AI_NOTICE.md` | Canonical local-first privacy, provider/connector data movement, retention/deletion, telemetry, and AI limitations. |
| `docs/PRIVACY_POLICY.md` | Transitional source retained pending CP16-F legal/content/link review. |
| `docs/SSL_CONFIGURATION.md` | HTTPS/TLS guidance and local desktop trust distinction. |
| `docs/CIS_BENCHMARKS.md` | Evidence-guided CIS-style hardening map. |
| `docs/SDLC_SSDF_MAPPING.md` | Secure SDLC / SSDF-style mapping. |
| `docs/AI_MANAGEMENT_SYSTEM_42001.md` | AI management system mapping; not a certification claim. |
| `docs/SLSA_LEVEL_3_ATTESTATION.md` | Supply-chain current-state/target-state roadmap. |

### Testing, operations, and release

| Document | Purpose |
|---|---|
| `docs/REQUIREMENTS_TRACEABILITY.md` | Canonical requirement-to-implementation/test/evidence/release-disposition matrix. |
| `docs/VERIFICATION_VALIDATION_REPORT.md` | Canonical V&V levels, current evidence, retained installed/manual gates, and release decision. |
| `docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md` | Canonical KA classification/invariants, DSQP/TruthCore/evidence, evaluation, and human-review dossier. |
| `docs/PRIVACY_IMPACT_ASSESSMENT.md` | Canonical data inventory, privacy flows/risks/controls, and required deployment/legal approvals. |
| `docs/ACCESSIBILITY_CONFORMANCE_REPORT.md` | Canonical automated evidence, manual protocol, findings, and truthful non-conformance status. |
| `docs/THIRD_PARTY_SOFTWARE_INDEX.md` | Canonical dependency/service/SBOM/license/notices/redistribution index and open legal gate. |
| `docs/RELEASE_READINESS_RECORD.md` | Canonical candidate identity, gate status, final evidence bundle, and go-no-go decision. |
| `docs/TESTING.md` | Test architecture, quality gates, validation commands. |
| `docs/ADMINISTRATOR_OPERATIONS_GUIDE.md` | Canonical deployment operations, service lifecycle, backup/recovery, gateway, connector, diagnostics, and incidents. |
| `docs/DEPLOYMENT.md`, `docs/OPERATIONAL_RUNBOOKS.md` | Transitional sources retained pending CP16-F evidence/link review. |
| `docs/RELEASE_CHECKLIST.md` | Release evidence and approval checklist. |
| `docs/PRODUCTION_READINESS.md` | Readiness scorecard, current caveats, release posture. |
| `docs/evaluation/QUALITY_EVALUATION.md` | Versioned Phase 6 corpus, metrics, thresholds, and provider/model evaluation contract. |
| `docs/evaluation/HUMAN_REVIEW_RUBRIC.md` | Blinded human-review and disagreement-resolution procedure. |
| `docs/evaluation/AI_SYSTEM_CARD.md` | Intended use, dependencies, evaluation limits, oversight, and known failure modes. |
| `docs/PROVIDER_MODEL_SUPPORT.md` | Generated authoritative provider/model support view. |
| `docs/PROVIDER_COST_QUOTA_POLICY.md` | Phase 7 provider call, token, retry, warning, unknown-price, and spend policy. |
| `docs/LOCAL_USAGE_LEDGER_CONTRACT.md` | Content-free local provider usage/egress ledger and owner-control contract. |
| `PRODUCTION_COMPLETION_PLAN_2026.md` (repository root) | Canonical 19-phase program for completing the local-first Windows governed LLM middleware/API gateway, production desktop control/administration/audit/validation application, full app-owned PostgreSQL/Redis/Neo4j/ChromaDB/MinIO data plane, qualification, production-documentation replacement, professional/Microsoft review dossier, consolidation, and signed release. |
| `docs/audits/DataLogicEngine_Audit_Slice_Findings_Report_2026-07-06.md` | Consolidated findings and corrections for the documentation audit slice and code audit slices 1-12. |
| `docs/audits/DataLogicEngine_Chat_Data_Path_QC_2026-07-10.md` | Packaged enhanced-chat, DMRF/DSQP, provider-routing, persistence, and Trace Explorer QC. |
| `docs/audits/DataLogicEngine_Cross_System_Data_Path_QC_2026-07-10.md` | Cross-system frontend/backend/store review, corrections, residual risks, and rebuilt-app acceptance sequence. |
| `docs/audits/DataLogicEngine_Design_vs_Implementation_Audit_2026-07-12.md` | Repository-wide production audit comparing the active product/architecture design with the implemented backend, governed chat path, desktop runtime, storage, frontend, packaging, and test evidence. |
| `reports/ci_repair_2026-07-11.md` | Root-cause analysis and validation for the dependency-resolution and Windows packaging CI repair. |
| `reports/code_scanning_alerts_2026-07-08.md` | CodeQL exception-disclosure source analysis, remediation, and regression evidence. |
| `reports/production-readiness/2026/phase-05/summary.md` | Phase 5 contract, causality, single-path, trace-truth, validation, risk, and deferred installed-proof evidence. |
| `reports/production-readiness/2026/phase-06/summary.md` | Phase 6 evidence, confidence, convergence, TruthCore, KA, and evaluation checkpoint evidence. |
| `reports/production-readiness/2026/phase-07/summary.md` | Phase 7 provider ownership, deadline/cancellation, budget, privacy ledger, replay, validation, and deferred live-provider evidence. |

### Documentation governance

| Document | Purpose |
|---|---|
| `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md` | Production documentation baseline and evidence rules. |
| `docs/DOCUMENTATION_COVERAGE_MATRIX.md` | Source-of-truth coverage map. |
| `docs/DOCUMENTATION_STANDARDS.md` | Documentation standards and quality gates. |
| `docs/DOCUMENTATION_VERSIONING.md` | Versioning and lifecycle policy. |
| `docs/DOCS_VERSION.json` | Documentation manifest where maintained. |
| `docs/CONTRIBUTING.md` | Documentation-specific contribution guide. |
| `docs/TOP_LEVEL_MARKDOWN_REVIEW_2026-07-06.md` | Review status, updates, and cleanup candidates for direct top-level markdown files under `docs/`. |
| `docs/SUBFOLDER_MARKDOWN_REVIEW_2026-07-06.md` | Review status, updates, and cleanup candidates for Markdown files under direct `docs/` subfolders. |
| `docs/ROOT_CLEANUP_REVIEW_2026-07-06.md` | Root document/artifact cleanup review and source-control cleanup decisions. |
| `docs/audits/AUDITS_MARKDOWN_REVIEW_2026-07-06.md` | Audit-folder Markdown review status and supersession cleanup notes. |

---

## Diagram navigation

Current active architecture diagrams are maintained under `docs/diagrams/`.

Recommended read order:

1. `docs/ARCHITECTURE_MAP.md`
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

The current archive Markdown catalog is `docs/archive/ARCHIVE_MARKDOWN_REVIEW_2026-07-06.md`.
Completed audit and remediation plans are indexed under
`docs/archive/audits/README.md`. Root `PRODUCTION_COMPLETION_PLAN_2026.md` is the
sole active execution plan.
Superseded root handoff and backlog snapshots are indexed under
`docs/archive/session-history/README.md` and are historical only.

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

1. active document metadata and current-state routing guidance;
2. local-first desktop and controlled web/cloud modes;
3. `governed.v1` and one backend-owned causal orchestrator;
4. DMRF/TruthGate, bounded retrieval, deterministic DSQP, and TruthCore/KA
   preflight as participants in that path;
5. exact executed-stage traces and stable result/failure identity;
6. Phase 6 separation between trace presence and evidence/confidence validity;
7. evidence-based security and compliance claims;
8. desktop-first source build, installer, install-smoke, and uninstall-smoke guidance.

## Change notes for v2.24.0

1. Advanced the active checkpoint to Phase 14 and indexed the completed Phase
   13 structured observability, Diagnostics/support, failure-semantics,
   compliance-truth, and soak-evaluator engineering evidence.
2. Preserved all installed Phase 13 acceptance work as open release gates and
   updated the automated route baseline to 28 axe-clean routes.

## Change notes for v2.20.0

1. Advanced the active checkpoint to Phase 8 and indexed the Phase 7 provider
   manifest, cost/quota policy, local usage-ledger contract, and evidence.
2. Preserved CP7-F as installed live-provider evidence rather than treating
   deterministic provider fixtures as production acceptance.

## Change notes for v2.18.0

1. Advanced the active documentation checkpoint to Phase 6 and indexed the
   Phase 5 evidence and canonical lifecycle diagram.
2. Replaced parallel control-plane wording with the implemented `governed.v1`
   ownership and explicit evidence-validity boundary.

## Change notes for v2.14.2

1. Recorded the 2026-07-06 whitepaper reorganization: active whitepaper assets remain indexed under `docs/whitepapers/`, and historical/reference whitepapers are consolidated under `docs/archive/whitepapers/`.

## Change notes for v2.14.1

1. Added the root cleanup review report covering root documents, tracked root artifacts, ignored local outputs, and future cleanup candidates.

## Change notes for v2.14.0

1. Added the docs subfolder Markdown review report and linked audit/archive review artifacts from the active portal.
2. Refreshed ADR, diagram, folder-index, IP-disclosure, and archive-index metadata for the 2026-07-06 production documentation pass.
3. Recorded the approved deletion of the superseded audit v1 plan. The completed
   v2 first-pass audit plan was later archived on 2026-07-12 when root
   `PRODUCTION_COMPLETION_PLAN_2026.md` became the sole active execution plan.

## Change notes for v2.13.0

1. Linked the production top-level Markdown review report into the active portal.
2. Updated the portal version after the 2026-07-06 strict top-level docs pass refreshed stale metadata, MCP/OAuth wording, login/register redirect-stub wording, and installer evidence gates.

## Change notes for v2.12.0

1. Added `docs/TOP_LEVEL_MARKDOWN_REVIEW_2026-07-06.md` as an active documentation-governance artifact for direct top-level Markdown files under `docs/`.

## Change notes for v2.11.0

1. **GitHub README and desktop documentation refresh.** Reframed the public README around the current local-first Windows desktop application, made the PyInstaller-backend-before-Electron-installer rebuild order explicit, documented install/uninstall packaging smoke evidence, and kept signed-production caveats separate from local desktop readiness.
2. Updated the active portal routing so evaluators start from the root README/product overview and operators start from the Windows local runbook before broader deployment docs.

## Change notes for v2.10.0

1. **Documentation audit refresh.** Aligned active docs and `docs/openapi.yaml` to the live model defaults (OpenAI `gpt-5.5`, Google `gemini-3.1-pro-preview`) and single-owner desktop auth surface. Retired stale duplicate API exports into `docs/archive/api/`; approved root scratch-output `.txt` files were removed as non-source artifacts.

## Change notes for v2.9.0

1. **LLM layer simplified to a single cloud model.** The 6-tier local-Ollama escalation engine was removed; the app now uses one user-selected cloud model (OpenAI `gpt-5.5` or Google `gemini-3.1-pro-preview`), so reasoning requires a cloud API key + internet (data still stays local). Reframed `docs/ARCHITECTURE.md`, `docs/COMPONENT_MAP.md`, `docs/API.md`, `docs/USER_GUIDE.md`, `docs/DEVELOPER_GUIDE.md`, `docs/ENGINEER_ONBOARDING.md`, `docs/OPERATIONAL_RUNBOOKS.md`, `docs/FILE_STRUCTURE.md`, and `docs/diagrams/12_end_to_end_request_lifecycle.md` to "local-first data + cloud BYOK"; removed the obsolete local-model-acceleration guide. (Supersedes the 6-tier escalation additions recorded under v2.7.0 below.)

## Change notes for v2.7.0

1. Updated `docs/ARCHITECTURE.md` (v2.8.0) with a new "6-tier local-to-cloud model escalation" subsection covering T0–T5 tier chain, cloud escalation gate, OllamaProvider, and thinking-model constraint.
2. Updated `docs/REPO_AUDIT_LOG.md` (v3.2.0) with Sprint 6a–6c session block.
3. Updated `docs/COMPONENT_MAP.md` (v2.7.0) LLM Gateway description to reference the 6-tier escalation chain.
4. Updated `docs/API.md` with `escalation_tier`/`escalation_reason`/`escalation_label` fields in the `/chat` 200 response.
5. Added Ollama local-provider guidance to `docs/USER_GUIDE.md`, `docs/DEVELOPER_GUIDE.md`, and `docs/ENGINEER_ONBOARDING.md`.
6. Updated `sdk/UKG_Python_SDK/README.md` with OllamaProvider in the provider list and a quick-start code example.
7. Updated `.github/README.md` with the local Ollama/6-tier chain in the capability table, architecture diagram, and completed items.

## Change notes for v2.6.0

1. Replaced older portal structure and stale capability counts with the current source-of-truth hierarchy.
2. Added explicit metadata, role-based navigation, active-doc classification, archive policy, and validation commands.
3. Aligned the portal with the updated architecture, security, API, operations, release, and documentation-governance documents.
