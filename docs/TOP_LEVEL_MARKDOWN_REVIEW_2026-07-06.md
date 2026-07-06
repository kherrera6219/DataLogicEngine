# Top-Level Markdown Review - 2026-07-06

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.1.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Documentation Governance |
| Review cadence | Per documentation audit slice |

## Scope

This review covers Markdown files directly under the top-level `docs/` folder.

The original requested scope was 41 Markdown files. The current top-level scope is 42 Markdown files because this review report was added during the pass and then reviewed as part of the final strict sweep.

This pass does not review Markdown files under `docs/adr/`, `docs/audits/`, `docs/archive/`, `docs/diagrams/`, `docs/documents/`, `docs/ip/`, `docs/whitepapers/`, or `docs/wireframes/`. Those subfolders should be reviewed in later passes.

## Review method

1. Listed every direct `docs/*.md` file and line count.
2. Read every top-level Markdown file in scope, including generated/pointer documents.
3. Reconciled high-risk claims against the live tree where needed, including auth decorators, MCP route files, frontend login/register redirect stubs, and generated repository structure.
4. Searched for stale provider, release, installer, API, auth, OAuth, tenant/role, and archive-policy references.
5. Updated confirmed stale docs and refreshed stale metadata on active source-of-truth documents.
6. Updated `docs/DOCS_VERSION.json`, `docs/README.md`, and `docs/DOCUMENTATION_COVERAGE_MATRIX.md` so the manifest and portal reflect the strict pass.

## Files updated in this pass

| Document | Update summary |
|---|---|
| `docs/AI_MANAGEMENT_SYSTEM_42001.md` | Refreshed metadata and added installer integrity/backend packaging evidence to AI management controls. |
| `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md` | Refreshed source-of-truth map and packaging evidence commands. |
| `docs/API.md` | Removed stale OAuth/JWT wording and aligned API auth/MCP guidance to session, signed desktop, and `ukg_...` API-key principals. |
| `docs/API_VERSIONING.md` | Refreshed metadata after confirming the versioning policy remains current. |
| `docs/ARCHITECTURE.md` | Refreshed metadata and release-validation wording. |
| `docs/ARCHITECTURE_MAP.md` | Added backend bundle, installer integrity, and installer-mode smoke checks to the validation matrix. |
| `docs/AUTH_DECORATORS.md` | Aligned accepted auth modes to `backend/auth/api_decorators.py`. |
| `docs/BRANCH_PROTECTION_POLICY.md` | Updated representative protected-check guidance for installer integrity, deploy/build, and security-scan checks where configured. |
| `docs/CIS_BENCHMARKS.md` | Added installer integrity and installer-mode smoke verification commands. |
| `docs/COMPONENT_MAP.md` | Added backend packaging and installer integrity to the ops/release component description. |
| `docs/CONTRIBUTING.md` | Refreshed metadata after confirming contribution policy remains current. |
| `docs/DATABASE_SCHEMA.md` | Removed stale OAuth-account sensitive-field wording and clarified vestigial tenant columns. |
| `docs/DATA_FLOW_DIAGRAMS.md` | Replaced stale tenant/user MCP-scope wording with authenticated-principal/local-profile checks. |
| `docs/DECISION_LOGIC.md` | Expanded desktop release decision criteria to include backend rebuild, installer integrity, and installer-mode smoke. |
| `docs/DEPLOYMENT.md` | Added release-candidate verification commands and checklist entries for installer integrity/install-mode smoke. |
| `docs/DOCUMENTATION_COVERAGE_MATRIX.md` | Updated matrix version for the strict pass and review-report linkage. |
| `docs/DOCUMENTATION_STANDARDS.md` | Added installer integrity/install-mode smoke quality gates and backend-before-Electron documentation rule. |
| `docs/DOCUMENTATION_VERSIONING.md` | Refreshed metadata after updating `docs/DOCS_VERSION.json`. |
| `docs/ENGINEER_ONBOARDING.md` | Added NSIS governance and portable smoke to the desktop packaging onboarding sequence. |
| `docs/FILE_STRUCTURE.md` | Added `scripts/generate_docs.py` to the file-structure validation path. |
| `docs/MCP_INTEGRATION.md` | Removed remaining OAuth/future-work wording and replaced generic support contact with runbook escalation. |
| `docs/OPERATIONAL_RUNBOOKS.md` | Expanded packaging incident handling and replaced stale MCP OAuth/role wording. |
| `docs/PRIVACY_POLICY.md` | Replaced OAuth-scope wording with API-token/connector credential/scope language. |
| `docs/PROCESS_MAP.md` | Updated release process flow for backend rebuild, installer integrity, and installer-mode smoke. |
| `docs/PRODUCT_DESIGN.md` | Replaced stale role-gated UX wording with single-owner/runtime language. |
| `docs/PRODUCTION_READINESS.md` | Added full installer evidence chain and corrected `/login`/`/register` redirect-stub wording. |
| `docs/README.md` | Updated portal version and change notes for the strict top-level docs pass. |
| `docs/SDLC_SSDF_MAPPING.md` | Added backend packaging, installer integrity, and installer-mode smoke to SSDF-style evidence. |
| `docs/SECURITY.md` | Removed stale MCP OAuth-token lifecycle wording and added installer evidence requirements. |
| `docs/SEQUENCE_DIAGRAMS.md` | Updated privacy auth wording and release validation sequence. |
| `docs/SLSA_LEVEL_3_ATTESTATION.md` | Added NSIS governance to the supply-chain reviewer path. |
| `docs/SSL_CONFIGURATION.md` | Replaced OAuth redirect wording with provider/connector callback safety language. |
| `docs/TESTING.md` | Added installer integrity/install-mode smoke to required release gates and reviewer path. |
| `docs/USER_GUIDE.md` | Removed stale local/offline-provider wording and clarified OpenAI/Google provider choices. |

