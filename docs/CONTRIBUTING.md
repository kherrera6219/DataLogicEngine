# Contributing — Documentation View

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Developer Experience |
| Review cadence | Every 30 days |

## Purpose

Define documentation-specific contribution requirements and point contributors to the canonical repository contribution policy.

## Canonical contribution policy

The repository root contribution policy is the source of truth:

1. `CONTRIBUTING.md`

Use this document for documentation-specific expectations only.

---

## Documentation-specific requirements

1. Follow `docs/DOCUMENTATION_STANDARDS.md`.
2. Follow `docs/DOCUMENTATION_VERSIONING.md` for metadata and lifecycle rules.
3. Update `docs/DOCUMENTATION_COVERAGE_MATRIX.md` when adding, renaming, promoting, or retiring active docs.
4. Use one active source-of-truth document per domain area.
5. Mark roadmap, partial, historical, and archived material clearly.
6. Do not treat `docs/archive/*` as operational source-of-truth.
7. Fold actionable planning items into root `TODO.md` before deleting obsolete planning docs.
8. Include tested commands for operational runbooks.
9. Update `README.md` and `docs/README.md` when setup, runtime, security, or reviewer navigation changes.
10. Keep release-impacting docs aligned with `docs/RELEASE_CHECKLIST.md` and `docs/PRODUCTION_READINESS.md`.

---

## Documentation PR checklist

1. Links resolve to existing files.
2. Commands are copy-ready and platform-appropriate.
3. Metadata block is present and current.
4. Related documents section is updated.
5. Change notes are included for substantive changes.
6. Claims are supported by code, tests, workflows, or release evidence.
7. The change does not contradict active source-of-truth docs.
8. `docs/DOCS_VERSION.json` is updated when required.
9. `docs/README.md` and coverage matrix are updated when adding or replacing active docs.

---

## Validation

```powershell
python scripts/verify_docs_references.py
python scripts/generate_docs.py
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
```

For release-impacting documentation changes:

```powershell
python scripts/verify_release_governance.py
```

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Aligned documentation contribution rules with the v2.6.0 documentation standards and versioning policy.
3. Added source-of-truth/archive guidance and evidence-based claim requirements.
4. Added validation commands.
