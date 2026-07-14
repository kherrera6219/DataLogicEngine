# Architecture Decision Records (ADR)

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.11.0 |
| Last updated | 2026-07-14 |
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
| `ADR-0003-internal-service-delivery.md` | App-owned pinned OCI containers through rootless Podman Machine/WSL2 | Accepted / Phase 0 CP0-B |
| `ADR-0004-seaweedfs-replacement-qualification.md` | SeaweedFS candidate replacement qualification | Proposed / candidate only |
| `ADR-0005-external-gateway-boundary.md` | External principal, network profile, virtual-model, and compatibility boundary | Accepted / Phase 8 implementation |
| `ADR-0006-memory-authority-and-trust-boundary.md` | Memory authority, trust-state, lifecycle, and migration boundary | Accepted / Phase 9 implementation |
| `ADR-0007-authoritative-simulation-engine.md` | Multi-agent debate authority, bounded provider adapter, durable lifecycle, and FROST component boundary | Accepted / Phase 10 engineering selection |
| `ADR-0008-governed-mcp-connector-boundary.md` | MCP 2025-11-25 stdio, exact consent, Windows containment, durable authority, and governed-result boundary | Accepted / Phase 11 engineering selection |

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
## ADR-000X: Title

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

## Change notes for v2.11.0

1. Added ADR-0008 selecting the bounded governed MCP connector boundary.

## Change notes for v2.10.0

1. Added ADR-0007 selecting one backend multi-agent simulation workflow and
   limiting FROST to a possible checkpoint implementation.

## Change notes for v2.9.0

1. Added ADR-0006 for the Phase 9 memory authority and trusted-recall boundary.
2. Recorded `unified-memory.v2` migration, lifecycle, and corruption-recovery
   requirements.

## Change notes for v2.8.0

1. Added ADR-0004 and ADR-0005 to the current index.
2. Recorded the accepted Phase 8 external-gateway authority boundary while
   preserving private exposure as qualification-gated.

## Change notes for v2.7.0

1. Added review metadata to the accepted ADR files.
2. Adjusted the template heading level so docs validation does not treat the example as a second top-level heading.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Added ADR status table.
3. Added current decision areas requiring ADR coverage.
4. Added ADR template and supersession rules.
