# Phase 16 information-architecture starter checkpoint

## Status

Phase 16 is active. The information-architecture foundation is implemented and
validated as a draft. CP16-A is not yet approved, and no document move, archive,
merge deletion, or authority retirement is authorized by this batch.

## Results

- One versioned authority selects exactly 30 hand-maintained canonical documents
  across five controlled classes.
- Ten canonical targets exist; 20 are planned replacement documents.
- Every one of the 134 current root and `docs/**` Markdown files has exactly one
  disposition.
- Dispositions: 14 authoritative inputs, five generated replacements, 43
  historical/archive records, and 72 source-to-canonical merge routes.
- Zero unclassified files, duplicate routes, duplicate canonical paths, duplicate
  document IDs, unknown classes, or noncanonical merge targets.
- The generated BOM defines the document IDs, paths, owners, classes, required
  controlled-header fields, and truthful status vocabulary.
- The generated crosswalk explicitly states that it does not authorize archive
  or deletion before manual route/content/link review.

## Controls added

- `config/documentation-authority.json`
- `scripts/generate_documentation_authority.py`
- `scripts/verify_documentation_bom.py`
- `docs/DOCUMENTATION_BOM.md`
- `docs/DOCUMENTATION_CROSSWALK.md`
- `tests/unit/test_documentation_authority.py`

## Validation

- Documentation BOM verification: pass, 30/30 canonical, 134 inventory rows,
  zero errors.
- Four focused documentation-authority unit tests passed.
- Ruff passed for the generator, verifier, and tests.

## Next

Review and approve or correct each route, apply controlled headers to existing
canonical documents, implement the broader document-authority verifier, create
the 20 planned targets from verified sources, migrate inbound links, and only
then begin controlled archive/delete work.
