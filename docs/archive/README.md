# Documentation Archive

> **Document metadata**
> - Document version: v1.2.0
> - Last reviewed: 2026-07-06
> - Status: Active archive index
> - Owner: Documentation Governance

This folder contains historical, reference-only, or superseded documentation. These files are preserved for research and traceability, but they are not operational source-of-truth for the current application.

Use the active documentation portal at [`docs/README.md`](../README.md) and the canonical open-work list at [`TODO.md`](../../TODO.md) for current guidance.

The latest archive Markdown review is recorded in [`ARCHIVE_MARKDOWN_REVIEW_2026-07-06.md`](ARCHIVE_MARKDOWN_REVIEW_2026-07-06.md).

## Phase 16 controlled source archive

`docs/archive/phase-16/` preserves the 72 source documents consolidated by
Phase 16 CP16-F on 2026-07-15. The originals retain their relative directory
shape; former root sources are under `phase-16/root/`. These files are historical
evidence only and are not active product, engineering, operating, security, or
release authority.

`reports/production-readiness/2026/phase-16/document-replacement-baseline.json`
records each source's pre-move SHA-256, byte count, Git blob, canonical target,
and archive destination. `document-replacement-closure.json` verifies 72/72
retained hashes, 18/18 routed target reviews, zero active legacy sources, and
zero unmigrated active links. Use `docs/DOCUMENTATION_CROSSWALK.md` for the full
154-file disposition record and `docs/README.md` for current authority.

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
