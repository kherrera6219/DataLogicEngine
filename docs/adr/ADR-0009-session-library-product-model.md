# ADR-0009: Session Library Product Model

## Document metadata

| Field | Value |
|---|---|
| Status | Accepted - Phase 12 product semantics |
| Date | 2026-07-14 |
| Owner | Product and Platform Architecture |
| Decision scope | Desktop project/workspace naming, identity, and persistence |
| Supersedes | Implicit independent-project wording in earlier UI and product docs |
| Superseded by | None |

## Context

The `/projects` and `/projects/view` routes do not use a Project entity, project
API, project files, notes, membership, or independent project lifecycle. They
list and inspect the current owner's durable chat sessions through
`/gateway/sessions` and `/gateway/sessions/{id}/messages`. Calling those records
projects or workspaces implied unsupported create/rename/archive/delete, file,
note, and linkage behavior. Several controls reinforced that implication but had
no backend action.

Introducing an independent durable project model during the UI completion phase
would require a new PostgreSQL authority, migrations, ownership rules, API
contracts, cross-linking, deletion semantics, and installed migration evidence.
The current product requirement is already served by durable session history.

## Decision

The initial production product uses a **Session Library**, not independent
Projects.

- The canonical identity is the existing durable chat session ID.
- The library lists, filters, and opens session messages and trace links backed
  by the gateway session contract.
- The existing `/projects` URLs remain compatibility routes for this release,
  but visible product copy uses Session Library and Sessions.
- Project-only uploads, notes, per-message delete/download menus, project status,
  and other unsupported controls are removed rather than simulated.
- Session rename, archive, delete, export, and clear controls remain absent until
  a durable owner-scoped API and destructive-action contract exist.
- A future independent workspace model requires a new ADR, schema/API migration,
  import/linking policy, backup/restore coverage, and installed acceptance.

## Alternatives considered

### Add a new Project entity now

Rejected for the initial release. It expands identity, authorization, migration,
storage, and deletion scope without an established owner workflow that requires
more than durable sessions.

### Keep the Projects label as a visual alias

Rejected. The label implied files, notes, lifecycle, and workspace semantics the
application did not implement.

### Remove the routes entirely

Rejected. Session history and detail are useful real workflows, and keeping the
existing route paths avoids unnecessary navigation compatibility breakage.

## Consequences

Positive:

- visible terminology matches the real persistence authority;
- unsupported project controls are no longer actionless;
- no speculative schema or migration is added;
- session history remains available without route churn.

Constraints:

- the route path remains `/projects` until a later compatibility migration;
- no independent workspace files, notes, lifecycle, or membership exists;
- future project functionality cannot reuse the Session Library label without a
  new explicit persistence decision.

## Implementation references

- `frontend/app/projects/page.tsx`
- `frontend/app/projects/view/page.tsx`
- `frontend/components/projects/ProjectDetail.tsx`
- `frontend/components/layout/AppSidebar.tsx`
- `frontend/lib/api/chat.ts`
- `reports/production-readiness/2026/phase-12/inventory.md`
