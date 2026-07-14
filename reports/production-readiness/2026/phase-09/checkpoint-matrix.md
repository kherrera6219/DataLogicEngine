# Phase 9 Checkpoint Matrix

| Checkpoint | Engineering result | Installed result |
|---|---|---|
| CP9-A Durable jobs | PostgreSQL authority, Redis content-free coordination, app-owned pre-acquisition, restart/idempotency and lifecycle tests pass | Rebuilt backend/Electron restart and recovery drill pending |
| CP9-B Cross-store consistency | Expected-revision completion, scanner, repair, retry, update, and divergence tests pass | Populated PostgreSQL/Neo4j/Chroma/S3 parity drill pending |
| CP9-C Security | Hostile path, link/reparse, device/UNC, special-file, archive, decompression, signature, binary, and content-defense tests pass | Packaged hostile-corpus acceptance pending |
| CP9-D Causal retrieval | Authority/revision/permission/defense checks and source-change causality tests pass | Rebuilt installed source-to-answer causal E2E remains release-blocking |
| CP9-E Deletion | Reference-aware corpus and provenance-linked memory deletion tests pass | Installed deletion/reingest/recovery drill pending |

Phase 9 is an engineering checkpoint, not a full phase exit. No pending installed
result is represented as passed.
