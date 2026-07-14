# Phase 9 Requirements Traceability

| Plan work package | Primary implementation | Primary evidence |
|---|---|---|
| 17.1 Secure acquisition and lifecycle | `backend/ingestion/acquisition.py`, `jobs.py`, `job_coordination.py`, `local_ingestion.py`, `backend/security/content_defense.py`, Electron picker IPC | `tests/unit/test_phase9_secure_acquisition.py`, `test_phase9_parser_limits.py`, `test_phase9_content_defense.py`, `test_phase9_ingestion_jobs.py` |
| 17.2 Cross-store indexing | ingestion models/migration, reconciliation service, materialization dispatcher, data contracts | `tests/storage/test_cross_store_reconciliation.py`, migration and ingestion tests |
| 17.3 Retrieval and graph use | governed retrieval, orchestrator/prompt, RAG service, graph/USKD stores | `tests/governed_execution/test_phase9_retrieval_authority.py`, graph route and USKD tests |
| 17.4 Memory model | UnifiedMemory service, memory owner routes, ADR-0006 | `tests/unit/test_phase9_memory_authority.py`, `tests/memory/test_unified_memory_service.py`, memory API tests |
| 17.5 Knowledge and Graph UI | Graph/Knowledge pages, ingestion and memory settings, run detail, typed clients | frontend ingestion, knowledge, memory, and component tests plus production build |
