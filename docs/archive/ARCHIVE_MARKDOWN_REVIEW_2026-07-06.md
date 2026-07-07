# Archive Markdown Review - 2026-07-06

> **Document metadata**
> - Document version: v1.1.0
> - Last reviewed: 2026-07-06
> - Status: Active archive review report
> - Owner: Documentation Governance
> - Scope: `docs/archive/**/*.md` historical/reference material.

## Review Method

This pass reviewed the pre-existing Markdown files under `docs/archive/` by folder, title, line count, archive status, and targeted scans for stale production-risk terms such as SSO, Azure AD, React Native, Kubernetes, multi-tenant, active/current, and production-ready.

After the subsequent 2026-07-06 whitepaper reorganization, the archive contains 21 Markdown files and the whitepaper-like historical PDFs/Markdown references are consolidated under `docs/archive/whitepapers/`.

Archive documents were cataloged rather than rewritten in place. This preserves historical research value while preventing archived plans from being mistaken for the current production source of truth.

## Archive Policy Decision

- No archived file was promoted back into active documentation in this pass.
- No archived file was deleted in this pass.
- Active source of truth remains `docs/README.md`, root `docs/*.md`, `docs/adr/`, `docs/diagrams/`, `docs/audits/`, generated inventory files, and `TODO.md`.
- Historical implementation claims must be checked against code and active docs before they are used in production planning.

## Cleanup Candidates

| Candidate | Finding | Recommended action |
|---|---|---|
| `docs/archive/research/K8S_OPERATOR_DESIGN.md` | Kubernetes operator planning for a v3.0 cluster strategy, outside current local-first desktop production scope. | Keep archived; do not link from active release docs unless Kubernetes work is reopened. |
| `docs/archive/research/REACT_NATIVE_RESEARCH.md` | React Native/mobile-axis plan, outside current desktop production scope. | Keep archived; do not treat as an active roadmap item unless mobile scope is explicitly reopened. |
| `docs/archive/wireframes/login-auth-2025.md` | Historical SSO/Azure AD/Okta login design conflicts with current single-owner desktop auth posture. | Keep archived only; active auth docs should point to desktop local auth and auth-deprecation docs. |
| `docs/archive/whitepapers/UKG_Workflow_Architecture.md` | Very large research/architecture transcript with dated as-of/current statements and speculative cloud/multi-tenant sections. | Preserve as research archive; cite active docs for production behavior. |

## Reviewed Markdown Catalog

| File | Lines | Review status | Action |
|---|---:|---|---|
| `docs/archive/README.md` | 15 | Archive index | Updated with metadata and review-report link. |
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
| `docs/archive/whitepapers/ARCHITECTURE_BLUEPRINT.md` | 44 | Historical architecture snapshot | Moved into consolidated archive whitepapers/reference folder. |
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
| `docs/archive/` | 2 | Archive index and archive review report. |
| `docs/archive/historical-documents/` | 0 | Historical non-Markdown source files only after whitepaper reorganization. |
| `docs/archive/markdowns/` | 6 | Historical research and verification material. |
| `docs/archive/research/` | 4 | Historical design spikes and old release notes. |
| `docs/archive/whitepapers/` | 3 | Historical whitepapers and research transcripts. |
| `docs/archive/wireframes/` | 6 | Historical design references, not implementation specs. |
