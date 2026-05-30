# Documentation Versioning Policy

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Purpose

Define versioning, lifecycle, ownership, and governance rules for active DataLogicEngine documentation.

## Version sources

Primary sources:

1. `docs/DOCS_VERSION.json`
2. individual document metadata blocks
3. release notes and changelog entries where applicable

The document metadata block is the authoritative version/date marker for a specific source-of-truth document.

---

## Required metadata

Active source-of-truth documents should include:

```markdown
## Document metadata

| Field | Value |
|---|---|
| Document version | vX.Y.Z |
| Last updated | YYYY-MM-DD |
| Status | Active |
| Owner | Team/Owner |
| Review cadence | Every N days |
```

Roadmap or planning documents may use alternate status values such as:

- Roadmap
- Planning
- Partial Implementation
- Historical

---

## Versioning model

### Patch updates

Increment patch version when:

1. correcting wording;
2. fixing links;
3. correcting commands;
4. updating references;
5. making non-substantive clarifications.

Example:

```text
v2.6.0 -> v2.6.1
```

### Minor updates

Increment minor version when:

1. adding sections;
2. expanding diagrams;
3. updating workflows;
4. adding validation steps;
5. documenting newly implemented functionality.

Example:

```text
v2.6.0 -> v2.7.0
```

### Major updates

Increment major version when:

1. architecture changes substantially;
2. source-of-truth ownership changes;
3. document purpose changes significantly;
4. workflows are fundamentally redesigned;
5. repository governance changes materially.

Example:

```text
v2.6.0 -> v3.0.0
```

---

## Lifecycle states

| State | Meaning |
|---|---|
| Active | Current operational source-of-truth. |
| Roadmap | Planned future-state guidance. |
| Partial Implementation | Documents a mix of implemented and planned behavior. |
| Historical | Preserved for context; not source-of-truth. |
| Deprecated | Scheduled for retirement/replacement. |
| Archived | Moved into archive/reference area. |

---

## Governance rules

1. Update `Last updated` when making substantive changes.
2. Update document version when required by the versioning model.
3. Update `docs/DOCS_VERSION.json` when source-of-truth docs change.
4. Add new active docs to `docs/DOCUMENTATION_COVERAGE_MATRIX.md`.
5. Keep archived whitepapers and exploratory research separate from active docs.
6. Move obsolete planning content into archive or root `TODO.md` as appropriate.
7. Keep change notes synchronized with the current version.
8. Ensure architecture/security/release docs remain internally consistent.

---

## Validation checks

```powershell
python scripts/verify_docs_references.py
python scripts/generate_docs.py
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
```

For release-impacting documentation updates:

```powershell
python scripts/verify_release_governance.py
```

---

## Reviewer guidance

When reviewing documentation:

1. Verify metadata exists.
2. Verify version/date are current.
3. Verify referenced files still exist.
4. Verify diagrams match implementation.
5. Verify claims are supported by code, tests, workflows, or release evidence.
6. Verify archived documents are not being treated as source-of-truth.
7. Verify new active docs appear in the coverage matrix.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Added formal versioning model.
3. Added lifecycle states.
4. Added governance and reviewer guidance.
5. Aligned policy with documentation modernization standards.
