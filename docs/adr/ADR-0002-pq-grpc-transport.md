# ADR-0002: PQ-gRPC Transport Research

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.1.0 |
| Last reviewed | 2026-07-06 |
| Status | Accepted |
| Owner | Platform Architecture |
| Review cadence | Historical decision; review only for supersession |

## Status

Accepted

## Date

2026-05-27

## Context

Phase G-B listed post-quantum gRPC transport as long-term Windows VM research. The local-first desktop application already uses local HTTP, IPC, SQLite/PostgreSQL-compatible storage, Redis, Neo4j, ChromaDB, and filesystem object storage inside the app-owned stack. Adding a mandatory gRPC or post-quantum transport dependency to desktop would expand the runtime surface without solving a current local-first requirement.

## Decision

Do not add PQ-gRPC as a desktop dependency. Treat PQ-gRPC as a VM-only research track until a deployment requires cross-node TruthLink transport with post-quantum key exchange. Keep current desktop/VM local paths on the app-managed internal services.

If a VM deployment later requires PQ-gRPC, prototype it behind an opt-in feature flag and keep existing TruthLink Redis Streams and in-memory transport as the compatibility path.

## Consequences

- Desktop installer scope remains unchanged.
- Phase G-B can close with an ADR instead of a runtime prototype.
- Future PQ-gRPC work needs a separate performance/security evaluation before implementation.

## Change notes for v1.1.0

1. Added metadata during the docs subfolder review.
