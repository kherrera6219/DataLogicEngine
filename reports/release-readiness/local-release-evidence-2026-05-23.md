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
| `python scripts\validate_phase1_provider_staging.py --provider openai --model gpt-4.1-mini --reset-database` | Passed | Live provider-backed Phase 1 staging evidence: `IS_DESKTOP_APP=true`, provider/model `openai / gpt-4.1-mini`, Tier `T2`, `[UKG Audit Trace]` footer present, and `TruthAuditEvent` rows `0 -> 1`; report written to `reports/phase1_provider_staging_report.json`. |
| `powershell -ExecutionPolicy Bypass -File .\scripts\windows\run_packaging_smoke.ps1 -RepoRoot C:\software\DataLogicEngine -Mode installer` | Passed | Packaged desktop smoke: portable launch started and stayed running until timeout; silent install/uninstall succeeded; installer SHA256 captured. Signature status is `NotSigned`, so signing remains an open release gate. |
| `powershell -ExecutionPolicy Bypass -File .\scripts\windows\verify_installer_signature.ps1 -RequireArtifacts -CheckRevocation` | Failed as expected | Confirms the current local installer is unsigned: `DataLogicEngine Setup Latest.exe: NotSigned`. This blocks A-2 until trusted signing credentials and CI signing evidence exist. |
| `python -m pytest tests\unit\test_uskd_memory_graph.py tests\unit\test_storage_hardening.py -q` | Passed | 13 tests passed for the Phase 2 NetworkX graph and GraphStore cached traversal helpers. |
| `python -m pytest tests\truth_engine\test_layer10_emergence.py tests\truth_engine\test_truth_engine_coverage.py -q` | Passed | 15 tests passed for L10 Lane B graph persistence and TruthCore coordinate-vector graph context extraction. |
| `python -m ruff check app.py backend\storage\uskd_memory_graph.py backend\storage\graph_store.py backend\truth_engine\truth_core\engine.py backend\truth_engine\truth_core\emergence_controller.py core\simulation\layer2_knowledge.py core\coordinate_system.py scripts\sync_nodes_to_neo4j.py tests\unit\test_uskd_memory_graph.py tests\unit\test_storage_hardening.py tests\truth_engine\test_layer10_emergence.py tests\truth_engine\test_truth_engine_coverage.py` | Passed | Phase 2 touched Python files pass Ruff. |
| `python -m py_compile app.py backend\storage\uskd_memory_graph.py backend\storage\graph_store.py backend\truth_engine\truth_core\engine.py backend\truth_engine\truth_core\emergence_controller.py core\simulation\layer2_knowledge.py core\coordinate_system.py scripts\sync_nodes_to_neo4j.py tests\unit\test_uskd_memory_graph.py tests\unit\test_storage_hardening.py tests\truth_engine\test_layer10_emergence.py tests\truth_engine\test_truth_engine_coverage.py` | Passed | Phase 2 touched Python files compile. |
| `python -c "import app; print('app-import-ok')"` | Passed | Startup imports with USKD memory graph initialization. |
| `python -c "from backend.storage import UskdMemoryGraph, get_uskd_memory_graph; g=get_uskd_memory_graph(); print(type(g).__name__)"` | Passed | Printed `UskdMemoryGraph`; storage package exports the Phase 2 graph singleton. |
| `docker compose up -d neo4j` | Passed | Started DataLogicEngine-local Neo4j as `ukg-neo4j` on host ports `7476` and `7690` to avoid existing local stack conflicts. |
| `python scripts/seed_neo4j.py --wipe` | Passed | Seeded the configured local Neo4j instance with 20 `Pillar` nodes and 18 `HONEYCOMB_BRIDGE` edges. |
| `python -c "import app; from backend.storage import get_uskd_memory_graph; print(get_uskd_memory_graph().stats().to_dict())"` | Passed | App startup refreshed the USKD memory graph from Neo4j: 20 nodes, 18 edges, 20 pillar nodes. |
| `python -m pytest tests\unit\test_axis_alignment.py -q` | Passed | 6 tests passed for Phase B canonical axis names, Axis 14-17 managers, CoordinateResolver contexts, Axis 17 FROST bridge, SDK offline taxonomy resolver, legacy metadata storage, and TraceRun FROST fields. |
| `python -m ruff check core\coordinate_system.py core\axes\axis_system.py core\axes\axis14_acquisition_lifecycle.py core\axes\axis15_risk_threat.py core\axes\axis16_ethics_trust.py core\axes\axis17_frost_mode.py backend\truth_engine\truth_core\engine.py models.py sdk\UKG_Python_SDK\ukg_sdk\coordinates17.py tests\unit\test_axis_alignment.py` | Passed | Phase B touched Python files pass Ruff. |
| `python -m py_compile core\coordinate_system.py core\axes\axis_system.py core\axes\axis14_acquisition_lifecycle.py core\axes\axis15_risk_threat.py core\axes\axis16_ethics_trust.py core\axes\axis17_frost_mode.py backend\truth_engine\truth_core\engine.py models.py sdk\UKG_Python_SDK\ukg_sdk\coordinates17.py tests\unit\test_axis_alignment.py` | Passed | Phase B touched Python files compile. |
| `DATABASE_URL=sqlite:///reports/phase_b_migration.sqlite python -m flask db upgrade` | Passed | Temporary SQLite migration smoke ran all Alembic revisions through `e2f3a4b5c6d7`; `trace_runs` contained `frost_depth` and `truth_engine_mode`; temporary DB was removed after verification. |

