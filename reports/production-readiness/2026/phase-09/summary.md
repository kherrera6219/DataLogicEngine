# Phase 9 Engineering Checkpoint Summary

Date: 2026-07-14

Status: **Engineering checkpoint complete; installed exit gates retained.**

## Outcome

Phase 9 makes local knowledge acquisition, ingestion, multi-store indexing,
retrieval, graph use, and memory ownership durable, bounded, reconcilable, and
causally connected to `governed.v1` at the source/engineering boundary.

## Delivered

- Bounded app-owned acquisition before parsing, with Windows path/reparse/
  device/UNC/special-file containment, content signatures, archive and
  decompression limits, page/file/byte/time budgets, and `content-defense.v1`.
- PostgreSQL ingestion job/file/chunk/attempt/checkpoint authority and Redis
  content-free queue, lease, state, cancellation, and progress coordination.
- Required hashed original and normalized artifacts in the eighth object bucket,
  `knowledge-sources`.
- PostgreSQL/Neo4j/Chroma/S3 expected-revision completion, consistency scanning,
  repair, retry, update, and reference-aware deletion including memory cleanup.
- Authority-validated causal retrieval with deterministic source diversity and
  budgets, persisted considered/selected/rejected decisions, and bounded graph
  context.
- ADR-0006 and UnifiedMemory v2 working-versus-validated trust, release-only
  promotion, integrity/recovery, review, export, delete, and compaction.
- Truthful Knowledge, Graph, ingestion, memory, and run-detail controls.

## Validation

- Backend: **2,033 passed, 18 skipped**.
- Frontend: **83 files / 407 tests passed**.
- Focused Phase 9 retrieval, graph, memory, and ingestion contracts: **38 passed**.
- Frontend TypeScript, ESLint, and production Next.js build: passed.
- Ruff and Python compilation: passed.
- Alembic head: `c8d9e0f1a2b3`.
- Ownership registry: 77 PostgreSQL entities and 30 logical data contracts.

## Retained gates

This checkpoint does not approve production release. The rebuilt application
must still prove restart/recovery, populated-store parity, hostile-corpus
containment, causal answer behavior, deletion, and packaged Knowledge/Graph UI.
Earlier installed gates, Dependabot alert 389, independent reviews, signing,
and final object-store Replacement Control remain open. SeaweedFS is still a
candidate only; MinIO remains the product-specific production architecture.
