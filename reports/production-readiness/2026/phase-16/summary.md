# Phase 16 CP16-A information-architecture checkpoint

## Status

Phase 16 is active and CP16-A is owner-approved and complete. The approval covers
the information architecture, canonical set, IDs, ownership, controlled status
vocabulary, required headers, and complete source-to-target map. It does not
authorize any document move, archive, merge deletion, or authority retirement.

## Results

- One approved versioned authority selects exactly 30 hand-maintained canonical documents
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
- All ten existing canonical documents contain the required 13-field controlled
  header, exact document ID, product 4.3.0 binding, controlled status, owner, and
  owner approver. Twenty canonical targets remain planned.

## Controls added

- `config/documentation-authority.json`
- `scripts/generate_documentation_authority.py`
- `scripts/verify_documentation_bom.py`
- `scripts/verify_doc_authority.py`
- `docs/DOCUMENTATION_BOM.md`
- `docs/DOCUMENTATION_CROSSWALK.md`
- `tests/unit/test_documentation_authority.py`

## Validation

- Documentation BOM verification: pass, 30/30 canonical, 134 inventory rows,
  zero errors.
- Document authority verification: pass, 10/10 existing headers, 20 planned,
  archive/delete authorization false, zero errors.
- Five focused documentation-authority unit tests passed.
- Ruff passed for the generator, both verifiers, and tests.

## Next

Begin CP16-B with the product requirements, installation, administrator/
operations, troubleshooting/support, and privacy/AI notice targets. Preserve
mapped requirements, decisions, limitations, and evidence; migrate inbound links
after target review, and only then begin controlled archive/delete work.
