# Memory authority matrix

| Field | Value |
|---|---|
| Status | Authoritative for operator-visible working memory |
| Date | 2026-08-12 |
| Code | `backend/memory/authority.py`, `backend/memory/unified_memory_service.py` |

## Operator-visible memory

| Concern | System of record | API |
|---|---|---|
| Working memory review / export / compact / recover | `UnifiedMemoryService` | `/api/v1/memory/*` |
| Run evidence, stages, claims, export bundles | Trace graph (`TraceRun` et al.) | `/api/v1/trace/*` |
| Vector retrieval materialization | Chroma (app-owned) | Ingestion + governed retrieval (not memory CRUD) |

## Rules

1. Settings **Memory** controls must call `/api/v1/memory/*` only.
2. Truth Engine UI telemetry uses **trace** data, not a second memory writer.
3. Do not reintroduce dual write paths without updating this document and `authority.py`.
