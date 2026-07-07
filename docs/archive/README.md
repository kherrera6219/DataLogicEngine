# Documentation Archive

> **Document metadata**
> - Document version: v1.2.0
> - Last reviewed: 2026-07-06
> - Status: Active archive index
> - Owner: Documentation Governance

This folder contains historical, reference-only, or superseded documentation. These files are preserved for research and traceability, but they are not operational source-of-truth for the current application.

Use the active documentation portal at [`docs/README.md`](../README.md) and the canonical open-work list at [`TODO.md`](../../TODO.md) for current guidance.

The latest archive Markdown review is recorded in [`ARCHIVE_MARKDOWN_REVIEW_2026-07-06.md`](ARCHIVE_MARKDOWN_REVIEW_2026-07-06.md).

## Contents

| Folder | Contents | Status |
| --- | --- | --- |
| `historical-documents/` | Residual imported planning/source documents that are not classified as active or archived whitepapers | Historical reference |
| `whitepapers/` | Consolidated historical UKG/USKD whitepapers, mathematical PDFs, design papers, and deep architecture narratives | Historical reference |
| `wireframes/` | 2025 design-system and wireframe drafts previously stored under `docs/wireframes/` | Historical design reference |
| `research/` | Old release notes, platform research, and design spikes not listed in the active documentation portal | Historical reference |
| `api/` | Superseded OpenAPI/Postman exports that no longer match the active single-owner desktop auth/API surface | Historical reference |

## Whitepaper Reorganization

On 2026-07-06, whitepaper-like historical PDFs and selected historical Markdown references were consolidated under `docs/archive/whitepapers/`. Current high-value whitepaper assets that remain production-facing are indexed in `docs/whitepapers/README.md`.

## Policy

1. Do not add new planning documents here until actionable items have been folded into the root `TODO.md`.
2. Do not treat archived content as current implementation status without validating it against code and active docs.
3. If archived material becomes current again, move it back into the active docs tree and link it from `docs/README.md`.
4. Prefer cataloging cleanup candidates before deleting archive files; historical value and old external links may still matter.
