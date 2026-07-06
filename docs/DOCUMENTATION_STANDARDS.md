# DataLogicEngine Documentation Standards

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.7.0 |
| Last updated | 2026-07-06 |
| Status | Active |
| Owner | Platform Engineering |
| Review cadence | Every 30 days |

## Purpose

Define production-grade documentation requirements for DataLogicEngine and establish consistent quality gates for AI system, local-first desktop, security, privacy, operations, and release documentation.

## Audience

1. Platform engineering
2. Frontend/backend developers
3. Security and compliance reviewers
4. Operations and support engineers
5. Release managers
6. Technical judges and external evaluators

## Scope

This standard applies to:

1. `README.md`;
2. active source-of-truth documents under `docs/`;
3. operational runbooks referenced by CI/CD, release, desktop packaging, or support workflows;
4. active diagrams in `docs/diagrams/`;
5. governance and compliance mapping documents.

This standard does not apply as a strict source-of-truth requirement to:

1. archived whitepapers;
2. historical research notes;
3. generated inventory files;
4. exploratory drafts explicitly marked as historical or archive.

Archived documents may be used as inputs for future combined papers, but active docs remain the operational source of truth.

---

## Required metadata model

Every active source-of-truth markdown document should include a metadata table near the top:

```markdown
## Document metadata

| Field | Value |
|---|---|
| Document version | vX.Y.Z |
| Last updated | YYYY-MM-DD |
| Status | Active |
| Owner | <team/persona> |
| Review cadence | Every N days |
```

Additional fields such as `Audience`, `Effective date`, or `Status: Roadmap` may be added when useful.

---

## Required active-document sections

Each active document should include these sections or direct equivalents:

1. Purpose;
2. Audience or intended reviewer;
3. Scope or applicability;
4. Current architecture/behavior/procedure;
5. Validation, evidence, or reviewer path;
6. Known caveats/limitations where relevant;
7. Related documents;
8. Change notes for the current version.

Operational documents should also include:

1. prerequisites;
2. commands/procedures;
3. expected outputs or success criteria;
4. troubleshooting;
5. rollback or recovery where relevant.

---

## AI application-specific requirements

AI-related docs must cover:

1. model/provider behavior and configuration;
2. DMRF or governance lifecycle impact;
3. TruthGate/TruthCore/TruthMemory/TruthLink impact where applicable;
4. 17-axis and DSQP impact where applicable;
5. prompt injection or unsafe-input handling where applicable;
6. evidence, claims, traceability, or export behavior;
7. privacy and data movement implications;
8. failure/fallback behavior;
9. human review/escalation where applicable;
10. limitations and uncertainty.

---

## Evidence-driven documentation rules

1. Distinguish implemented behavior from target-state roadmap.
2. Do not claim certifications, attestations, or benchmark conformance without evidence.
3. Do not claim SLSA, SBOM, Sigstore, Rekor, CodeQL, DAST, or scanner coverage unless workflow artifacts prove it.
4. Do not state local-first means air-gapped.
5. Do not state desktop local-auth is valid as a cloud/web trust boundary.
6. Tie API claims to route behavior and tests.
7. Tie release claims to checklist evidence.
8. Tie security claims to implementation paths, tests, or runbooks.
9. Mark archived/exploratory material clearly as historical/reference.
10. Avoid duplicating backlog lists; use root `TODO.md` for active follow-up items.

---

## Writing and structure rules

1. Use direct, active language.
2. Use explicit dates in `YYYY-MM-DD` format.
3. Use copy-ready command blocks.
4. Use precise file paths, route names, env vars, and API endpoints.
5. Prefer tables for mappings and matrices.
6. Use diagrams only when they clarify actual implementation.
7. Avoid vague phrases such as "enterprise-grade" unless supported by specific evidence.
8. Keep claims testable and reviewable.
9. Add caveats when implementation is partial.
10. Keep archived/historical context separate from operational instructions.

---

## Diagram and architecture map rules

1. Diagrams must map to real code paths, runtime services, or documented control points.
2. Diagrams must distinguish local desktop, Windows VM, and web/cloud paths where relevant.
3. Trust boundaries must be explicit for security/data-flow diagrams.
4. Provider and connector data movement must be visible where relevant.
5. Trace/export/privacy flows must identify whether data leaves the local application boundary.
6. Active diagrams should be referenced by `docs/ARCHITECTURE_MAP.md` or related source-of-truth docs.

---

## Documentation quality gates

Before merge or release:

```powershell
python scripts/verify_docs_references.py
python scripts/generate_docs.py
python scripts/verify_environment_parity.py --strict
python scripts/verify_lockfiles.py
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
```

When docs reference schema/data behavior:

```powershell
python scripts/validate_schema_parity.py
```

When docs reference Windows packaging/release behavior:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\verify_nsis_governance.ps1 -RepoRoot (Get-Location).Path
.\.venv\Scripts\python.exe scripts\verify_installer_integrity.py --require-artifacts
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot (Get-Location).Path -Mode installer
```

For desktop installer release docs, also state that `scripts/build_backend.py` runs before Electron/NSIS packaging so the shipped backend matches source.

---

## Lifecycle management

1. Active docs must be reviewed at the cadence declared in their metadata.
2. `docs/DOCUMENTATION_COVERAGE_MATRIX.md` must list active source-of-truth docs.
3. `docs/DOCUMENTATION_VERSIONING.md` defines version rules.
4. `docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md` defines the production documentation baseline.
5. `docs/archive/*` remains historical/reference unless promoted into active docs.
6. Release-impacting changes must update relevant active docs and release checklist evidence.
7. Documentation version metadata must be updated when source-of-truth docs change.

## Change notes for v2.7.0

1. Added installer integrity and installer-mode smoke to the packaging/release documentation quality gates.
2. Added an explicit requirement to document backend-before-Electron packaging order for desktop installer release docs.
3. Updated metadata for the production top-level documentation review.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Added required metadata model.
3. Updated standards for DMRF, Truth Engine, local-first, privacy, release, and evidence-driven documentation.
4. Added stronger rules against unsupported compliance/security claims.
5. Added diagram/data-flow rules and current quality gates.
