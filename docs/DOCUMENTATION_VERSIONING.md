# Documentation Versioning Policy

## Purpose

Define versioning and lifecycle rules for active documentation.

## Version Source

1. Canonical docs version manifest: `docs/DOCS_VERSION.json`.
2. Root changelog for release-level documentation changes: `CHANGELOG.md`.

## Policy

1. Bump `docs/DOCS_VERSION.json` whenever source-of-truth docs or governance docs change.
2. Keep `updated_at` in ISO date format (`YYYY-MM-DD`).
3. Keep planning history out of active docs; fold actionable items into root `TODO.md` before removing stale planning files.
4. Include document-control metadata in major runbooks and standards docs.
5. Ensure `docs/README.md` and `docs/DOCUMENTATION_COVERAGE_MATRIX.md` reference any new active docs.

## Governance Checks

1. `python scripts/verify_docs_references.py`
2. `python scripts/generate_docs.py`
3. `python scripts/verify_environment_parity.py`
4. `python scripts/verify_lockfiles.py`

## Document Control

1. Owner: Platform Engineering
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days