## Files reviewed with no manual content edit

| Document | Disposition | Reason |
|---|---|---|
| `docs/DEVELOPER_GUIDE.md` | Reviewed, no further edit | Already contained current provider and packaging workflow guidance. |
| `docs/GENERATED_STRUCTURE.md` | Reviewed, regenerated artifact | Generated by `scripts/generate_docs.py`; do not hand-edit. |
| `docs/PRODUCT_OVERVIEW.md` | Reviewed, no further edit | Already reflected July 2026 rebuild evidence and product posture. |
| `docs/RELEASE_CHECKLIST.md` | Reviewed, no further edit | Already contained backend-before-Electron, installer integrity, and installer-mode smoke gates. |
| `docs/REPO_AUDIT_LOG.md` | Reviewed, cleanup candidate | Pointer-only file; root `REPO_AUDIT_LOG.md` is canonical. |
| `docs/WINDOWS_11_LOCAL_RUNBOOK.md` | Reviewed, no further edit | Already contained July 2026 rebuild, installer integrity, and install/uninstall smoke evidence. |
| `docs/WORKFLOW.md` | Reviewed, metadata refresh only | Workflow model remains current. |

## Cleanup candidates

| Candidate | Recommendation | Reason |
|---|---|---|
| `docs/REPO_AUDIT_LOG.md` | Delete after link check, or keep only if a pointer is intentionally required for old doc links. | It duplicates the root audit-log name and only points to root `REPO_AUDIT_LOG.md`. |
| `docs/AUTH_DECORATORS.md` | Keep through production hardening; consider merging into `docs/SECURITY.md` or `docs/API.md` after route-auth cleanup stabilizes. | It is narrow but useful while auth-route policy is still a review focus. |
| `docs/ARCHITECTURE_MAP.md`, `docs/COMPONENT_MAP.md`, `docs/FILE_STRUCTURE.md` | Keep for now; reassess after subfolder review. | These overlap as reviewer navigation maps but currently serve different entry points. |
| `docs/SEQUENCE_DIAGRAMS.md` and `docs/diagrams/*` | Keep top-level overview until the diagram subfolder pass is complete. | There is likely overlap, but subfolder diagrams need a separate review before consolidation. |
| `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md` and `docs/DOCUMENTATION_COVERAGE_MATRIX.md` | Keep both for now. | The baseline is an evidence/control artifact; the matrix is a source-of-truth map. |
| `docs/GENERATED_STRUCTURE.md` and `docs/FILE_INVENTORY.csv` | Keep generated, do not manually edit. | They are generated reviewer artifacts maintained by `scripts/generate_docs.py`. |

## Follow-up for subfolder pass

1. Review `docs/audits/` separately; several audit plans are historical and may belong in archive.
2. Review `docs/adr/` for metadata consistency and duplicate-heading warnings.
3. Review `docs/diagrams/` against the current local-first desktop/provider/MCP model.
4. Review `docs/archive/` for archive hygiene only, not current implementation truth.
5. Review `docs/whitepapers/`, `docs/wireframes/`, and `docs/documents/` as cleanup/archive-only areas.
