# ADR-0006: Memory Authority and Trust-State Boundary

## Metadata

| Field | Value |
|---|---|
| Status | Accepted for Phase 9 implementation |
| Date | 2026-07-13 |
| Decision owner | Kevin |
| Plan authority | Phase 9, section 17.4 |
| Working-memory schema | `unified-memory.v2` |

## Context

DataLogicEngine had several components called memory with overlapping wording but
different persistence and trust behavior. UnifiedMemory JSON could retain query
and layer output across sessions without a validation-state boundary. TruthMemory
combined audit, cache, metrics, and artifacts. PostgreSQL `MemoryEntry`, chat and
trace rows, Neo4j, ChromaDB, Redis, and the USKD NetworkX graph each held related
state. Without an explicit authority map, unvalidated working output could be
mistaken for trusted knowledge or deleted from only one representation.

## Decision

1. PostgreSQL is the durable authority for users, sessions, chat, runs, traces,
   validation, audit, ingestion jobs, corpus revisions, and structured session
   memory records.
2. TruthMemory is audit/explainability behavior over PostgreSQL authority,
   required object artifacts, and a disposable Redis cache. It is not a second
   answer-memory authority.
3. Ingested knowledge is authorized by completed PostgreSQL corpus revisions.
   Neo4j, ChromaDB, and the S3-compatible object store are required, revisioned
   materializations. Retrieval fails closed when their vector metadata does not
   match an eligible PostgreSQL revision.
4. UnifiedMemory JSON is a bounded, versioned working-reasoning graph. Working
   entries are visible only within the originating session. They cannot become
   cross-session trusted recall merely because they were persisted.
5. Cross-session UnifiedMemory recall requires `validation_state=validated`, a
   source run identity, `policy_result=release_authorized`, and a retention class.
   Only the release-authorized L10 commit path may create that state.
6. `unified-memory.v2` adds explicit trust metadata and an integrity hash. Legacy
   v1 vertices migrate as `working` and `legacy_working_only`; migration never
   upgrades them to trusted memory.
7. UnifiedMemory supports owner review, export, deletion, bounded compaction, and
   recovery only from an integrity-verified last-known-good backup.
8. Redis memory/cache state is disposable coordination. The USKD NetworkX graph
   is a bounded working materialization loaded from a recorded durable graph
   revision. Neither can silently replace durable authority.
9. Source/user deletion must reconcile PostgreSQL, Neo4j, ChromaDB, object
   artifacts, UnifiedMemory, chat/trace records, and cache state through the
   existing deletion and reconciliation contracts.

## Alternatives considered

1. Treat every component named memory as an equal authority. Rejected because
   conflicts and partial deletion cannot be resolved deterministically.
2. Promote every completed TruthCore layer result to trusted recall. Rejected
   because completion is not governed output validation or release authority.
3. Delete UnifiedMemory and use only relational rows immediately. Rejected for
   Phase 9 because the bounded structured working graph is still used by active
   TruthCore workflows; its role can be narrowed without inventing a replacement
   during this phase.
4. Trust legacy JSON vertices during migration. Rejected because their source,
   policy, and validation state cannot be reconstructed safely.

## Consequences

- Existing v1 UnifiedMemory data remains available for owner review but becomes
  working-only until a new release-authorized run produces trusted memory.
- A malformed or hash-mismatched primary memory file does not load. A verified
  backup may restore it; otherwise the service fails or starts empty according
  to the configured strictness.
- Working-memory compaction never automatically removes validated entries.
- Knowledge and Graph UI state must distinguish working memory, validated memory,
  pending materializations, divergence, deletion, and recovery.

## Implementation references

- `backend/memory/unified_memory_service.py`
- `backend/routes/memory_routes.py`
- `backend/governed_execution/retrieval.py`
- `backend/ingestion/reconciliation.py`
- `backend/storage/data_contracts.py`
- `backend/storage/store_migration_adapters.py`
- `tests/memory/test_unified_memory_service.py`
- `tests/unit/test_phase9_memory_authority.py`

## Supersedes / superseded by

- Supersedes: none
- Superseded by: none
