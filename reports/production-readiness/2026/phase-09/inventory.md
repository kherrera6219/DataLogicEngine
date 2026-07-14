# Phase 9 Live Subsystem Inventory

Date: 2026-07-13; closure reconciled 2026-07-14

Status: **Preserved before-state inventory plus verified engineering closure.
This is not installed acceptance evidence.**

## Acquisition and entry points

- Electron issues one-use ingestion path capabilities in
  `frontend/electron/main.ts`, consumes them in the main process, and signs the
  loopback ingestion request with the `ingestion` desktop IPC capability.
- Flask exposes supported-types, history, synchronous start, asynchronous start,
  and status routes in `backend/routes/ingestion_routes.py`.
- The owner settings surface is
  `frontend/components/settings/KnowledgeIngestionSettings.tsx`.
- Before Phase 9 work, the backend parsed the selected source path directly,
  accepted types primarily by extension, followed normal filesystem traversal,
  and bounded only individual file size.
- The first Phase 9 batch adds app-owned staging, local-path enforcement,
  link/reparse and Windows device-name rejection, content-signature checks,
  binary-text rejection, source hashes, per-file/total-job/file-count limits,
  and cleanup on success/failure.

## Job and persistence truth

- `LocalKnowledgeIngestionService.ingest_path_async()` currently uses a daemon
  Python thread and module-local `_ASYNC_STATUS`; state is lost on backend or
  Electron restart.
- History currently reads JSON manifests from a local filesystem directory.
- There are no PostgreSQL ingestion job, file, chunk, attempt, error, or
  checkpoint authorities yet.
- Pause, resume, durable cancel, retry, lease recovery, and restart reconciliation
  are not implemented.
- This is the first CP9-A closure target; no restart-safety claim is permitted.

## Cross-store indexing

- `KnowledgeGraphNode` rows are PostgreSQL-authoritative and ingestion enqueues
  Chroma and Neo4j materializations through `CrossStoreOutbox`.
- Stable chunk IDs are content-hash based, but document identity and source
  revision are embedded only in node metadata. Identical chunks across distinct
  documents collapse, losing document-specific provenance.
- Ingestion does not persist approved original/normalized source artifacts in
  the app-owned S3 service.
- A job becomes `materialization_pending`, but no ingestion-specific scanner
  reconciles PostgreSQL, Neo4j, Chroma, and S3 into a completed corpus revision.
- Update/delete/reingest reconciliation and corpus repair controls are missing.

## Retrieval and causal use

- Canonical governed retrieval is in
  `backend/governed_execution/retrieval.py`; vector, graph, source permission,
  revision, rejected-source, and selected-context parity require Phase 9 review.
- Existing graph/vector adapters and outbox materialization are reusable, but no
  installed test yet proves that a source change changes citations, validation,
  or the governed answer.

## Memory authorities

- The ownership registry still labels the local JSON unified memory graph as a
  legacy authority pending Phase 9 consolidation.
- PostgreSQL `MemoryEntry`, TruthMemory, UnifiedMemoryService, structured local
  memory, Redis cache, graph state, and chat/trace memory records overlap without
  one complete promotion/conflict/deletion contract.
- Unvalidated provider output promotion, poisoning defense, compaction,
  corruption recovery, and cross-memory deletion remain open.

## UI truth

- The settings ingestion surface exposes the picker, per-file limit, async flag,
  Neo4j flag, history, and coarse counts.
- The first Phase 9 batch adds explicit total-job and file-count controls.
- Current history is correctly manifest-backed but not PostgreSQL job-backed;
  progress is not per-file/per-store and graph/knowledge repair controls remain
  open.

## First ordered implementation targets

1. PostgreSQL job/file/chunk/attempt/checkpoint authority and migrated history.
2. Redis queue, lease, cancellation, event, and restart reconciliation.
3. S3 original/normalized artifact contract with hashes and retention metadata.
4. Document-scoped stable IDs plus cross-store corpus revision scanner/repair.
5. Causal retrieval and delete/update/reingest tests.
6. Memory authority ADR/contract and truthful Knowledge/Graph controls.

## Closure reconciliation

All six ordered targets above are implemented at the source/engineering
boundary:

- PostgreSQL owns ingestion jobs, files, chunks, attempts, checkpoints, source
  hashes, and revisions; Redis coordination is content-free and restart-safe.
- Source authority is app-owned after acquisition. Original and normalized
  artifacts are required hashed revisions in `knowledge-sources`.
- Document/chunk identity preserves document provenance. Completion requires
  PostgreSQL, Neo4j, Chroma, original-object, and normalized-object parity.
- Scanner/repair/update/retry and reference-aware cross-store plus memory
  deletion paths are implemented.
- Retrieval records considered/selected/rejected decisions, validates authority
  and revisions, applies diversity/budgets, and can include bounded graph context.
- ADR-0006 and UnifiedMemory v2 establish working/validated trust and owner
  review/export/delete/compact/recover actions.
- Knowledge, Graph, ingestion, memory, and run-detail controls expose live state.

The rebuilt-installed CP9 lifecycle and UI gates remain open as recorded in
`checkpoint-matrix.md`.