## Phase 1 / A Local Code Evidence

Completed locally on 2026-05-24. Closed for the local-first desktop target on 2026-05-25; see `reports/release-readiness/local-first-phase1-completion-2026-05-25.md`.

- SDK duplicate `__version__` assignment removed; `ukg_sdk.__version__` resolves to `0.4.0`.
- `ExternalAPIKey.expires_at` is modeled, serialized, and enforced by `verify_key()`.
- API-key creation persists a Python datetime expiration instead of assigning a SQL expression to an unmapped attribute.
- `ChatSession.to_dict()` exists for gateway/tracing session list endpoints.
- Gateway-created `TraceRun` records set `user_id`, allowing authenticated trace-list views to see chat-generated runs.
- Provider-backed staging validation is complete for a live OpenAI call: the gateway returned Tier `T2`, added the `[UKG Audit Trace]` footer, created a `TraceRun`, and committed a hash-chained `TruthAuditEvent` row in SQLite.
- Installer-mode packaging smoke is complete for the current unsigned artifact: install/uninstall succeeded, portable launch stayed alive until the smoke timeout, and Electron source sets `IS_DESKTOP_APP=true` plus the per-user `ukg_database.db` SQLite path.

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
- Local validation proves code paths and fallbacks. A DataLogicEngine-local Neo4j container is configured via ignored `.env`, seeded, and verified with 20 pillar nodes and 18 graph edges. SQL `KnowledgeGraphNode` parity still depends on initializing the local SQL graph tables.

## Phase B / Axis Alignment Local Code Evidence

Completed locally on 2026-05-25:

- Updated `UnifiedCoordinate.AXIS_NAMES` and coordinate resolver contexts so Axes 14-17 use Acquisition Lifecycle, Risk & Threat Context, Ethics/Trust/Criticality, and FROST-Mode Selector.
- Added dedicated canonical axis managers for Axis 14-17 and registered them in `AxisSystem`.
- Wired Axis 17 FROST mode context into `TruthCoreEngine.get_workflow_steps()`.
- Added `TraceRun.frost_depth` and `TraceRun.truth_engine_mode` with an Alembic migration using `batch_alter_table`.
- Kept legacy provenance/object type/validation/security concepts in `KnowledgeGraphNode.node_metadata["legacy_axis_metadata"]`.
- Updated the SDK `CoordinateResolver17` to use bundled offline JSON taxonomy files.
- Added `tests/unit/test_axis_alignment.py` to lock the aligned definitions and resolver behavior.

## Phase 4 / DB-C Validation Evidence

Validated on 2026-05-25:

- `python -m pytest tests\unit\test_vector_store_unit.py tests\unit\test_services.py -q` passed with 29 tests.
- DB-C remains open. VectorStore and RAG unit support are present, but the ingestion script, startup background indexing, TruthCore Chroma retrieval wiring, local/offline `sentence-transformers` packaging, and Electron IPC Chroma counts are not implemented.
- First implementation step is collection-name alignment: DB-C and `backend/storage/vector_store.py` use `knowledge_nodes`, while `backend/services/rag_service.py` currently uses `knowledge_graph`.

## Release-Runner Or Manual Evidence Still Required

These gates are required for public production release artifacts, not for local-first desktop completion.

1. Review current CI results for the release branch or tag.
2. Review security scan output for the release branch or tag.
3. Complete NVDA manual validation against the packaged Windows executable.
4. Produce signed installer artifacts through `.github/workflows/release-installer-signing.yml`.
5. Attach code-owner approval, rollback plan, disaster recovery review, and artifact signing evidence to the release ticket.
