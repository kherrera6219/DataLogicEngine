# Architecture Decision Records (ADR)

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Platform Architecture |
| Review cadence | Every 60 days |

## Purpose

Capture high-impact technical decisions with context, alternatives, consequences, and implementation links.

ADRs are historical decision records. Accepted ADRs should not be rewritten to match later architecture changes; instead, create a superseding ADR when a decision changes.

---

## Current ADR index

| ADR | Topic | Status |
|---|---|---|
| `ADR-0001-engineering-governance-baseline.md` | Engineering governance baseline | Accepted / historical source |
| `ADR-0002-pq-grpc-transport.md` | PQ/gRPC transport decision | Accepted / historical source |

---

## When to create an ADR

Create or update an ADR when a change affects:

1. runtime architecture;
2. DMRF or Truth Engine behavior;
3. 17-axis or DSQP model semantics;
4. security/authentication trust boundaries;
5. privacy/export guarantees;
6. data-store or memory architecture;
7. API compatibility/versioning;
8. release, deployment, or supply-chain governance;
9. major frontend/product-surface structure.

---

## Authoring rules

1. One decision per ADR file.
2. Use immutable ADR IDs such as `ADR-0001`, `ADR-0002`, and so on.
3. Do not rewrite historical context after acceptance.
4. Use `Supersedes` and `Superseded by` fields when decisions change.
5. Link ADRs from implementation PRs and relevant source-of-truth docs.
6. Distinguish implemented decisions from roadmap decisions.
7. Avoid compliance/certification claims unless evidence exists.

---

## Recommended ADR template

```markdown
# ADR-000X: Title

## Status

Proposed | Accepted | Superseded | Deprecated

## Date

YYYY-MM-DD

## Context

What problem or decision pressure exists?

## Decision

What decision was made?

## Alternatives considered

1. Option A
2. Option B
3. Option C

## Consequences

Positive, negative, and operational consequences.

## Implementation references

- file/path.py
- docs/RELATED.md

## Supersedes / superseded by

- Supersedes: none
- Superseded by: none
```

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Added ADR status table.
3. Added current decision areas requiring ADR coverage.
4. Added ADR template and supersession rules.
