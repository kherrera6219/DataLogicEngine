# Archive Markdown Review - 2026-07-06

> **Document metadata**
> - Document version: v1.0.0
> - Last reviewed: 2026-07-06
> - Status: Active archive review report
> - Owner: Documentation Governance
> - Scope: `docs/archive/**/*.md` historical/reference material.

## Review Method

This pass reviewed the 26 pre-existing Markdown files under `docs/archive/` by folder, title, line count, archive status, and targeted scans for stale production-risk terms such as SSO, Azure AD, React Native, Kubernetes, multi-tenant, active/current, and production-ready.

Archive documents were cataloged rather than rewritten in place. This preserves historical research value while preventing archived plans from being mistaken for the current production source of truth.

## Archive Policy Decision

- No archived file was promoted back into active documentation in this pass.
- No archived file was deleted in this pass.
- Active source of truth remains `docs/README.md`, root `docs/*.md`, `docs/adr/`, `docs/diagrams/`, `docs/audits/`, generated inventory files, and `TODO.md`.
- Historical implementation claims must be checked against code and active docs before they are used in production planning.

## Cleanup Candidates

| Candidate | Finding | Recommended action |
|---|---|---|
| `docs/archive/markdowns/complete_verification_checklist.md` and `docs/archive/markdowns/complete_verification_checklist (1).md` | Same title, different hashes, short file appears truncated compared with the 228-line copy. | Compare the two files and keep the more complete version, or rename the short copy as a fragment before deleting anything. |
| `docs/archive/research/K8S_OPERATOR_DESIGN.md` | Kubernetes operator planning for a v3.0 cluster strategy, outside current local-first desktop production scope. | Keep archived; do not link from active release docs unless Kubernetes work is reopened. |
| `docs/archive/research/REACT_NATIVE_RESEARCH.md` | React Native/mobile-axis plan, outside current desktop production scope. | Keep archived; do not treat as an active roadmap item unless mobile scope is explicitly reopened. |
| `docs/archive/wireframes/login-auth-2025.md` | Historical SSO/Azure AD/Okta login design conflicts with current single-owner desktop auth posture. | Keep archived only; active auth docs should point to desktop local auth and auth-deprecation docs. |
| `docs/archive/markdowns/56_Architecture_Decision_Records_ADRs.md` | Historical ADR bundle superseded by active `docs/adr/` decisions. | Keep archived; do not use as current ADR source of truth. |
| `docs/archive/whitepapers/UKG_Workflow_Architecture.md` | Very large research/architecture transcript with dated as-of/current statements and speculative cloud/multi-tenant sections. | Preserve as research archive; cite active docs for production behavior. |

## Reviewed Markdown Catalog

| File | Lines | Review status | Action |
|---|---:|---|---|
| `docs/archive/README.md` | 15 | Archive index | Updated with metadata and review-report link. |
| `docs/archive/historical-documents/ARCHITECTURE_BLUEPRINT.md` | 44 | Historical architecture snapshot | Preserve; not current source of truth. |
| `docs/archive/markdowns/56_Architecture_Decision_Records_ADRs.md` | 722 | Historical ADR bundle | Preserve; superseded by `docs/adr/`. |
| `docs/archive/markdowns/57_FAQ_Document.md` | 95 | Historical FAQ | Preserve. |
| `docs/archive/markdowns/compass_artifact_wf-eeb53485-f211-4476-b343-dec6b21b1e20_text_markdown.md` | 45 | Imported research artifact | Preserve. |
| `docs/archive/markdowns/complete_verification_checklist (1).md` | 228 | Historical verification checklist | Cleanup candidate paired with shorter same-title file. |
| `docs/archive/markdowns/complete_verification_checklist.md` | 30 | Historical verification checklist fragment | Cleanup candidate paired with longer same-title file. |
| `docs/archive/markdowns/group_a_b_alignment_analysis.md` | 555 | Historical KA alignment analysis | Preserve as research reference. |
| `docs/archive/markdowns/layered_analysis_report.md` | 150 | Historical layered-analysis report | Preserve as research reference. |
| `docs/archive/markdowns/UKG_17_Axis_Mathematical_Framework_v3.md` | 1233 | Historical mathematical framework | Preserve as research reference. |
| `docs/archive/markdowns/UKG_17_Axis_Mathematical_Manual_v1.0.md` | 1607 | Historical mathematical manual | Preserve as research reference. |
| `docs/archive/markdowns/ukg_layers_5_10_implementation_guide.md` | 225 | Historical implementation guide | Preserve as research reference. |
| `docs/archive/markdowns/ukg_layers_5_10_update.md` | 251 | Historical implementation update | Preserve as research reference. |
| `docs/archive/markdowns/ukg_simulation_context_instructions.md` | 190 | Historical simulation instructions | Preserve as research reference. |
| `docs/archive/research/CROSS_USER_TESTING.md` | 230 | Historical cross-user testing guide | Preserve; validate against current single-owner auth before reuse. |
| `docs/archive/research/K8S_OPERATOR_DESIGN.md` | 76 | Historical Kubernetes design spike | Cleanup/roadmap candidate; keep archived. |
| `docs/archive/research/REACT_NATIVE_RESEARCH.md` | 68 | Historical mobile design spike | Cleanup/roadmap candidate; keep archived. |
| `docs/archive/research/RELEASE_NOTES_v2.5.0.md` | 174 | Historical release summary | Preserve; not current release status. |
| `docs/archive/whitepapers/UKG_Grok_Whitepaper.md` | 2831 | Historical whitepaper | Preserve as research reference. |
| `docs/archive/whitepapers/UKG_Workflow_Architecture.md` | 15598 | Historical architecture transcript | Preserve as research reference; avoid production citations without verification. |
| `docs/archive/wireframes/2025-design-system.md` | 732 | Historical wireframe/design system | Preserve; not active implementation spec. |
| `docs/archive/wireframes/chat-interface-2025.md` | 560 | Historical wireframe | Preserve; not active implementation spec. |
| `docs/archive/wireframes/knowledge-graph-dashboard-2025.md` | 494 | Historical wireframe | Preserve; not active implementation spec. |
| `docs/archive/wireframes/landing-page-2025.md` | 345 | Historical wireframe | Preserve; not active implementation spec. |
| `docs/archive/wireframes/login-auth-2025.md` | 610 | Historical auth wireframe | Cleanup/roadmap candidate; conflicts with current desktop auth. |
| `docs/archive/wireframes/README.md` | 386 | Historical wireframe index | Updated with metadata and production-boundary note. |

## Subfolder Summary

| Subfolder | Markdown reviewed | Production posture |
|---|---:|---|
| `docs/archive/` | 1 | Archive index only. |
| `docs/archive/historical-documents/` | 1 | Historical reference only. |
| `docs/archive/markdowns/` | 12 | Historical research and verification material. |
| `docs/archive/research/` | 4 | Historical design spikes and old release notes. |
| `docs/archive/whitepapers/` | 2 | Historical whitepapers and research transcripts. |
| `docs/archive/wireframes/` | 6 | Historical design references, not implementation specs. |
