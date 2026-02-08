# DataLogicEngine Documentation Standards

## Document purpose

Define enterprise documentation standards for DataLogicEngine and establish a single, auditable style baseline for all active documentation.

## Sources reviewed (Microsoft)

The standards below are aligned to Microsoft primary guidance:

1. Microsoft Writing Style Guide:
   https://learn.microsoft.com/style-guide/welcome/
2. Microsoft Learn documentation overview:
   https://learn.microsoft.com/en-us/contribute/content/
3. Microsoft style guidance for procedures/instructions:
   https://learn.microsoft.com/style-guide/procedures-instructions/
4. Microsoft style guidance for titles and headings:
   https://learn.microsoft.com/style-guide/scannable-content/headings

## Scope

Applies to:

1. `README.md`
2. All active files under `docs/`
3. Runbooks and operational procedures referenced by CI/CD and production support

Does not apply to:

1. `docs/archive/` historical artifacts
2. `docs/whitepapers/` long-form research narratives
3. Auto-generated inventories (`FILE_INVENTORY.csv`, generated structure maps)

## Required structure for active docs

Every active document must include these top-level sections (or equivalent):

1. `Purpose`
2. `Audience`
3. `Prerequisites` (if operational)
4. `Procedure` or `Reference` content
5. `Validation` (commands/checks where applicable)
6. `Troubleshooting` or `Known limitations` (if operational)
7. `Related documents`
8. `Document control` block

## Document control block

Active docs should include a control block near the top:

1. `Owner`: team or role
2. `Last updated`: ISO date
3. `Status`: Draft, Active, Deprecated, Archived
4. `Review cadence`: for example, 30/60/90 days

## Content model

Use these content types intentionally:

1. `Concept`: architecture and design intent (`docs/ARCHITECTURE.md`)
2. `How-to`: step-by-step operations (`docs/WINDOWS_11_LOCAL_RUNBOOK.md`, `docs/DEPLOYMENT.md`)
3. `Reference`: APIs, configuration, schema (`docs/API.md`, `docs/openapi.yaml`)
4. `Policy/Standard`: security/compliance and governance (`docs/SECURITY.md`, `docs/SDLC_SSDF_MAPPING.md`)

## Writing rules

1. Use clear, direct, active voice.
2. Prefer sentence-case headings for readability.
3. Keep procedures task-oriented and numbered.
4. Put prerequisites before commands.
5. Use explicit command blocks with copy-ready syntax.
6. Use exact file paths and environment variable names.
7. Avoid ambiguous terms such as "soon", "later", "some".
8. Avoid contradictory statements across duplicated docs.

## Operational quality gates

Before merging documentation updates:

1. Validate command examples on target platform (Windows for desktop runbooks).
2. Ensure cross-links resolve to existing files.
3. Ensure one source-of-truth document per area.
4. Update `docs/README.md` index and coverage matrix when adding a new active doc.

## Lifecycle management

1. Active docs must be reviewed at the cadence declared in document control.
2. Obsolete docs should be moved to `docs/archive/` with replacement link.
3. Major release changes must update:
   - `README.md`
   - `docs/DEPLOYMENT.md`
   - `docs/SECURITY.md`
   - `docs/PRODUCTION_READINESS.md`
   - `docs/WINDOWS_11_LOCAL_RUNBOOK.md` (for desktop release paths)

