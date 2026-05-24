# Local Release Evidence

Date: 2026-05-23

## Repo-Verifiable Commands

| Command | Result | Notes |
| --- | --- | --- |
| `python scripts/dev_doctor.py --skip-ports` | Passed | Warnings: not running inside a virtual environment; `templates/` directory is missing. Action item: initialize local schema via `scripts/windows/start_local_stack.ps1`. |
| `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process` | Passed | Strict mode reports 0 blockers and 0 action items after local SQLite schema initialization. Warnings remain: not running inside a virtual environment; `templates/` directory is missing. |
| `python scripts/verify_lockfiles.py` | Passed | Report written to `reports/lockfile_governance_report.json`. |
| `python scripts/verify_docs_references.py` | Passed | Documentation references are valid after the TODO and README consolidation. |
| `python scripts/validate_schema_parity.py` | Passed | Report written to `reports/schema_parity_report.json`. |
| `python scripts/verify_release_governance.py` | Passed | Report written to `reports/release_governance_report.json`. |
| `python -m py_compile models.py backend\llm_gateway\api.py backend\llm_gateway\gateway.py sdk\UKG_Python_SDK\ukg_sdk\__init__.py tests\unit\test_models_extended.py` | Passed | Phase 1 gateway/model contract and SDK version files compile. |
| `python -c "import sys; sys.path.insert(0, r'sdk\UKG_Python_SDK'); import ukg_sdk; print(ukg_sdk.__version__)"` | Passed | Printed `0.4.0`; SDK now has a single version assignment. |
| `python -m pytest tests\unit\test_models.py tests\unit\test_models_extended.py tests\integration_routes\test_api_routers.py -q` | Passed | 43 tests passed after adding API-key expiration and chat-session serialization coverage. |
| `python -m pytest tests\integration\test_gateway_api_coverage.py tests\unit\test_llm_gateway_internal_units.py -q` | Passed | 23 tests passed for gateway API/internal behavior. |
| `python -m pytest tests\unit\test_uskd_memory_graph.py tests\unit\test_storage_hardening.py -q` | Passed | 13 tests passed for the Phase 2 NetworkX graph and GraphStore cached traversal helpers. |
| `python -m pytest tests\truth_engine\test_layer10_emergence.py tests\truth_engine\test_truth_engine_coverage.py -q` | Passed | 15 tests passed for L10 Lane B graph persistence and TruthCore coordinate-vector graph context extraction. |
| `python -m ruff check app.py backend\storage\uskd_memory_graph.py backend\storage\graph_store.py backend\truth_engine\truth_core\engine.py backend\truth_engine\truth_core\emergence_controller.py core\simulation\layer2_knowledge.py core\coordinate_system.py scripts\sync_nodes_to_neo4j.py tests\unit\test_uskd_memory_graph.py tests\unit\test_storage_hardening.py tests\truth_engine\test_layer10_emergence.py tests\truth_engine\test_truth_engine_coverage.py` | Passed | Phase 2 touched Python files pass Ruff. |
| `python -m py_compile app.py backend\storage\uskd_memory_graph.py backend\storage\graph_store.py backend\truth_engine\truth_core\engine.py backend\truth_engine\truth_core\emergence_controller.py core\simulation\layer2_knowledge.py core\coordinate_system.py scripts\sync_nodes_to_neo4j.py tests\unit\test_uskd_memory_graph.py tests\unit\test_storage_hardening.py tests\truth_engine\test_layer10_emergence.py tests\truth_engine\test_truth_engine_coverage.py` | Passed | Phase 2 touched Python files compile. |
| `python -c "import app; print('app-import-ok')"` | Passed | Startup imports with USKD memory graph initialization; local Neo4j was unreachable, so live parity remains environment evidence. |
| `python -c "from backend.storage import UskdMemoryGraph, get_uskd_memory_graph; g=get_uskd_memory_graph(); print(type(g).__name__)"` | Passed | Printed `UskdMemoryGraph`; storage package exports the Phase 2 graph singleton. |

## Phase 1 / A Local Code Evidence

Completed locally on 2026-05-24:

- SDK duplicate `__version__` assignment removed; `ukg_sdk.__version__` resolves to `0.4.0`.
- `ExternalAPIKey.expires_at` is modeled, serialized, and enforced by `verify_key()`.
- API-key creation persists a Python datetime expiration instead of assigning a SQL expression to an unmapped attribute.
- `ChatSession.to_dict()` exists for gateway/tracing session list endpoints.
- Gateway-created `TraceRun` records set `user_id`, allowing authenticated trace-list views to see chat-generated runs.

## Phase 2 / DB-N Local Code Evidence

Completed locally on 2026-05-24:

- Added `backend/storage/uskd_memory_graph.py`, a NetworkX-backed in-memory graph for the active USKD substrate.
- Added SQL and Neo4j loaders, search, bounded neighborhood traversal, graph stats, coordinate anchor lookup, authorized upsert, and singleton access through `backend.storage`.
- Added `scripts/sync_nodes_to_neo4j.py` for idempotent SQL `KnowledgeGraphNode`/`KnowledgeGraphEdge` sync into Neo4j `KnowledgeNode` relationships.
- Added `GraphStore` cached query, coordinate lookup, subgraph traversal, and idempotent merge helpers.
- Wired `app.py` startup to load the SQL graph, optionally sync SQL to Neo4j with `USKD_SYNC_NEO4J_ON_STARTUP=true`, then refresh from Neo4j when available.
- Wired TruthCore to populate graph context from text and the 17-axis coordinate vector after intent parsing.
- Wired Layer 2 to prefer live NetworkX subgraph links and retain static fallback for empty local graphs.
- Wired CrosswalkTraversal to attempt cached Neo4j traversal before static fallback.
- Wired L10 Lane B to persist release-authorized knowledge into the NetworkX graph and Neo4j merge helpers after the promotion gate authorizes commit.
- Added `networkx` to `backend.spec` hidden imports.
- Local validation proves code paths and fallbacks. Live Neo4j count parity still requires a reachable Neo4j instance with valid credentials and seeded data.

## Release-Runner Or Manual Evidence Still Required

1. Review current CI results for the release branch or tag.
2. Review security scan output for the release branch or tag.
3. Produce signed installer artifacts through `.github/workflows/release-installer-signing.yml`.
4. Attach code-owner approval, rollback plan, disaster recovery review, and artifact signing evidence to the release ticket.
