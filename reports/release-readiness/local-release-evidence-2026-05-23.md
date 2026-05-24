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
| `python -m pytest tests\unit\test_uskd_memory_graph.py -q` | Passed | 3 tests passed for the Phase 2 NetworkX-backed USKD memory graph foundation. |
| `python -c "from backend.storage import UskdMemoryGraph, get_uskd_memory_graph; g=get_uskd_memory_graph(); print(type(g).__name__)"` | Passed | Printed `UskdMemoryGraph`; storage package exports the Phase 2 graph singleton. |

## Phase 1 / A Local Code Evidence

Completed locally on 2026-05-24:

- SDK duplicate `__version__` assignment removed; `ukg_sdk.__version__` resolves to `0.4.0`.
- `ExternalAPIKey.expires_at` is modeled, serialized, and enforced by `verify_key()`.
- API-key creation persists a Python datetime expiration instead of assigning a SQL expression to an unmapped attribute.
- `ChatSession.to_dict()` exists for gateway/tracing session list endpoints.
- Gateway-created `TraceRun` records set `user_id`, allowing authenticated trace-list views to see chat-generated runs.

## Phase 2 / DB-N Local Code Evidence

Started locally on 2026-05-24:

- Added `backend/storage/uskd_memory_graph.py`, a NetworkX-backed in-memory graph for the active USKD substrate.
- Added loaders for SQL-style records and Neo4j query results.
- Added search, bounded neighborhood traversal, graph stats, and singleton access through `backend.storage`.
- Added unit coverage for record loading, Neo4j loading, traversal, search, stats, and singleton export.

## Release-Runner Or Manual Evidence Still Required

1. Review current CI results for the release branch or tag.
2. Review security scan output for the release branch or tag.
3. Produce signed installer artifacts through `.github/workflows/release-installer-signing.yml`.
4. Attach code-owner approval, rollback plan, disaster recovery review, and artifact signing evidence to the release ticket.
