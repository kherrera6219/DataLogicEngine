# Contributing (Documentation View)

## Purpose

Define contribution requirements for documentation and provide a pointer to the canonical repository contribution policy.

## Canonical contribution policy

Use the repository root policy as source-of-truth:

1. `CONTRIBUTING.md`

## Documentation-specific requirements

1. Follow `docs/DOCUMENTATION_STANDARDS.md`.
2. Update `docs/README.md` and `docs/DOCUMENTATION_COVERAGE_MATRIX.md` when adding or replacing active docs.
3. Use one source-of-truth document per domain area.
4. Move obsolete docs to `docs/archive/` instead of deleting historical records.
5. Include tested commands for operational runbooks.
6. Update `README.md` when setup, runtime, or security prerequisites change.
7. Keep governance docs current: `docs/RELEASE_CHECKLIST.md`, `docs/BRANCH_PROTECTION_POLICY.md`, `docs/DOCUMENTATION_VERSIONING.md`.

## Pull request checklist (documentation)

1. Links resolve to existing files.
2. Commands are copy-ready and platform-appropriate.
3. Document control block is present and current.
4. Related documents section is updated.
5. Changes do not contradict existing source-of-truth docs.
6. Documentation version metadata (`docs/DOCS_VERSION.json`) is updated when source-of-truth docs change.

## Document control

1. Owner: Developer Experience
2. Last updated: 2026-02-16
3. Status: Active
4. Review cadence: Every 30 days
