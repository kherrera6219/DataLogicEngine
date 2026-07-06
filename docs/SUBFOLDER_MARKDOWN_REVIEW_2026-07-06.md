# Docs Subfolder Markdown Review - 2026-07-06

> **Document metadata**
> - Document version: v1.0.0
> - Last reviewed: 2026-07-06
> - Status: Active documentation-governance artifact
> - Owner: Documentation Governance
> - Scope: Markdown files under direct `docs/` subfolders, after the separate top-level `docs/*.md` review.

## Scope

This report covers the Markdown review of each direct `docs/` subfolder:

| Subfolder | Markdown count after this pass | Review result |
|---|---:|---|
| `docs/adr/` | 3 | Reviewed and refreshed. |
| `docs/api/` | 0 | No Markdown files to update. |
| `docs/archive/` | 27 | Reviewed and cataloged as historical/reference material. |
| `docs/assets/` | 0 | No Markdown files to update. |
| `docs/audits/` | 6 | Reviewed in separate audit-folder report. |
| `docs/diagrams/` | 11 | Reviewed and refreshed. |
| `docs/documents/` | 1 | Reviewed and expanded into an active folder index. |
| `docs/ip/` | 1 | Reviewed and refreshed. |
| `docs/whitepapers/` | 1 | Reviewed and expanded into an active folder index. |
| `docs/wireframes/` | 1 | Reviewed and expanded into an active folder index. |

## Detailed Review Results

| Area | Files reviewed | Updates made |
|---|---|---|
| ADRs | `docs/adr/ADR-0001-engineering-governance-baseline.md`, `docs/adr/ADR-0002-pq-grpc-transport.md`, `docs/adr/README.md` | Added current metadata/review status and fixed the ADR template H1 example so docs validation does not treat the template as an extra page title. |
| Audits | `docs/audits/*.md` | Added/updated audit review metadata and created `docs/audits/AUDITS_MARKDOWN_REVIEW_2026-07-06.md`. The superseded `docs/audits/DataLogicEngine_Complete_Audit_Plan.md` was deleted after approval; v2 remains active. |
| Diagrams | `docs/diagrams/*.md` | Added review metadata to all 11 active architecture diagrams. Removed stale exact inventory count, changed brittle provider/model wording to configured-provider wording, removed obsolete "Future:" diagram labels, and clarified tenant-compatible budget wording. |
| Folder indexes | `docs/documents/README.md`, `docs/whitepapers/README.md`, `docs/wireframes/README.md` | Replaced three-line move notices with active folder indexes, production-use notes, and cleanup guidance. |
| IP | `docs/ip/dsqp_technical_disclosure.md` | Updated status to reflect that DSQP implementation now exists under `backend/dsqp/`, added metadata, and clarified that the disclosure is not legal advice. |
| Archive | `docs/archive/**/*.md` | Preserved historical content, updated archive indexes, and created `docs/archive/ARCHIVE_MARKDOWN_REVIEW_2026-07-06.md` with per-file catalog and cleanup candidates. |

## Cleanup Decisions

| Item | Decision |
|---|---|
| `docs/audits/DataLogicEngine_Complete_Audit_Plan.md` | Deleted after approval because `docs/audits/DataLogicEngine_Complete_Audit_Plan_v2.md` is the active completed audit plan. |
| `docs/archive/markdowns/complete_verification_checklist.md` and `docs/archive/markdowns/complete_verification_checklist (1).md` | Keep for now; cataloged as cleanup candidates because they share a title but differ in length and hash. |
| `docs/archive/research/K8S_OPERATOR_DESIGN.md` | Keep archived only; Kubernetes/operator work is outside current production scope. |
| `docs/archive/research/REACT_NATIVE_RESEARCH.md` | Keep archived only; mobile scope is outside current production scope. |
| `docs/archive/wireframes/login-auth-2025.md` | Keep archived only; historical SSO/Azure AD login design conflicts with current desktop local-auth posture. |

## Related Review Reports

- `docs/TOP_LEVEL_MARKDOWN_REVIEW_2026-07-06.md`
- `docs/audits/AUDITS_MARKDOWN_REVIEW_2026-07-06.md`
- `docs/archive/ARCHIVE_MARKDOWN_REVIEW_2026-07-06.md`

## Validation Required

After this subfolder pass, regenerate docs and rerun reference validation:

```powershell
python scripts/generate_docs.py
python scripts/verify_docs_references.py
git diff --check
```
