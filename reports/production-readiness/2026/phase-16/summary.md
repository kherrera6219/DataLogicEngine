# Phase 16 CP16-A information-architecture checkpoint

## Status

Phase 16 is active and CP16-A is owner-approved and complete. The approval covers
the information architecture, canonical set, IDs, ownership, controlled status
vocabulary, required headers, and complete source-to-target map. It does not
authorize any document move, archive, merge deletion, or authority retirement.

The CP16-B product/user content checkpoint is complete. Five mapped canonical
targets now cover product requirements, installation/lifecycle, administration/
operations, troubleshooting/support, and privacy/provider/retention/AI
limitations. The signed-RC unfamiliar-user walkthrough remains a retained CP16-B
exit gate, and CP16-C document construction is active.

The first CP16-C content batch adds seven canonical engineering/assurance
targets: data architecture, interface/integration, security architecture,
software lifecycle, maintenance/disaster recovery, requirements traceability,
and V&V. CP16-C remains active for five assurance/release records.

## Results

- One approved versioned authority selects exactly 30 hand-maintained canonical documents
  across five controlled classes.
- Twenty-two canonical targets exist; eight are planned replacement documents.
- Every one of the 146 current root and `docs/**` Markdown files has exactly one
  disposition.
- Dispositions: 26 authoritative inputs, five generated replacements, 43
  historical/archive records, and 72 source-to-canonical merge routes.
- Zero unclassified files, duplicate routes, duplicate canonical paths, duplicate
  document IDs, unknown classes, or noncanonical merge targets.
- The generated BOM defines the document IDs, paths, owners, classes, required
  controlled-header fields, and truthful status vocabulary.
- The generated crosswalk explicitly states that it does not authorize archive
  or deletion before manual route/content/link review.
- All 22 existing canonical documents contain the required 13-field controlled
  header, exact document ID, product 4.3.0 binding, controlled status, owner, and
  owner approver. Eight canonical targets remain planned.

## Controls added

- `config/documentation-authority.json`
- `scripts/generate_documentation_authority.py`
- `scripts/verify_documentation_bom.py`
- `scripts/verify_doc_authority.py`
- `scripts/verify_product_user_docs.py`
- `scripts/verify_engineering_assurance_docs.py`
- `docs/DOCUMENTATION_BOM.md`
- `docs/DOCUMENTATION_CROSSWALK.md`
- `tests/unit/test_documentation_authority.py`

## Validation

- Documentation BOM verification: pass, 30/30 canonical, 146 inventory rows,
  zero errors.
- Document authority verification: pass, 22/22 existing headers, eight planned,
  archive/delete authorization false, zero errors.
- Product/user document verification: pass, five of five targets, zero errors.
- Engineering/assurance document verification: pass, seven of seven targets,
  zero errors.
- Seven focused documentation-authority unit tests passed.
- Ruff passed for the generator, all four verifiers, and tests.

## Next

Complete CP16-C with the KA/TruthCore validation dossier, privacy impact
assessment, accessibility conformance report, third-party software index, and
release-readiness record. Preserve truthful open status, then proceed to the
CP16-D/CP16-E external-review records. Defer archive/delete work.
