# DataLogicEngine TODO

**Last updated:** 2026-06-19 (**A16 Priority 2 in progress** — frontend component coverage remains **80.06%+** and the newest accessibility pass extends labelled controls, landmarks, and busy/error semantics into `ProjectDetail`, `ApiOverlayConfig`, and `McpServerConfig`, with matching test coverage updates. Recent work already covered API + telemetry tests, app error/loading surfaces, DatabaseSettings, and Tier 1/Tier 2 a11y follow-through on `ChatInterface`, `DetailedResponseView`, `MessageBubble`, `CommandBar`, `AiModelSettings`, `KnowledgeIngestionSettings`, and `McpClientConfig`. **NEXT:** continue the remaining A16 accessibility sweep, prioritizing the remaining settings/admin/project surfaces that still lack explicit ARIA/keynav review.)
**Status:** Canonical planning source

This is the canonical active TODO list for repository release readiness and operational work. `UKG_DataLogicEngine_Master_Completion_Plan_v1.txt` is the current phased execution plan for the broader UKG/DataLogicEngine completion roadmap; keep release go/no-go items mirrored here when they affect the current shipping branch.

## Unified Backlog

Review date: 2026-05-23

No standalone `ROADMAP.md` file exists in the repository. The only roadmap-style source found during the May 22 review was `docs/archive/historical-documents/MVP Plan_ Universal Knowledge Graph (UKG) System.pdf`; actionable current and future work is consolidated below.

### Production Code Review Remediation

Source report: `reports/production-code-review-2026-05-23.md`

Validation status: Production code-review remediation phases 1 through 4 are complete as of 2026-05-23.

Master completion plan status: Phase 1 / A is complete for the local-first desktop target as of 2026-05-25. Phase 2 / DB-N local implementation and Phase B / Axis Alignment are also complete. NVDA screen-reader pass, trusted production signing, final CI/security/code-owner/rollback/DR release evidence remain production/public release gates, not local-first blockers. Phase 2 live Neo4j is configured locally through ignored `.env`, seeded, and verified; SQL graph-node parity still depends on initializing the local SQL graph tables.

CI/security update, 2026-05-28: dependency-alert remediation and backend CI regression fixes are pushed to `main` in `edbf0127`. Local validation passed `python -m pytest -q` (`1717 passed, 21 skipped`), targeted ruff/py_compile checks, and the commit hook's ruff/frontend lint/frontend typecheck. GitHub Security Scan passed on `edbf0127`; CI/CD and Deploy were rerunning on that head when this document was updated.

| Item | Code validation | Status |
| --- | --- | --- |
| API gateway authentication | `backend/api_gateway/api_gateway.py` validates signed JWT bearer tokens, required expiration, optional issuer/audience, and optional roles. | Done |
| Migration-first deployment | `scripts/deploy.py` runs `python -m flask db upgrade` through Flask-Migrate/Alembic. | Done |
| Trusted proxy and host validation | `app.py` gates `ProxyFix` behind `TRUST_PROXY_HEADERS=true`, enforces `TRUSTED_HOSTS`, and no longer trusts raw `X-Forwarded-Proto` for HTTPS redirects. | Done |
| Multimodal upload hardening | `backend/routes/multimodal_routes.py` validates route-specific size, extension, content signatures, sanitized filenames, inferred MIME types, and normalized public errors before processing. | Done |
| Security scan API protection | `backend/security_scan_api.py` requires admin authentication on scan/compliance endpoints and normalizes public 500 errors. | Done |
| Legacy fallback secrets | `backend/__init__.py` keeps deterministic defaults under pytest only and fails fast outside tests when secrets are missing. | Done |
| Shell-based static copy | `scripts/deploy.py` copies static build artifacts with `pathlib`/`shutil` and no shell invocation. | Done |
| Strict runtime precheck | `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process` passes with no blockers and no action items. | Done |
| Phase 1 gateway/model contract drift | `ChatSession.to_dict()` exists; API key expiration is modeled/enforced; gateway-created `TraceRun` rows set `user_id`; SDK version has a single `0.4.0` assignment. | Done |
| Phase 1 provider-backed staging | `scripts/validate_phase1_provider_staging.py` runs a live-provider Tier 2 gateway request with `IS_DESKTOP_APP=true` and verifies the audit footer plus a SQLite `TruthAuditEvent` row. | Done |
| Phase 1 installer smoke | `scripts/windows/run_packaging_smoke.ps1 -Mode installer` verifies packaged portable launch plus silent installer/uninstaller behavior; Electron source sets desktop mode and the per-user SQLite database path. | Done |
| Phase 1 local-first closure | `reports/release-readiness/local-first-phase1-completion-2026-05-25.md` separates completed local-first desktop gates from production/public release evidence gates. | Done |
| Phase 2 USKD memory graph implementation | `backend/storage/uskd_memory_graph.py`, `scripts/sync_nodes_to_neo4j.py`, `GraphStore` cached traversal helpers, TruthCore graph context bootstrap, Layer 2 live graph preference, L10 Lane B authorized graph commit, and `backend.spec` NetworkX hidden import are implemented and locally validated. | Done |
| Phase B axis alignment | Axes 14-17 now use the canonical Acquisition Lifecycle, Risk & Threat Context, Ethics/Trust/Criticality, and FROST-Mode Selector definitions across coordinate system, axis managers, SDK resolver, TraceRun, and tests. | Done |
| Phase 4 / DB-C Chroma wiring | `knowledge_nodes` collection naming is aligned; `scripts/index_knowledge_nodes.py` indexes SQL nodes; startup can background-index empty local desktop collections; `/health` and Electron IPC expose Chroma counts; L3/L8/L9/L10 use DB-C retrieval/indexing; persona_profiles cache path and sentence-transformers packaging are in place. | Done |
| Phase 5 / DB-R Redis TruthCache persistence | TruthCache supports Redis HSET/HGET persistence with memory fallback; TruthMemoryManager auto-selects Redis when `USE_REDIS=true`; GraphStore subgraph and RAG embedding caches can use Redis; `/health` and Electron IPC expose `redis_ping_ms`. | Done |
| Phase C Integration Bridge + LocalSLM | Gateway quad mode reaches `PodOrchestrator` and records pod status; TruthCore L5 constructs 7-part personas for axes 8-11 and uses pod expansion; KA-038, PersonaEnhancer, DRL refinement, JSON-safe weights, desktop LocalSLM fallback, and `quadAnalysisStatus` IPC are wired. | Done |
| Phase DB-P SQL historical reasoning calibration | L8 calibrates confidence thresholds from 90-day TraceRun history by risk domain; TruthSession stores local deterministic input embeddings; L9 returns `db_similar_sessions` historical drift baselines; KA execution timing is persisted and KA-036 reads p95 latency from the last 100 executions. | Done |

Remaining phase validation update: 2026-05-26

Next priority update: 2026-05-30. Phase H, KI local-first text-corpus ingestion, TV / Trace Viewer Wiring, the first KI productization slice, hardened KI end-to-end validation evidence, KI-6/KI-7 productization, Dependabot alert 389 remediation, and explicit KA stub replacement for KA-011, KA-033, KA-048, KA-077, KA-109, and KA-Master are implemented and locally validated. The next local implementation priority is a broader KA production-depth review for thin heuristic KAs that were not explicit stubs. Production release evidence and manual store/release tasks can run in parallel, but they should not block local-first productization unless the target is immediate public distribution.

Quad-persona consolidation update: 2026-06-05. Phases 4b, 5, and 6 are implemented and locally validated. Phase 5 fixed timezone-aware memory timestamps, deterministic persona confidence, stable text embedding seeds, reachable/configurable refinement thresholds, instance-isolated sufficiency configuration, and Axis 9/10 secondary influence mapping. Phase 6 wires the gateway-only `backend/quad_persona/quad_engine.py` path through `backend.llm_gateway`, adds a deterministic offline fallback, returns the gateway-consumed `perspectives`/string `synthesis` contract, and covers the path with non-monkeypatched regressions.

KA production-depth update: 2026-06-08. First model-ops KA batch is implemented and locally validated. `KA-084`, `KA-087`, `KA-089`, and `KA-090` now derive monitoring, versioning, pruning, and quantization outputs from supplied metrics/artifact/model metadata instead of canned placeholder values, and their constructor config overrides work with file-backed defaults. Continue the broader KA production-depth review with the remaining thin heuristic KAs.

Structural audit update: 2026-06-07. Sprints 1, 2, and 3 are complete. Routes audit completed 2026-06-07: 22 route files reviewed across `routes/` and `backend/routes/`; 20 issues identified; RT-1 through RT-18 sprint tasks defined. Complete remaining audit plan produced 2026-06-10: live scan of all 1,049-commit repo identified 32 audit areas across ~36 sessions; plan saved to `docs/audits/DataLogicEngine_Complete_Audit_Plan.md`. Sprint 1 eliminated duplicate class names, module name collisions, and misplaced files. Sprint 2 resolved all core→backend import inversions (`find_core_backend_inversions.py` reports 0 lines; `# inversion:ok` policy documented in `REPO_AUDIT_LOG.md`). Sprint 3 replaced all 5 stub `_check_*` compliance methods with real SOC 2 Type 2 runtime checks (SC-1 through SC-5) plus 25 unit tests. Full suite: 1855 passed / 21 skipped / 0 failures.

| Remaining phase | Live-code validation | Status |
| --- | --- | --- |
| Phase D / DSQP | `docs/ip/dsqp_technical_disclosure.md`, `backend/dsqp/`, local templates, DSQP chain/registry/orchestrator/validator, PersonaConstructionService DSQP fallback, TruthCore L5 context wiring, KA-012 DSQP profiles, SDK `DSQPClient`, PyInstaller template datas, Electron DSQP IPC, desktop persona cards, DSQP benchmark/report, and provider-backed `dsqp_chain` audit evidence are implemented. | Done for D-1..D-12 code/test/evidence scope; broader production packaging smoke remains under release evidence. |
| Phase E / L10 KA suite | `backend/knowledge_algorithms/l10/l10_ka_001..007` modules expose `.run` callables; `ka_registry.yaml` points at importable functions; KA-116 delegates entropy scoring to L10-KA-001; KA-014, KA-023, KA-002, and KA-022 have deterministic depth implementations; L10 modules are included in PyInstaller collection and covered by focused tests. | Done for E-0..E-14 code/test scope; broader production packaging smoke remains under release evidence. |
| KA explicit stub replacement sweep | `KA-011` now supports statistical, structural, and Bayesian summaries; `KA-033` is a functional extension slot; `KA-039` has z-score/IQR anomaly detection; `KA-048` performs deterministic typed entity extraction; `KA-077` adds local deterministic enrichment; `KA-109` reports local runtime/filesystem/registry/disk health; `KA-Master` selects and dispatches bounded KA flows instead of returning a canned path. | Done for the explicit stub/placeholder files identified in `backend/knowledge_algorithms`; focused tests pass. |
| DB-O / Object store + blockchain | `TruthAuditEvent` now has queryable object-store and anchor fields; `TruthMemoryCommitService` writes audit bundles to `audit_logs`, records object references, computes Merkle roots, and anchors Tier 3+ runs through BlockchainAdapter with local simulated anchors when no node/key is configured. `FROSTService` persists snapshots to `simulation_artifacts`, `DSQPChain` persists persona artifacts to `deliverables/dsqp`, and `/health` plus Electron `get-db-status` expose object-store bucket counts and byte totals. | Done for DB-O local-first desktop/VM scope. |
| DB-M / StructuredMemoryGraph | `backend/memory/unified_memory_service.py` wraps `StructuredMemoryGraph` with deterministic local embeddings, layer/persona namespacing, JSON persistence under `databases/memory/memory_graph.json`, recall/consolidation APIs, FROST branch checkpoints, and runtime stats. TruthCore recalls and writes memory for L1-L10 workflow steps, L10 Lane B records release-authorized knowledge into StructuredMemoryGraph, and `/health` plus Electron `get-db-status` expose memory counts/timestamps. | Done for DB-M local-first desktop/VM scope. |
| Phase F / DMRF | `backend/dmrf/` now contains the Python control-plane foundation: orchestrator/result models, 17-axis router, tier classifier, convergence/evidence policy, injection defense, TruthGate/TruthCore/TruthMemory/TruthLink adapters, Redis Streams publishing against the app-managed Redis service with in-memory fallback, FROST snapshots, DSQP persona construction, MLflow/local JSONL tracking, gateway `USE_DMRF` flag, Prometheus metrics, `dmrf-status` API/IPC, validation script, and focused integration tests. | Done for Phase F Python control-plane scope on the internal Windows app database model. Desktop and VM are treated as identical Windows app deployments; no external database source is required. Optional Rust F2 is not required unless VM profiling later shows a Python bottleneck. |
| Phase G / Enterprise integrations | G-A desktop-compatible scope is implemented: TruthMemory local MLflow/JSONL tracking, Rego policy file plus OPA subprocess/Python fallback evaluation in TruthGate, W3C PROV-JSON in TruthAuditEvent data, active MCP `sampling/createMessage`, MCP resource subscriptions with SSE stream route, and SDK v0.5.0 metadata with offline `DSQPClient` plus bundled taxonomy data. G-B optional VM enhancements are now implemented with TruthLink Redis Streams fallback, TruthMemory local retention archives, opt-in TruthGate enhanced screening, and ADR-0002 for PQ-gRPC research/no-go on desktop dependency. | Done for Phase G local-first desktop/VM scope. |
| Phase H / Desktop experience | H-1..H-15 local-first desktop scope is implemented: app-owned JRE setup/priority and installer resources; provider/local-model network status; signed Electron IPC for live reasoning progress and KA execution feed; trace panel active KA/persona confidence/FROST enrichment; detailed storage metrics; one-click backup archive; durable desktop offline queue/replay; DSQP and gateway LocalSLM audit metadata; backend health-gated splash startup and three-attempt restart recovery; PyInstaller desktop module inclusion; reproducible cold-start/packaging evidence in `reports/phase_h_desktop_evidence.json`. | Done for Phase H local-first desktop/VM scope. |
| KI / Knowledge ingestion | KI local-first scope is implemented: `backend/ingestion/` ingests supported local text files into chunk-level SQL `KnowledgeGraphNode` rows, scrubs prompt-injection markers, writes manifests, indexes chunks through existing `RAGService`/Chroma `knowledge_nodes`, exposes `POST /api/v1/ingestion/local`, adds `scripts/ingest_local_corpus.py`, surfaces citation metadata in RAG and TruthCore deep-research output, and records reproducible sample-corpus evidence in `reports/ki_ingestion_evidence.json`. KI productization slice 1 adds `/api/v1/ingestion/supported`, `/api/v1/ingestion/history`, and a Settings -> Knowledge UI for local path ingestion and manifest-backed history. The evidence script now validates extraction/scrubbing, chunking, SQL persistence/metadata, Chroma handoff, citation normalization, source-rendered context, and manifest output end to end. Richer PDF/DOCX/binary extractors, standard corpus loaders, async queue semantics, and SQL -> Neo4j sync evidence remain next enhancements. | Done for KI local-first text-corpus ingestion scope, productization slice 1, and end-to-end validation evidence; partly done for rich corpus/product workflow scope. |
| TV / Trace Viewer Wiring | `UKG_TraceViewer_Wiring_Plan_v3_1.docx` was reviewed against live code and completed locally. Gateway chat responses now expose structured trace links, `/api/v1/trace/runs/<run_id>/bundle` returns an aggregate bundle, chat messages show a lazy inline trace panel, trace-specific Socket.IO run rooms/events exist, trace serializers expose viewer aliases, and `/runs/view` consumes the same bundle contract. | Completed with local evidence in `reports/trace_viewer_wiring_evidence.json`; focused backend/frontend tests, typecheck, ruff, and docs reference validation pass. Browser smoke reached the local Next app but authenticated page rendering still requires backend/auth running on `127.0.0.1:5000`. |
| Quad-persona Phase 4b/5/6 | `core/persona/quad/` split the oversized `mathematical_framework`, `persona_scaling`, and `pod_orchestrator` modules into compatibility-exported packages, then fixed Phase 5 correctness bugs in memory timestamps, deterministic confidence, stable embeddings, refinement thresholds, sufficiency config isolation, and Axis 9/10 mapping. Phase 6 wires the gateway-only `backend/quad_persona` engine into `_run_quad_analysis` with deterministic offline fallback and gateway-compatible output shape. | Done for Phase 4b/5/6 code/test/docs scope. Focused quad tests, Group A, full pytest, ruff, docs reference validation, Bandit, and diff whitespace checks pass locally through Phase 5; Phase 6 focused tests and touched-path ruff pass locally. |

### Next Work Queue

1. [x] KI-1: build the local-first knowledge ingestion package.
   - Evidence: `backend/ingestion/local_ingestion.py` discovers supported local text files, extracts/scrubs text, chunks through `RAGService`, creates chunk-level SQL `KnowledgeGraphNode` rows, dedupes by chunk hash, indexes Chroma `knowledge_nodes`, and writes JSON manifests.
   - Validation: `python -m pytest -q --no-cov tests\unit\test_ki_local_ingestion.py tests\unit\test_phase4_dbc.py::test_index_knowledge_nodes_indexes_sql_node_like_objects`.
2. [x] KI-2: add document ingestion CLI and API entrypoints.
   - Evidence: `scripts/ingest_local_corpus.py` runs ingestion under Flask app context; `POST /api/v1/ingestion/local` is registered through `routes/__init__.py` and path-scoped outside desktop mode.
   - Validation: route tests cover allowed local ingestion and path rejection outside `DATALOGIC_INGESTION_ROOT`.
3. [x] KI-3: connect ingestion evidence to trace/audit surfaces.
   - Evidence: `RAGService.search_documents()` now returns normalized `citation` objects from source metadata; `get_context_for_query(include_sources=True)` renders source/chunk labels; TruthCore deep-research output includes `citations` alongside RAG evidence.
   - Validation: focused RAG/TruthCore tests verify citation metadata from ingested corpus search results.
4. [x] KI-4: release evidence refresh after KI.
   - Evidence: `scripts/verify_ki_ingestion.py` creates a disposable sample corpus/database, ingests it, verifies SQL node creation, verifies indexing handoff, verifies search citation metadata, and writes `reports/ki_ingestion_evidence.json`.
   - Validation: KI tests, ruff, py_compile, docs reference validation, and the KI evidence script passed.
5. [x] KI-5: add Settings knowledge ingestion controls and manifest-backed history.
   - Evidence: `GET /api/v1/ingestion/supported`, `GET /api/v1/ingestion/history`, `frontend/components/settings/KnowledgeIngestionSettings.tsx`, and Settings -> Knowledge tab are implemented.
   - Validation: `python -m pytest -q --no-cov tests\unit\test_ki_local_ingestion.py`; `npm --prefix frontend test -- tests/unit/lib/api/ingestion.test.ts components/settings/KnowledgeIngestionSettings.test.tsx`; frontend typecheck passed.
6. [x] KI-6a: harden end-to-end KI ingestion validation evidence.
   - Evidence: `scripts/verify_ki_ingestion.py` now writes explicit checks for text extraction/scrubbing, chunking, SQL persistence and metadata, Chroma handoff, citation metadata, source-rendered context, and manifest output to `reports/ki_ingestion_evidence.json`.
   - Validation: `python scripts\verify_ki_ingestion.py`; `python -m ruff check scripts\verify_ki_ingestion.py`.
7. [x] KI-6b: add richer PDF/DOCX/binary extractors and standard corpus loaders.
   - Evidence: `LocalKnowledgeIngestionService` now supports `.pdf` and `.docx` files by delegating to the existing `DocumentProcessor` (pypdf + python-docx). Binary extensions are routed through `_extract_via_document_processor()` while text files continue through the existing UTF-8 fallback path. `SUPPORTED_EXTENSIONS` is the new union set; `SUPPORTED_TEXT_EXTENSIONS` is preserved for backward compatibility. `/api/v1/ingestion/supported` now returns `.pdf` and `.docx` in the extensions list.
   - Validation: `python -m pytest tests/unit/test_ki_local_ingestion.py` — all 14 tests pass including `test_pdf_file_ingestion_uses_document_processor`, `test_docx_file_ingestion_uses_document_processor`, `test_unsupported_binary_files_are_rejected`, `test_pdf_without_processor_rejects_gracefully`. Ruff clean.
8. [x] KI-7: add optional async/background ingestion queue semantics and SQL -> Neo4j sync evidence after ingestion.
   - Evidence: `ingest_path_async()` runs ingestion in a background `threading.Thread` with Flask app context, tracks status via a module-level dict, and optionally calls `scripts.sync_nodes_to_neo4j.sync()` post-ingestion. New routes: `POST /api/v1/ingestion/local/async` (returns 202 with `ingestion_id`), `GET /api/v1/ingestion/status/<ingestion_id>`. Frontend `KnowledgeIngestionSettings` adds async mode toggle with 2s polling and Neo4j sync toggle.
   - Validation: `test_async_ingestion_returns_id_and_completes`, `test_async_ingestion_status_route`, `test_async_route_starts_and_returns_202`, `test_neo4j_sync_called_on_async_with_flag` — all pass. Ruff clean.
9. [x] KA-STUB-1: replace explicit KA stubs and add focused tests.
   - Evidence: `KA-011`, `KA-033`, `KA-039`, `KA-048`, `KA-077`, `KA-109`, and `KA-Master` no longer return explicit placeholder/stub behavior.
   - Validation: `python -m pytest -q --no-cov tests\knowledge_algorithms\test_ka_stub_replacements.py tests\knowledge_algorithms\test_ka_master_controller.py tests\knowledge_algorithms\test_ka_logic.py`; focused ruff check passed.
10. [x] KA-DEPTH-1: upgrade first thin model-ops KA batch.
   - Evidence: `KA-084` detects absolute and relative metric drift, `KA-087` versions artifacts from semantic version and artifact digest data, `KA-089` computes pruning impact from parameter/importance metadata, and `KA-090` computes quantization size reduction from precision and artifact-size metadata.
   - Validation: `python -m pytest -q --no-cov tests\knowledge_algorithms`; touched-path ruff check passed.
11. [x] AUDIT-SPRINT-1: eliminate duplicate class names, module name collisions, misplaced files.
    - Evidence: KA-050 renumbered to KA-117; `SystemRefinementOrchestrator` disambiguated; `MultiAgentSimulationEngine` separated from core simulation engine; governance axis enums ported to canonical `core/coordinate_system.py`; `GatewayPersonaSufficiencyTool` disambiguated; `RAGSanitizer`/`ResilienceRouter` moved from `backend/core/` to `core/`; disambiguating docstrings added to 6 intentional same-name pairs; `TruthAuditRecorder` renamed.
    - Validation: `python -m pytest --no-cov -q` → 1830 passed / 21 skipped; `ruff check .` → clean.
12. [x] AUDIT-SPRINT-2: resolve all core→backend import inversions.
    - Evidence: `find_core_backend_inversions.py` reports 0 lines. Module-level inversions moved inside method bodies; optional backend services injected via constructor (`frost_service.py`, `layer2_knowledge.py`, `persona_construction_service.py`) or annotated `# inversion:ok` for approved lazy-try patterns. Scanner updated to exclude annotated lines. `# inversion:ok` policy documented in `REPO_AUDIT_LOG.md`.
    - Validation: `python -m pytest --no-cov -q` → 1838 passed / 21 skipped; `ruff check .` → clean; `python scripts/find_core_backend_inversions.py` → 0 lines.
13. [x] AUDIT-SPRINT-3: replace compliance manager stubs with real implementations.
    - Evidence: `backend/security/compliance_manager.py` — all 5 `_check_*` methods replaced with real SOC 2 Type 2 runtime checks. SC-1: `ENCRYPTION_KEK_SECRET` set/not-dev + key rotation via `get_encryption_manager().get_key_status()` + audit dir probe. SC-2: `db.engine.connect()` / `SELECT 1` + violation spike guard. SC-3: Alembic Python API migration-at-head + `TruthAuditRecorder.verify_chain()` hash chain. SC-4: key not dev/weak + PII regex scan of last 200 audit log lines. SC-5: route file presence check for `/export`, `/delete`, `ai_processing_enabled`. `_apply_check_result()` helper eliminates duplicate state-mutation. Module-level `try/except` imports make all dependencies patchable by unit tests.
    - Test file: `tests/security/test_compliance_manager_coverage.py` — 25 tests covering happy-path and non-compliant branches for each of SC-1 through SC-5.
    - Validation: `python -m pytest tests/security/test_compliance_manager_coverage.py -v --no-cov` → 25 passed / 0 failures; `python -m pytest tests --no-cov -q` → 1855 passed / 21 skipped / 0 failures; `ruff check .` → clean.

14. [x] REPO-AUDIT-DUPS: duplicate class/file audit and sprint plan produced.
    - Evidence: `scripts/audit_duplicates.py` and `scripts/audit_deep.py` scanned live code and found 8 module name collisions, 17 duplicate class names, 2 cross-tree factory function duplicates, and 2 misplaced files in `backend/core/`. Full findings in `docs/audits/DataLogicEngine_Audit_Sprint_Plan_v2.md`. Note: Audit Sprints 1–3 already completed the execution of most findings from this audit; see AUDIT-SPRINT-1 through AUDIT-SPRINT-3 above.
    - Audit file: `docs/audits/DataLogicEngine_Audit_Sprint_Plan_v2.md`
15. [x] REPO-AUDIT-ROUTES: full routes audit — `routes/` and `backend/routes/` (all 22 route files).
    - Evidence: live read of all 22 route files. 20 issues found including 2 functional bugs (RT-1: 4 duplicate function names in multimodal_routes causing wrong handler dispatch; RT-2: unauthenticated `/search/suggest`), 5 unregistered blueprints (settings, analytics, retention, gdpr, privacy — all endpoints unreachable), and 3 overlapping user-data deletion implementations.
    - Sprint tasks: RT-1 through RT-18 — see `docs/audits/DataLogicEngine_Routes_Audit.md` for full task list and exit gates.
    - Audit file: `docs/audits/DataLogicEngine_Routes_Audit.md`
    - Status: Audit complete; all 18 RT tasks executed and merged 2026-06-07/08 (`df29906b`, `0eb2b0bb`, `cc01c15b`). `df29906b` also migrated `routes/` → `backend/routes/`.

16. [x] REPO-AUDIT-COMPLETE-PLAN-V2: complete remaining audit plan v2.0 — all 4 new items investigated from live code reads + full conversation history review.
    - Evidence: live MCP reads of `core/self_evolving/sekre_engine.py` (620 lines),
      `prompts/defense_supervisor.txt` (30 lines), `core/axes/axis_system.py` (345 lines),
      all 4 legacy axis files, and importer scans confirming zero usage of sekre_engine and
      defense_supervisor. Full conversation history reviewed (9 prior sessions).
    - N1 `core/self_evolving/sekre_engine.py`: SEKRE = Self-Evolving Knowledge Refinement Engine,
      620 lines, fully implemented, **zero importers** — disconnected. Must be wired into post-L10
      pipeline. Correct location confirmed. Wiring tasks defined.
    - N2 `prompts/defense_supervisor.txt`: LLM security supervisor prompt for injection/social-
      engineering/DAN detection. **Zero importers** — disconnected. Must be wired into
      `backend/security/prompt_injection_shield.py` or `ai_guardrail.py`. Added to installer
      bundling requirement.
    - N3 Duplicate axis files: `axis_system.py` confirmed loading canonical set (acquisition_
      lifecycle, risk_threat, ethics_trust, frost_mode). 4 legacy files (provenance, object_type,
      validation_state, security) **never imported** — safe to delete. Delete tasks defined.
    - N4 Missing Axis 4/5 files: `axis3_domain.py` (DomainManager) reused for Axis 4. Axis 5
      has no dedicated manager. Verdict and resolution tasks defined.
    - Plan: `docs/audits/DataLogicEngine_Complete_Audit_Plan_v2.md`
    - Scope: 32 audit areas, ~31 sessions, full Definition of Done criteria.
    - Status: Plan complete. Correction 2026-06-11: the plan's Sprint 0 listed RT-1/RT-2/RT-3 from a
      stale snapshot — all RT items were already done 2026-06-07/08. Sprint 0 (N3 + N4) and Phase 1 / A4
      executed 2026-06-11; next session is A3 `backend/llm_gateway/`.

17. [x] AUDIT-SPRINT-0 + N3/N4: close Sprint 0 of audit plan v2.0.
    - N3 evidence: `core/axes/axis14_provenance.py`, `axis15_object_type.py`, `axis16_validation_state.py`,
      `axis17_security.py` deleted; orphaned `SourceProvenance`/`ObjectType`/`ValidationState`/
      `SecurityClassification` enums removed from `core/coordinate_system.py`; `core/axes/__init__.py`
      rewritten (its re-exports were the only importers; nothing consumed them).
    - N4 evidence: `axis_system.py` documents Axis 4 = DomainManager (hierarchical taxonomy fits branch
      semantics) and Axis 5 = deliberately unmanaged (convergence nodes are graph nodes; unmanaged
      resolution path). Found + fixed live bug: `backend/honeycomb_api.py` looked up Honeycomb at legacy
      Axis 5 instead of canonical Axis 3 — all 4 endpoints always returned 500. Added `_get_honeycomb()`
      (Axis 3 + None guard) and missing auth (`@api_login_required` ×3, `@api_admin_required` on `/connect`).
    - Validation: `tests/unit/test_axis_alignment.py` (+2 decision tests), new
      `tests/integration/test_honeycomb_api.py` (7 tests); full `python -m pytest --no-cov -q` →
      2003 passed / 21 skipped; `ruff check` clean on touched paths.

18. [x] AUDIT-A4: Phase 1 session 1 — `backend/local_model_acceleration/` audit (8 files).
    - Evidence: all audit questions answered in `REPO_AUDIT_LOG.md` (Sprint 0 + A4 entry). Tier 0 query
      traced end-to-end (classifier → tier cascade → ollama_model_override → acceleration wrapper →
      governance/usage). Cache invalidation on knowledge-base update confirmed wired in all 3 RAGService
      ingestion entry points. `safety.py` confirmed cache-eligibility filter only — N2 defense_supervisor
      wiring belongs to A3/A10.
    - Fixes: A4-1 gateway cache-hit coroutine lifecycle (`inspect.getcoroutinestate` gate; close on hit,
      no re-await after consumption); A4-2 keepalive settings reload per request (UI toggle now effective
      without restart); A4-3 `backend.spec` adds `collect_submodules('backend.local_model_acceleration')`.
    - Forward findings: A4-4 tier re-probe trigger (A3), A4-5 latent `stream=True` NDJSON break (A3),
      A4-7 exact-cache-hit audit-trail semantics (A1b), A4-8 `process()` test harness (A3).
    - Validation: `python -m pytest -q --no-cov tests\unit\test_local_model_acceleration.py
      tests\unit\test_tier_availability.py` → 56 passed (5 new tests); gateway units 17 passed;
      ruff clean; full suite green.

19. [x] AUDIT-A3: Phase 1 session 2 — `backend/llm_gateway/` audit + N2 defense supervisor wiring.
    - Evidence: full audit verdicts in `REPO_AUDIT_LOG.md` (A3 entry). Governance confirmed enforced
      per-request (input shields, token budgets, output replacement, AIAuditEvent). DMRF flag wired.
      Complexity classifier is deliberately separate from KA-113 (model tier vs reasoning tier).
      All 6 escalation tiers configured; model names current.
    - N2 wired: `backend/security/defense_supervisor.py` + prompt moved to
      `backend/security/prompts/defense_supervisor.txt`; gateway screens pipeline queries on the
      cheapest available local Ollama tier (JSON mode, 8s timeout, temperature 0, 5-turn Crescendo
      context); BLOCK/HONEYPOT → `DEFENSE_SUPERVISOR_BLOCK` audit event + "Request blocked by
      security policy"; fail-open everywhere; `DEFENSE_SUPERVISOR_ENABLED=false` kill switch.
    - Security fix: `/network-status`, `/quad-analysis-status`, `/dmrf-status`,
      `/dsqp-persona-profiles` now require auth (signed desktop loopback accepted); Electron IPC
      handlers switched to signed `desktopFetch`.
    - Carry-overs resolved: A4-4 (throttled background tier re-probe + `POST
      /local-acceleration/reprobe`), A4-5 (`OllamaClient.generate` stream guard + system/format_json/
      timeout params), A4-8 (`tests/unit/test_llm_gateway_process_harness.py`).
    - Forwarded: A3-3 Tier 2+ audit-commit tier-string gate (A1b), A3-4 supervisor user_role/HONEYPOT
      (A10), A3-5 governance no-db audit no-op (A26).
    - Validation: 98 focused tests pass (14 supervisor, 7 harness, 5 re-probe new); ruff clean;
      Electron typecheck clean; full pytest green.

20. [x] AUDIT-A1a: Phase 1 session 3 — `truth_core/` + `truth_gate/` audit.
    - Verdicts in `REPO_AUDIT_LOG.md` (A1a entry). TruthCore `engine.py` is the real entry point
      (wired in `truth_engine/api.py`), tier→layer maps real, L8 FAIL / L10 HALT break the loop.
      L9 max-5-iteration enforced; L10 emergence gate makes real RELEASE/HALT/MODIFY/ESCALATE
      decisions; L7 AGI planner is real BFS with depth/iteration/goal caps + guardrail sanitization.
      TruthGate blocks (not just logs): adversarial blocks, budget kill-switch DB writes, L8 5-phase
      gate is fail-closed on timeout and exception, OPA + model screening can flip to FAIL.
    - Fix A1a-1: `engine.py` `_execute_workflow` returned hardcoded `processing_time_ms: 500` into
      the audit trail; now computes real `time.perf_counter()` elapsed.
    - Forwarded: A1a-2 `LLMRouter` parallel dead code w/ stale models (A6b/cleanup), A1a-3 SDK tier
      vocabulary vs Tier 2+ audit-commit gate (A1b, joins A3-3), A1a-4 no-KA "Mock result" fallback
      (A6).
    - Validation: focused truth_engine 94 passed; ruff clean; full pytest green.

35. [~] AUDIT-A15: Phase 3 — `frontend/app/` pages audit + deferred auth removals. **IN PROGRESS.**
    - Done (nav/structure batch 2026-06-18): full 29-page map; F1 broken `tools/history`→`/runs/[id]` link fixed
      (→`/runs/view?id=`); F2 removed dead duplicate `projects/[id]`; F3 consolidated nav to `AppSidebar`
      (NavBar→chrome); F4 wired 5 orphaned surfaces (`/runs`,`/truth-engine`,`/analytics`,`/algorithms`,
      `/admin/compliance`) into the sidebar. Component suite 51 files/150 tests pass.
    - Remaining: F5 coordinated auth removal + B2 docs (below); per-page error/loading-state verification.
    - Scope: all Next.js page files under `frontend/app/`; coordinated frontend+backend deferred auth cleanup.
    - Deferred auth: admin user-mgmt UI (`frontend/app/admin/page.tsx` 268-line form ↔ `backend/routes/admin_routes.py`
      user-mgmt/ownership routes); MFA (`backend/security/mfa.py` + `User.mfa_enabled/mfa_secret` ↔ 3 frontend files);
      `backend/security/tenant_rls.py` (Postgres RLS + app startup + prometheus); `User.role/is_admin` column slim
      (DB migration). Remove these as coordinated frontend+backend pairs — not as isolated backend sweeps.
    - **B2 RBAC doc reconciliation (folded in 2026-06-18):** correct multi-user/RBAC claims that contradict
      single-mode in `docs/PRODUCT_OVERVIEW.md` (capability table "role-gated"/"admin users"),
      `docs/diagrams/11_frontend_product_surface_and_trace_review_map.md` ("RBAC enforcement"/"user management"),
      and `docs/ARCHITECTURE.md` — change docs alongside the admin-UI code removal so they stay in sync.
    - Auth deprecation plan: `docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md` (Phases D+E+F remain).
    - **Next up after A15: A16 `frontend/components/`, A17 `frontend/lib/` + hooks.**
    - **A16 carries C3 (folded in 2026-06-18):** surface `test_provider` status codes inline in
      `frontend/components/settings/ApiOverlayConfig.tsx`.

34. [x] AUDIT-A14: Phase 2 (FINAL) — `sdk/UKG_Python_SDK/` SDK surface audit + Antigravity breakage repair.
    Commits: `087a9917` (Antigravity initial A14 work), `008287ca` (Claude repair), `25f3e929` (docs).
    - Antigravity A14 work (`087a9917`): A14-2 coord routing (`{**meta, "query": query}` to resolver), A14-3 DSQP import
      cached at init, A14-4 axis_17 default `"moderate"` → `"standard"` (tier-label collision), tenlayer docstring,
      pyproject deps, new `test_coordinates17.py` + `test_overlay_run.py`.
    - **5 build-breaking bugs repaired** (`008287ca`): (1) `Coordinate→Coordinate17` in `__init__.py` — `ImportError`
      on ALL consumers of the packaged SDK; (2) unused imports in `coordinates17.py` (ruff F401); (3) builtin KA
      registration guard removed from `ka/builtins.py` — guard meant no handlers registered with empty registry,
      `overlay.run()` always returned `ok=False`; (4) invalid `veto_reason=` kwarg on `KAExecutionResult` in
      `ka_004_validate` (field doesn't exist, would TypeError); (5) `out_valid.veto_reason` → `out_valid.error` +
      KA-61 regex `(previous|all)` → `(all\s+)?(previous\s+)?` in `overlay.py`.
    - SDK surface confirmed: UKGClient/UKGAsyncClient, UKGOverlay (full 10-step run), TruthEngineAPI, KAExecutor,
      WorkflowRunner, CoordinateResolver17/Coordinate17, DSQPClient (import-guarded), providers/memory/audit/builtins.
    - Validation: 33 SDK tests pass (were 4 failing + ImportError); ruff clean; pre-commit green.

33. [x] AUDIT-A13: Phase 2 — `core/system/` (System Services) — verify-only.
    Commit: `4a66ebff`.
    - All 11 services confirmed live. SekreEngine (N1) wired: `system_initializer.py:192` invoked by
      `core/simulation/app_orchestrator`; gm/smm/usm injected; `simulation_validator=None` minor forward.
    - DUP-2 = 3 DISTINCT orchestrators retained by design (plan's "confirm deleted" was stale): SystemRefinementOrchestrator
      (core/system), SimulationRefinementOrchestrator (core/simulation), RefinementOrchestrator (truth_core).
    - FROSTService, PersonaConstructionService, UnitedSystemManager, TraceProvenanceService all confirmed live.
    - TV-6 correction: `trace_stage_update` Socket.IO emitted in `backend/llm_gateway/gateway.py` + `backend/websocket.py`
      (NOT `core/system/trace_service.py`, which is *provenance* tracing). 5 tests pass.

32. [x] AUDIT-A12: Phase 2 — `backend/storage/` storage layer audit.
    Commit: `cea5039e`.
    - All 8 storage files confirmed wired. DB-N (graph_store/Neo4j), DB-C (vector_store/ChromaDB), DB-M
      (uskd_memory_graph `UskdMemoryGraph` via `__init__` re-export — distinct from `StructuredMemoryGraph` in quad
      math framework; plan conflated them) all re-confirmed live.
    - `connection_manager.py` = Postgres/Redis connection config only (plan misattributed rate-limiting; flask_limiter
      handles that; multi-worker concern moot under single-mode).
    - **Fixed RT-10:** `runtime_settings.save_storage_settings` now writes atomically (tempfile + os.replace). Was
      non-atomic — could silently reset all user preferences on crash mid-write.
    - Validation: 46 tests pass; ruff clean.

31. [x] AUDIT-A11: Phase 2 — `core/axes/` (17-Axis System) — verify-only.
    Commit: `85c114fe`.
    - 17 axes register correctly in `axis_system.py`. Axis 5 (Node/convergence) intentionally unmanaged by design (N4,
      documented in-code). N3 (4 legacy axis14-17 files) + N4 (Axis 4=DomainManager) + DUP-4 (single canonical
      `core/coordinate_system.py`) all confirmed resolved from Sprint 0. AxisSystem live via `backend/contextual_api.py`.
    - Forwarded: `scripts/audit_deep.py:144` stale regex → A32; misleading-but-stable filenames kept by decision.
    - Validation: 30 axes tests pass.

30. [x] AUDIT-A10: Phase 2 — `backend/security/` audit + **auth deprecation BANKED at A+B+C-partial**.
    Commits: `57b912da` (Phase A), `e710aeb3` (Phase B), `b1a92674` (Phase C-partial + BANKED).
    - **Architecture reframe (user-confirmed):** app is single-mode / OS-level auth (even cloud = single-tenant VM).
      Multi-user auth layer is architecturally obsolete. Memory: `architecture-single-mode`.
    - Carry-overs resolved: A3-4 N/A by design (HONEYPOT→BLOCK correct for single owner), A5-2 keep all 5 injection
      defenses (defense-in-depth union, distinct stages), SC-2 AES-256-GCM confirmed active cipher.
    - **Auth deprecation executed:** Phase A — removed dead `zero_trust.py` + `token_manager.py` (~1,200 LOC, 0 live
      importers). Phase B — `api_admin_required` collapsed to alias of `api_login_required`; removed `rbac.py`
      + de-wired from admin/privacy/mcp/extensions; full owner scopes for MCP; migrated 3 admin-403 tests → 200.
    - **Phase C correction:** auth_routes/LoginManager/session_manager/API-key branch = live **desktop-auth keep-path**
      (NOT removable). Dropped only stale CSRF entries; fixed 5 pre-existing `test_desktop_auto_login_security.py`
      failures (stale `routes.auth_routes` → `backend.routes.auth_routes`).
    - Remainder (admin user-mgmt UI, MFA, tenant_rls, User.role/is_admin) = vestigial-but-wired/cross-cutting →
      deferred to A15/A16 as coordinated frontend+backend changes.
    - Plan: `docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md` (6 phases A–F; A+B+C-partial DONE).
    - Validation: pre-commit green; 5 fixed desktop-auth tests; 3 migrated admin tests.

29. [x] AUDIT-A9: Phase 2 — `core/persona/quad/` reachability map (+ follow-on carry-over resolutions).
    Commits `5a1353c9` (A9 + docs), `f2899e30` (A1a-2/A1a-4 code).
    - **LIVE/canonical:** `models.py` (PersonaProfile 7-component + QueryState), `persona_scaling/sufficiency.py`
      (DUP-5 clean: GatewayPersonaSufficiencyTool + PersonaSufficiencyTool), `pod_models.py`, `pod_orchestrator/`,
      `mathematical_framework/`. **DEMO-ONLY:** `quad_engine.py` (heuristic 4-persona; importers = demo scripts + 1
      test). Plan premise was wrong — the real query-time 7-component construction is
      `core/system/persona_construction_service.py` → DSQP (A2/A2-2), not quad_engine. Fixed its stale docstring
      (named `layer2_legacy_knowledge.py`, deleted in A6a `2afe2d14`).
    - Forwarded: A9-1 `axis_role_mapper.py` (test-only) + `persona_loader.py` (script-only) → A29; A9-2 `quad_models.py`
      (misnamed L3 models, dup of SDK, 1 script importer) → A14/A29; A9-3 `__init__.py` docstring → A31.
    - **Carry-overs resolved this pass** (REPO_AUDIT_LOG.md "Carry-over resolutions"):
      - A1a-2 — deleted dead `truth_core/router.py` `LLMRouter` (stale model set; zero prod callers; DMRFRouter is a
        separate live class) + its `__init__` export + `TestLLMRouter`.
      - A1a-4 — `_execute_refinement_step` fabricated `completed`/0.8 "Mock result" (was consolidated into the memory
        graph + piped downstream as if real) → honest `skipped`/0.0/reason.
      - A10-password — CONFIRMED SECURE, no code change. `password_security.py` is policy-only; real store-hash is
        `models.py:112` werkzeug `generate_password_hash` → `scrypt:32768:8:1` on werkzeug 3.1.8 (OWASP baseline,
        ≥ bcrypt-12). The plan's "bcrypt ≥12 rounds" pointer was a red herring.
    - Validation: `tests/persona/quad/` 41 + `tests/truth_engine/` 75 passed; ruff clean; pre-commit hooks green.
    - **Next: A10 `backend/security/`** — resolve A3-4 (defense supervisor `user_role`/HONEYPOT-as-BLOCK — may need a
      product call on honeypot behavior), A5-2 (consolidate 5 overlapping injection defenses), SC-2 (Fernet→AES-256-GCM
      docs). Password item already closed — do NOT re-chase.

28. [x] AUDIT-A8: Phase 2 session 2 — per-KA rating sweep + A5-3. **knowledge_algorithms audit complete.**
    - Rated all 125 KAs: 117 real + 8 compact-real (7 l10/ modules delegating to l10/common + KA-112) + 0 stub.
      Config completeness: 0 orphan configs; 4 KAs (33 reserved, 117/43/44) use graceful defaults. Verdicts in
      `REPO_AUDIT_LOG.md` (A8 entry). The 100–117 band are representational infra KAs (describe ops, don't perform).
    - A5-3 resolved (deeper than planned): KA-005 never emitted a tier, so TruthCore.determine_tier's KA-005
      branch always fell through to heuristic. Fixed — KA-005 now maps category→`suggested_tier`
      (REGULATORY→high_stakes, TECHNICAL/RESEARCH→moderate, GENERAL→trivial; config-overridable). Dropped the
      genuinely-unused `DMRFTierClassifier.ka_controller` param (DMRF tiering stays a fast heuristic by design).
    - Validation: `tests/knowledge_algorithms/test_ka_05_suggested_tier.py` (4) + DMRF/KA/truth_engine green (77);
      ruff clean. Full-suite run covering A7+A8 before commit. Next: A9 `core/persona/quad/`.

27. [x] AUDIT-A7: Phase 2 session 1 — `backend/knowledge_algorithms/` registry/config map + high-risk verification.
    - Registry: all **125** `ka_registry.yaml` entries resolve to an importable `module.run` callable (0 broken).
    - Configs: by-convention `config/ka_NN_config.json` with graceful fallback; `ka_33` reserved (no config, expected);
      KA-117 rename confirmed (integrity validator at 117; 50 is now summarization).
    - High-risk verified real: KA-014 (F-CONF-01 confidence), KA-061 (adversarial shield, fail-closed),
      KA-005 (classification), KA-117/116/032/034/024. Plan's high-risk numbering was stale (corrected by concept).
    - Fix A7-1: KA-113 complexity router was scoring on `len(query)/100` despite its config declaring
      `heuristic_weights` (query_length/semantic_ambiguity/domain_specificity); implemented the 3-signal
      weighted blend the config specifies. +6 tests.
    - Carried to A8: per-KA rating sweep (all 125 real/heuristic/stub), config-completeness cross-check,
      A5-3 KA-005 hook for DMRFTierClassifier.
    - Validation: KA suite + truth_engine coverage green; ruff clean. (Full-suite run pending next session.)

26. [x] AUDIT-A6b: Phase 1 session 8 (FINAL) — `core/simulation/` L6–L10 map + N1 SEKRE wiring. **PHASE 1 COMPLETE.**
    - Map in `REPO_AUDIT_LOG.md` (A6b entry). Live L6–L10: layer6_enhancement, layer7_agi_system,
      layer8_quantum (quantum-inspired), layer9_recursive (max_iterations=5 enforced), layer10_synthesis.
      The 4 variant files (layer6_neural_analysis, layer8_quantum_computer, layer9_recursive_agi,
      layer10_self_awareness) are demo/research code (scripts/demos + scripts/archive consumers) — kept.
      legacy_simulation_engine.py + agentic/ are live via persona_api/truth_engine api — kept. No deletions.
    - N1 SEKRE WIRED: `SimulationEngine.__init__` instantiates `SekreEngine` (fail-safe, config-gated);
      `run_simulation` calls `_run_sekre_analysis` post-L10; Tier-3+ gate (`_qualifies_for_sekre`);
      read-only by default (auto_improve off); added `collect_submodules('core.self_evolving')` to backend.spec.
    - Both June-10-scan disconnected components now wired: N1 (SEKRE) + N2 (defense_supervisor, A3).
    - Validation: `tests/simulation/test_sekre_wiring.py` (9) + simulation suite 58 passed; full suite green; ruff clean.
    - Next: **Phase 2 — Reasoning Depth**, starting A7 (`backend/knowledge_algorithms/`, the 117 KAs).

25. [x] AUDIT-A6a: Phase 1 session 7 — `core/simulation/` L1–L5 layer map + legacy-cluster removal.
    - Verdicts/map in `REPO_AUDIT_LOG.md` (A6a entry). Live path: `SimulationEngine` (via app_orchestrator
      / master_workflow / system_initializer) wires L4–L10; master_workflow wires L1–L3. Authoritative
      L1–L5 live files: layer1_entry, layer2_knowledge, layer3_expert, layer4_reasoning, layer5_integration.
    - Fix A6a-1: `SimulationEngine.__init__` was overwriting the canonical `layer5_integration` engine with
      the legacy `layer5_legacy_integration` after `_initialize_simulation_layers` set the canonical one;
      removed the redundant block (+ redundant L7 re-init) so canonical L5 wins (matches DUP-3 + the test).
    - Removed 12 confirmed zero-importer dead files: two parallel dead orchestrators
      (`orchestrator.py`/`SimulationOrchestrator`, `layer_controller.py`/`LayerController`) and their
      exclusive dependency chains (truth_engine, layer1_database, layer1_legacy_entry, layer1_planning,
      layer2_legacy_knowledge, layer2_retrieval, layer3_agents, layer3_agent_engine,
      layer5_legacy_integration, layer5_pipeline). Three-orchestrator / three-files-per-layer mess
      collapses to one live orchestration with one file per layer.
    - Validation: focused simulation 53 passed + end_to_end; full suite green; ruff clean. Next: A6b
      (L6–L10 + orchestration + `legacy_simulation_engine` + `agentic/`), then wire N1 SEKRE.

24. [x] AUDIT-A5: Phase 1 session 6 — `backend/dmrf/` 17-axis router / control plane.
    - Verdicts in `REPO_AUDIT_LOG.md` (A5 entry). All 17 axes exercised by `router.py`;
      `tier_classifier` is the reasoning tier (distinct from gateway model-escalation classifier —
      not a duplicate); `convergence_policy` real (KA-023 belief decay); `frost_bridge` real per-step
      FROST snapshots; **no MLflow conflict** (`dmrf` vs `truthmemory` experiments); injection_defense
      layered at DMRF + TruthGate; all 4 truth_integration adapters are real delegations.
    - Fix A5-1: `DMRFDesktopConfig` was orphaned while its values were hardcoded; wired
      `offline_tier_cap` + `max_refinement_iterations` from config into the classifier and convergence
      policy (defaults unchanged; now tunable via `dmrf_config.json`).
    - Forwarded: A5-2 five overlapping pattern-injection defenses → consolidate review (A10);
      A5-3 `DMRFTierClassifier.ka_controller` unused param (A7/A8).
    - Validation: DMRF integration 11 passed (+2 new); ruff clean; full suite green. Next: A6a/A6b
      `core/simulation/` 10-layer stack, then wire N1 SEKRE.

23. [x] A2-2: build LLM-assisted DSQP construction (closes the deferred patent-claim gap).
    - `backend/dsqp/dsqp_answer_generator.py`: one local-Ollama JSON call per persona axis answers the
      7 role-construction questions from the query/coordinate/domain; per-component schema validation;
      missing/malformed components fall back to the deterministic scaffold. Kill switch
      `DSQP_LLM_ASSISTED=false`; timeout `DSQP_GENERATION_TIMEOUT` (15s).
    - `dsqp_chain.py`: per-step `source` provenance + `construction_mode`
      (llm_assisted/hybrid/deterministic_offline); deterministic context fields back-filled so the
      `ExpandedPersona` schema and validator are unchanged.
    - `tier_availability.cheapest_available_local_model(optimistic=)` added; DSQP uses strict
      (probe-confirmed) resolution to avoid hot-path timeouts; defense_supervisor refactored onto the
      shared helper. `tests/conftest.py` pins `DSQP_LLM_ASSISTED=false` so the suite stays offline.
    - Now substantively query-derived (verified live in A2): FDA-implant vs SEC-10b-5 queries yield
      different roles/credentials instead of the same "Lead Regulatory Analyst". A2-2 no longer a pre-IP gap.
    - Validation: `tests/unit/test_dsqp_llm_assisted.py` (7) + existing DSQP/persona suites green; ruff clean; full suite green.

22. [x] AUDIT-A2: Phase 1 session 5 — `backend/dsqp/` patent-claim audit.
    - Exit-gate disclosure-match statement in `REPO_AUDIT_LOG.md` (A2 entry). Verdict: implementation
      matches `docs/ip/dsqp_technical_disclosure.md` as written (deterministic first slice). Structure
      (per-axis 7-step self-questioning chain, per-query construction, no cross-query cache, coverage
      validation, audit persistence, offline) all real and confirmed. Registry stores question specs
      (not pre-built definitions); templates hold questions only (not role cards).
    - Fix A2-1: `DSQPValidator` now validates the DSQP *process* (chain executed: 7 steps, each with a
      non-empty question + answer) in addition to component coverage — closes the "process validation"
      gap. All real callers pass the full persona payload, so happy path unaffected.
    - Forwarded A2-2: deterministic `_answer_question` yields axis-keyed role scaffolds with only shallow
      query derivation; implement the LLM-assisted answer generation the disclosure anticipates before any
      external IP filing / "fully dynamic construction" claim. Until then describe the build as the
      "deterministic activation scaffold."
    - Validation: DSQP unit 12 + integration 46 pass; +2 validator process tests; ruff clean; full suite green.
    - Next: A5 `backend/dmrf/`.

21. [x] AUDIT-A1b: Phase 1 session 4 — `truth_memory/` + `truth_link/` audit + carry-over resolution (`5027fc3b`).
    - Verdicts in `REPO_AUDIT_LOG.md` (A1b entry): 9 truth_memory + 5 truth_link files verified
      (hash-chain audit recorder, commit service/Merkle, Redis-backed cache, blockchain anchors, bus).
    - A3-3/A1a-3 RESOLVED: canonical `dmrf/models.py` `TIER_ORDER` confirms `moderate` = Tier 2, so the
      audit-commit/footer gate excluding "moderate" was skipping Tier 2 audit bundles. Exclusion set
      normalized to `{"", "0", "t0", "1", "t1", "trivial"}` with `.lower().strip()` (also fixes SDK
      `"T1"`/`"T2"` casing) across `_build_response`, `_create_trace_run`, and the cache-hit path.
    - A4-7 RESOLVED: response cache stores/returns `original_run_id`; Tier 2+ cache hits write a
      `cache_hit` compliance `TruthAuditEvent` linking new + original run ids (fail-safe wrapped).
    - Review (2026-06-11): `audit_logger.log_event` call verified against the real
      `TruthAuditRecorder.log_event` signature; 127 focused tests pass (process harness + LMA +
      truth_engine). Next: A2 `backend/dsqp/`.

### Trace Viewer Wiring Phased Update Plan

Source plan: `UKG_TraceViewer_Wiring_Plan_v3_1.docx` reviewed 2026-05-29 against live code.

Live-code baseline:

- Existing: `backend/tracing/api.py` exposes run, stage, evidence, claim, axis, persona, KA, policy, memory, metrics, export, replay, span, and log routes under `/api/v1/trace/runs*`.
- Existing: `frontend/lib/api/trace.ts`, `frontend/app/runs/page.tsx`, `frontend/app/runs/view/page.tsx`, `frontend/components/Chat/LiveTracePanel.tsx`, `frontend/components/Chat/MessageBubble.tsx`, and `frontend/components/Chat/ChatInterface.tsx`.
- Existing: `backend/websocket.py` initializes Socket.IO and supports generic room join/leave plus chat/simulation events.
- Gap: the DOCX assumes direct `/api/v1/trace/{run_id}` endpoints, but current live routes use `/api/v1/trace/runs/{run_id}` and related subroutes.
- Gap: `/api/v1/gateway/chat` currently returns `run_id` but not a structured `audit_trail` object with `complete_trace_url` and `download_url`.
- Gap: `MessageBubble` does not render an inline lazy-loaded trace panel for a specific assistant response.
- Gap: live WebSocket trace streaming needs trace-specific room join and `trace_stage_update` emissions after `TraceStage` writes.

| Phase | Scope | Local exit gate | Status |
| --- | --- | --- | --- |
| TV-0: Contract verification | Capture local Tier 2/Tier 3 gateway responses and trace route payloads; document exact live shapes for chat response, run detail, stages, evidence, personas, KAs, axes, and export. | A fixture report records current JSON contracts and mismatches from the DOCX assumptions. | Done: `scripts/verify_trace_viewer_wiring.py` writes `reports/trace_viewer_wiring_evidence.json` with gateway `audit_trail` links and aggregate bundle keys. |
| TV-1: Backend response and bundle contract | Add `audit_trail` to `/api/v1/gateway/chat`; add or document a single aggregate trace bundle shape that wraps run, stages, evidence, claims, personas, KAs, axes, policy, memory, and metrics; keep `/api/v1/trace/runs/*` canonical unless aliases are deliberately added. | Focused backend tests prove chat response contains `audit_trail.complete_trace_url`, `download_url`, and trace bundle data resolves for a generated/local fixture run. | Done: gateway chat includes `audit_trail`; `/api/v1/trace/runs/<run_id>/bundle` returns the aggregate contract; UUID route parsing and backend contract tests pass. |
| TV-2: Frontend trace types and API client | Expand `frontend/lib/api/trace.ts` and add typed trace interfaces for run bundle, stages, evidence, personas, KA invocations, axes, and export. | Frontend unit tests prove each API function unwraps the backend response shape and handles missing optional sections. | Done: `TraceBundle`, evidence, KA, persona, axis, stage, metrics, and audit-trail types are wired through `frontend/lib/api/trace.ts`; focused API tests pass. |
| TV-3: Inline chat trace panel | Thread `runId`/`auditTrail` through `ChatInterface` into `MessageBubble`; build an inline lazy-loaded TracePanel with summary, coordinate, FROST stages, personas, evidence, KA feed, refinement, and export affordance using the current design system. | Assistant messages with a trace run show a compact trace control; expanding it fetches the bundle only once and renders useful panels. | Done: `ChatInterface` threads `auditTrail`, `MessageBubble` renders `ChatTracePanel`, and the panel lazy-loads bundle data, streams live updates, links details, and exports traces. |
| TV-4: Runs explorer completion | Align `/runs` list/detail pages with the same typed trace bundle and add missing detail panels rather than relying on shallow run metadata. | `/runs` list and detail page render seeded/local trace fixture data, handle empty/error states, and pass frontend typecheck. | Done: `/runs/view` now consumes the aggregate bundle and renders stages, evidence, personas, KA feed, policy/memory counts, coordinates, metrics, and export. |
| TV-5: Evidence and persona depth | Validate or add serializer fields for evidence tier, source provenance, KA invoked, claims supported, persona positions, debate log, synthesis weights, and conflicts. | Backend tests prove evidence/persona APIs expose the fields used by the frontend panels without leaking unauthorized runs. | Done: `TraceEvidence`, `TracePersona`, `TraceStage`, and `TraceKAInvocation` serializers expose the viewer aliases used by frontend panels; backend contract tests validate them. |
| TV-6: Real-time trace streaming | Add trace-specific `join_run_room`/leave handling and emit `trace_stage_update` after `TraceStage` creation/update; add frontend hook for run-scoped live updates and a live badge. | WebSocket unit tests prove join + emit behavior; frontend tests prove streamed stage updates merge into panel state. | Done: trace run room join/leave, `trace_stage_update` emission, gateway stage emission, frontend `useTraceStream`, and socket tests are implemented. |
| TV-7: Validation and docs | Add trace viewer contract tests, frontend component tests, update API docs/TODO/master plan, and record local evidence. | Focused pytest, frontend unit/typecheck, docs reference validation, and trace viewer evidence report pass locally. | Done: pytest, Vitest, typecheck, ruff, docs validation, and evidence generation pass. Browser smoke was limited by auth/backend not running. |

### CI And Security Evidence

Update: 2026-06-11 — three red checks (Dependency Security Scan, NPM Security Audit, CI/CD `backend-test`) cleared.

- **Dependency Security Scan + CI/CD `backend-test` (same root cause).** `pip-audit -r requirements.txt` flagged `torch 2.12.0` / **CVE-2025-3000** (memory corruption in `torch.jit.script`, local-host attack only). No patched torch release exists, `torch` is a transitive dep (transformers / sentence-transformers), and the app calls `torch.jit.script` nowhere (`grep` over backend/core/sdk = 0 hits) — not reachable. Suppressed with `--ignore-vuln CVE-2025-3000` in both `.github/workflows/security.yml` and `.github/workflows/ci.yml` (the `backend-test` "Security Audit" step ran the same command, so it was a cascade — both clear together). Verified locally: `pip-audit -r requirements.txt --desc --ignore-vuln CVE-2025-3000` → "No known vulnerabilities found, 1 ignored", exit 0. Revisit when an upstream torch fix ships.
- **NPM Security Audit.** `npm audit --audit-level=high` flagged `shell-quote` (critical, `GHSA-w7jw-789q-3m8p`) pulled in transitively by the dev-only `concurrently@9.2.1`. Rather than the breaking `concurrently@10` bump, added `"shell-quote": "^1.8.4"` (the patched release) to `frontend/package.json` `overrides` — matching the existing `postcss`/`tmp` override pattern — and refreshed `package-lock.json`. Verified locally: `npm audit --audit-level=high` → "found 0 vulnerabilities", exit 0.

Previous update: 2026-05-30

- CI red-to-green remediation (multi-commit series on `main`): fixed all five originally-failing checks — Code Security Scan, Dependency Security Scan, CI/CD `backend-test`, CI/CD `frontend-build`, and Deploy `Build and Test` — plus the chain of jobs that fixing those unmasked. Final result: Security Scan, Deploy, and CI/CD Pipeline all green.
  - Dependency CVEs: `requirements.txt` pinned the stale `chromadb==0.5.23` (metadata caps `tokenizers<=0.20.3`), which locked the transitive `transformers` onto the vulnerable `4.46.3`. Pinning a CVE-free `transformers>=5.0.0` then surfaced that `chromadb==1.4.1` is itself in the pre-auth code-injection range of `GHSA-f4j7-r4q5-qw2c` (`>=1.0.0,<=1.5.9`, no patched release). That flaw is in ChromaDB *server* mode (`/api/v2/.../collections` with `trust_remote_code`); this app uses only the embedded `PersistentClient`, so it is not reachable. Final pin is `chromadb==0.6.3` — `<1.0.0` (outside the vulnerable range) and only requires `tokenizers>=0.13.2`, so the tree still resolves to CVE-free `transformers 5.9.0` / `tokenizers 0.22.2`. Verified: `pip install --dry-run`, backend smoke, and 16 chroma/vector/DB-C + 55 storage/startup/health tests pass against chromadb 0.6.3; CI Dependency Scan green.
  - Bandit delta gate: `backend/routes/storage_routes.py` row-count query annotated `# nosec B608` (table names come from `sqlite_master`, never user input). Delta gate exits 0.
  - Frontend typecheck: repaired type drift in five test files (`MessageBubble`, `CommandBar`, `DesktopStatus`, `McpIntegrationExamples`, `McpServerConfig`) against updated production interfaces — notably adding the eleven new `ElectronAPI` methods to the `DesktopStatus` mock.
  - Frontend unit tests (unmasked once typecheck passed): `LiveTracePanel.test.tsx`'s `vi.mock('@/lib/api')` omitted the `request` named export the component uses for `/trace/live-progress` and `/trace/ka-execution-feed`; the undefined export threw and the component's catch block dropped to the empty state. Added `request: vi.fn().mockResolvedValue(null)`. Full suite: 234 tests / 66 files pass.
  - Docs reference validation (Deploy): `scripts/verify_docs_references.py` treated any backtick ref ending in `/*` as a repo-directory wildcard, so API routes like `/api/v1/*` were checked as filesystem dirs and failed; now skips absolute, `/`-rooted refs. `docs/README.md` read-order repointed the missing `docs/diagrams/01_master_system_architecture.md` to the real `docs/ARCHITECTURE_MAP.md`. Validator passes: 0 errors.
  - NPM Security Audit deflake: the job's `npm ci` ran electron's `install.js` postinstall and flaked on a transient CDN 502. Added `ELECTRON_SKIP_BINARY_DOWNLOAD` / `CHROMEDRIVER_SKIP_DOWNLOAD` (npm audit needs only the dependency tree).
  - Docker builds (unmasked once upstream went green): both `Dockerfile.cloud` and `frontend/Dockerfile` ran `npm ci` before copying `scripts/`, so the `postinstall` (`scripts/patch-electron-builder.mjs`, a no-op off Windows) failed with "Cannot find module". Copy `frontend/scripts` before `npm ci` in both. Verified locally with `docker build --target frontend-builder`; CI Deploy "Build Docker Images" green.
- Anthropic provider package: the prior handoff note to add the `anthropic` package is closed as a non-issue — `sdk/UKG_Python_SDK/ukg_sdk/providers/anthropic.py` calls the Messages API over raw `httpx` with no SDK dependency.

Previous update: 2026-05-28

- Security/dependency remediation: frontend `tmp` transitive dependency is pinned through npm overrides, Python lockfile `idna` is updated, `npm --prefix frontend audit --audit-level=moderate` reports zero vulnerabilities, and GitHub Dependabot open-alert query returns no open alerts.
- Deploy/CI remediation: strict runtime precheck accepts explicit in-memory SQLite for disposable CI/runtime checks; KA-116 bulk-contract input coercion accepts scalar claims; TruthGate OPA policy respects Axis 14 threshold overrides; DRL convergence no longer overwrites a recovered refinement confidence when refinement steps fail; expanded persona pod outputs expose lane-level pod summaries; SQLite DMRF audit tests disable foreign-key checks while dropping cyclic test tables.
- Validation: `python -m pytest -q` passed with `1717 passed, 21 skipped`; targeted ruff and py_compile checks passed; commit hook ran repository ruff plus frontend lint and typecheck successfully.
- GitHub status at documentation update: Security Scan passed for `edbf0127`; CI/CD Pipeline and Deploy were rerunning on `edbf0127`.

Phased update plan:

| Phase | Scope | TODO items | Exit gate |
| --- | --- | --- | --- |
| Phase 1: Stop production blockers | Fix gateway authentication and migration-first deployment; remove shell-based static copy while touching deploy flow. | 1, 2, 7 | Done: `python -m pytest -q --no-cov tests/unit/test_api_gateway_auth.py tests/unit/test_deploy_phase1.py`; `python -m ruff check backend/api_gateway/api_gateway.py scripts/deploy.py tests/unit/test_api_gateway_auth.py tests/unit/test_deploy_phase1.py`. |
| Phase 2: Harden request perimeter | Add trusted proxy/host validation and harden active multimodal upload routes. | 3, 4 | Done: `python -m pytest -q --no-cov tests/unit/test_phase2_request_perimeter.py`; `python -m ruff check app.py backend/routes/multimodal_routes.py tests/unit/test_phase2_request_perimeter.py`. |
| Phase 3: Remove latent unsafe surfaces | Protect or remove security scan API and remove insecure legacy factory defaults. | 5, 6 | Done: `python -m pytest -q --no-cov tests/integration_routes/test_uncovered_blueprints.py::test_security_scan_api_requires_admin tests/integration_routes/test_uncovered_blueprints.py::test_security_scan_api_endpoints tests/integration_routes/test_uncovered_blueprints.py::test_security_scan_api_error_paths tests/unit/test_models.py::test_create_legacy_app tests/unit/test_models.py::test_create_legacy_app_requires_secrets_outside_pytest`; `python -m ruff check backend/security_scan_api.py backend/__init__.py tests/integration_routes/test_uncovered_blueprints.py tests/unit/test_models.py`. |
| Phase 4: Release evidence refresh | Re-run strict runtime precheck after schema initialization and refresh release evidence/docs. | 8 | Done: `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process`; `python scripts/verify_docs_references.py`. |

Priority order:

1. [x] Replace API gateway placeholder authentication with real token validation.
   - Evidence: `backend/api_gateway/api_gateway.py` now rejects unsigned placeholder tokens and validates signed JWT bearer tokens in `verify_token`.
   - Acceptance: JWT validation checks signature, expiration, optional issuer, optional audience, and optional authorization roles; negative tests cover missing, malformed, wrong-audience, and insufficient-role tokens.
2. [x] Replace production deployment `db.create_all()` behavior with migration-first deployment.
   - Evidence: `scripts/deploy.py` now runs `python -m flask db upgrade` in `run_database_migrations`.
   - Acceptance: production deploys run the migration system and fail when the migration command fails; `create_all()` remains reserved for disposable local/test bootstrap paths outside this deployment script.
3. [x] Add trusted proxy and host validation controls.
   - Evidence: `app.py` now gates proxy header trust behind `TRUST_PROXY_HEADERS=true`, validates request hosts against `TRUSTED_HOSTS`, and redirects HTTPS without trusting raw forwarded headers.
   - Acceptance: proxy header trust is environment-gated, trusted host/canonical-origin validation is enforced, and tests cover direct-backend requests with spoofed `Host`, `X-Forwarded-Host`, and `X-Forwarded-Proto`.
4. [x] Harden active multimodal upload routes.
   - Evidence: registered `/api/v1/multimodal/*` routes now validate uploads before processing and normalize public errors.
   - Acceptance: upload routes enforce per-route limits before processing, validate file type from content signatures, sanitize filenames, normalize public errors, and include abuse/rate-limit tests.
5. [x] Protect or remove the security scan API before any production registration.
   - Evidence: `backend/security_scan_api.py` now requires administrator authentication on scan/compliance endpoints.
   - Acceptance: endpoints require administrator auth if retained, unauthenticated/unauthorized tests assert `401`/`403`, and public errors do not expose internal exception details.
6. [x] Remove insecure fallback secrets from the legacy Flask app factory.
   - Evidence: `backend/__init__.py` now limits fallback secrets to pytest and raises outside tests when required secrets are missing.
   - Acceptance: defaults are pytest-only; non-test startup fails when required secrets are missing, or the factory is moved under test utilities.
7. [x] Replace shell-based static file copy in `scripts/deploy.py`.
   - Evidence: static collection now uses `pathlib` and `shutil`.
   - Acceptance: static collection no longer uses `cp -r`, `shell=True`, or shell glob behavior.
8. [x] Clear the strict runtime precheck action item and update release evidence.
   - Evidence: strict precheck now detects the Flask SQLite instance database path and passes with no action items.
   - Acceptance: ran the documented local schema initialization path, reran `python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process`, and updated release-readiness evidence with the passing output.

### Release Readiness

- [x] Finalize the in-app feature list used by `frontend/public/manifest.json`, `README.md`, and About pages. Current copy is conservative and aligned; manifest shortcuts now point to dashboard, chat, privacy controls, and provider settings.
- [x] Add or document keyboard navigation coverage across primary pages and modal/dialog workflows on the packaged Windows app.
- [ ] Production/public release only: execute NVDA screen reader compatibility checks on Windows using `reports/app-readiness/nvda-manual-checklist.md`.
- [ ] Production/public release only: provision a trusted production code-signing certificate in GitHub secrets and run `.github/workflows/release-installer-signing.yml` to produce signed release artifacts with signature reports.
- [ ] Production/public release only: prepare release checklist evidence: changelog entry, governance command output, CI/security scan review, artifact signing evidence, code-owner approval, rollback plan, and disaster recovery review. Local-first Phase 1 closure is documented in `reports/release-readiness/local-first-phase1-completion-2026-05-25.md`.

### Product And UX

- [x] Decide whether `/register` remaining disabled is the intended local-first behavior or whether web self-registration should be reopened as a future web-mode feature. Decision: keep disabled for the current local-first desktop build; reopen only as a future web-mode product requirement.
- [x] Audit MCP and admin screens for live-data versus static metric placeholders and update any placeholder controls before release. Evidence: `reports/app-readiness/ui-placeholder-audit.md`.
- [x] Verify toolbar actions route by route and either wire, hide, or document placeholder-only actions. The graph toolbar now routes search/help/settings/history/profile actions and hides unsupported export/notification controls.
- [x] Add public architecture assets under `docs/assets/readme/` for the external README.
- [ ] Keep screenshots refreshed when primary UI changes.

### API, Contracts, And Documentation

- [x] Tighten public API contracts, reduce legacy route aliases, and improve generated OpenAPI coverage.
- [x] Keep generated inventory docs (`docs/FILE_INVENTORY.csv`, `docs/GENERATED_STRUCTURE.md`) refreshed after repository cleanup/refactors.
- [x] Expand CI docs enforcement to include markdown linting for active files.
- [ ] Keep vendor guidance baseline (`docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md`) reviewed at least monthly.
- [x] Expand deployment reference material for Windows VM installation and the internal portable PostgreSQL, Redis, Neo4j, ChromaDB, object-store, and SQLite fallback stack.

### Runtime, Testing, And Operations

- [ ] Validate the simulation engine in a provider-backed staging environment.
- [ ] Expand comprehensive integration tests beyond current targeted route and readiness evidence.
- [ ] Configure production firewall rules and network security groups.
- [ ] Set up or document the production security incident response team.
- [x] Configure local desktop backup creation evidence for Phase H. Restore-drill automation remains a production operations item.
- [ ] Set up continuous security scanning review evidence for release.
- [ ] Set up performance benchmarking evidence.
- [ ] Configure compliance reporting automation.
- [ ] Document production blue-green deployment, disaster recovery, read-replica, and rollback procedures where applicable.
- [ ] Configure user analytics, usage tracking, A/B testing, feature flags, and chaos testing only if they remain product requirements for the target deployment.

### MCP And Connector Roadmap

- [x] Reconcile `docs/MCP_INTEGRATION.md` future items against implemented connector/OAuth/metrics work and close stale entries.
- [x] Add MCP sampling support for LLM completions if still required.
- [x] Add advanced MCP resource subscriptions and real-time update notifications.
- [x] Add external/remote MCP server connection management.
- [x] Add dynamic MCP plugin discovery and loading.
- [ ] Validate production connector operation against real external systems.

### Long-Term Research And Platform Roadmap

- [ ] Evaluate mobile applications only if mobile becomes a product requirement; historical research is retained in `docs/archive/research/REACT_NATIVE_RESEARCH.md`.
- [ ] Evaluate local SLM/model serving for L1/L2 tasks.
- [ ] Add multi-language/i18n support if required by target users.
- [ ] Expand richer user-facing trace and compliance overlay UX.
- [ ] Validate production-scale enterprise ingestion and vector-store workflows.
- [x] Phase 4 / DB-C: align RAG `knowledge_nodes` collection naming, add `scripts/index_knowledge_nodes.py`, wire startup empty-index detection, connect Chroma retrieval to TruthCore L3/L8/L9/L10, add local/offline embedding packaging, and expose Chroma collection counts through health/IPC.
- [x] Phase 5 / DB-R: implement Redis-backed TruthCache persistence, Redis subgraph cache, Redis embedding cache, TruthMemoryManager Redis selection, and Redis ping latency in health/IPC.
- [x] Phase C: wire quad-persona `PodOrchestrator`, L5 7-part persona construction, dynamic weighted synthesis, DRL convergence, desktop LocalSLM fallback, and quad analysis IPC status.
- [x] Phase DB-P: implement SQL historical reasoning calibration with TraceRun threshold history, TruthSession input embeddings, L9 DB similarity baselines, KAExecution timing persistence, and KA-036 p95 latency estimation.
- [x] Phase D prerequisite: write the DSQP technical disclosure before implementing the DSQP Protocol code.
- [x] Phase D first slice: write DSQP technical disclosure, implement offline deterministic DSQP chain/registry/orchestrator/validator, wire PersonaConstructionService and KA-012 to DSQP, expose SDK `DSQPClient`, and include templates in PyInstaller datas.
- [x] Phase E first slice: repair L10 registry/import shape, add executable L10-KA-001..007 modules, and route KA-116 entropy scoring through L10-KA-001.
- [x] Phase D follow-up: expose DSQP persona profiles through backend/Electron IPC, render desktop persona cards, and add deterministic 18-question DSQP benchmark report.
- [x] Phase E follow-up: complete E-9..E-14 with KA-014 domain calibration, KA-023 domain lambdas, KA-002 deterministic 3-branch BFS decomposition, KA-022 six-dimensional Axis 15 risk schema, PyInstaller L10 collection, and focused tests.
- [x] Phase D live evidence: provider-backed end-to-end flow confirmed `dsqp_chain` appears in persisted audit events via `reports/dsqp_provider_audit_report.json`.
- [x] Phase F first slice: implement DMRF Python control-plane package with 17-axis routing, tier classification, convergence/evidence policy, injection defense, DSQP/FROST wiring, Truth subsystem adapters, optional gateway flag, desktop status IPC, and focused tests.
- [x] Phase F completion: add DMRF Redis Streams-compatible TruthLink publishing, MLflow/local tracking, Prometheus metrics, SQLite audit persistence evidence, standalone validation report, and Rust F2 no-build decision based on current Python timing.
- [x] Cross-phase VM/database correction: audit previous DB-N/DB-C/DB-R/DB-O/Phase F/G/H planning and storage runtime paths for external-database assumptions; enforce internal app-owned database selection in `ConnectionManager`, `VectorStore`, and `ObjectStore`; update deployment/security/architecture docs to define Windows VM as the same Windows app stack.
- [x] DB-O first slice: add TruthAuditEvent object-store/blockchain fields, write TruthMemory audit bundles to `audit_logs`, compute Merkle roots, and anchor Tier 3+ audit events with local simulated blockchain receipts when no node/key is configured.
- [x] DB-O completion: persist FROST snapshots to `simulation_artifacts`, DSQP construction outputs to `deliverables/dsqp`, and object-store bucket counts/byte totals through `/health` and Electron `get-db-status`.
- [x] DB-M completion: add `UnifiedMemoryService`, persist StructuredMemoryGraph to `databases/memory/memory_graph.json`, wire TruthCore L1-L10 memory recall/consolidation, L10 Lane B memory commits, FROST memory checkpoints, and memory stats through `/health` plus Electron `get-db-status`.
- [x] Phase G-A completion: add local TruthMemory MLflow/JSONL tracking, TruthGate OPA/Rego policy evaluation fallback, W3C PROV-JSON audit records, active MCP sampling and resource subscription SSE, and SDK v0.5.0 offline DSQP/coordinate resolver packaging.
- [x] Phase G-B completion: add optional TruthLink Redis Streams XADD/XREAD, TruthMemory 7-year local archive routing, opt-in TruthGate enhanced model screening fallback, and ADR-0002 documenting PQ-gRPC as VM-only research with no desktop dependency.
- [x] Phase H first slice: add Eclipse Temurin JRE 17 setup/bundling path, prioritize `databases/jre` for Neo4j, add backend network status + Electron IPC/local model status, gate desktop window creation on `/health`, and restart backend up to three times on unexpected exit.
- [x] Phase H completion: implement desktop offline queue/replay, LocalSLM audit metadata, dedicated live reasoning/KA IPC feeds, trace panel active KA/persona confidence/FROST enrichment, detailed settings database metrics, one-click backup flow, PyInstaller desktop-module inclusion, and reproducible cold-start/packaging evidence.
- [ ] Validate production alerting evidence for `/health`, `/live`, `/ready`, `/metrics`, Sentry, and admin dashboards.
- [ ] Harden multi-tenant operations, cost controls, recursive persona evaluation, dynamic persona expansion, human feedback loops, automated axis learning, quantum-ready node research, and policy-as-code governance for larger deployments.

## Completed Local Stack QC (Phase 6 — 2026-05-15)

All five internal databases have been wired, seeded, and mutually validated in local QC mode. No cloud or external dependencies required.

| Check | Status |
| --- | --- |
| PostgreSQL migrations current | Done — `flask db current` resolves to head; `correlation_id` and `estimated_cost_usd` columns added via `d1e2f3a4b5c6` migration |
| All tracked tables exist | Done — 64 models fully migrated |
| TraceRun AuditBundle columns added | Done — `layers_executed`, `refinement_cycles`, `regulatory_pass`, `security_pass`, `truthgate_decision`, `token_cost`, `latency_ms`, `evidence_pack_hash`, `coordinate17_id` |
| Redis live | Done — Redis on port 6379 responds; session and rate-limit storage functional |
| Neo4j pillar seed | Done — `scripts/seed_neo4j.py` seeds pillar taxonomy + `HONEYCOMB_BRIDGE` crosswalk edges |
| ChromaDB collections initialized | Done — `knowledge_nodes`, `persona_profiles`, `citation_cache`, `audit_evidence` collections created at startup |
| Object storage buckets initialized | Done — `audit_logs`, `simulation_artifacts`, `deliverables`, `graphs`, `eval_data` buckets pre-created at startup |
| End-to-end Tier 2 gateway query | Done — 200 OK with `[UKG Audit Trace]` footer in response body |
| TruthAuditEvent hash-chain receipt | Done — `TruthAuditEvent` row written with valid `hash_chain` and `previous_hash` after each Tier 2+ run |
| F-CONF-01 confidence formula | Done — `TraceRun.confidence` set by `ConfidenceCalculator` (evidence × KA × persona × gate weighting), not raw LLM output |
| Circular import fixes | Done — `core/axes/axis1_knowledge.py`, `axis12_location.py`, `axis13_time.py` migrated to `from extensions import db` |
| `db.session.flush()` before FK child rows | Done — `TraceStage.run_id` now populated correctly after `TraceRun` flush |
| Audit footer coordinate guard | Done — `_audit_footer` coerces non-dict `coordinate` to `{}` before attribute access |
| TruthAuditEvent session_id FK | Done — `TruthMemoryCommitService` passes `session_id=None` (nullable column; no `truth_sessions` row in this flow) |
| Local database setup script | Done — `scripts/setup_local_databases.py` installs PostgreSQL 16, Redis, and Neo4j binaries |
| GraphStore schema constraints | Done — `ensure_schema()` creates `Pillar` and `KnowledgeNode` uniqueness constraints and code/axis indexes on connect |
| Vector store collection init | Done — `initialize_collections()` called at startup via `app.py` |
| Object storage bucket pre-creation | Done — called at startup via `app.py` |

## Completed Application-Readiness Work

| Area | Evidence |
| --- | --- |
| Privacy policy drafted | `docs/PRIVACY_POLICY.md` |
| Privacy policy published in-app | `frontend/app/legal/privacy/page.tsx` |
| AI limitations page | `frontend/app/about/ai-limitations/page.tsx` |
| Cloud services page | `frontend/app/about/cloud-services/page.tsx` |
| Cloud disclosure banner | `frontend/components/CloudDisclosureBanner.tsx` |
| AI output labels | `frontend/components/Chat/MessageBubble.tsx` |
| Provider/model shown per response | `frontend/components/Chat/MessageBubble.tsx` |
| User data export endpoint | `routes/user_data_routes.py` |
| User data deletion endpoint | `routes/user_data_routes.py` |
| Privacy controls page | `frontend/app/settings/privacy/page.tsx` |
| Privacy links in settings and footer | `frontend/app/settings/page.tsx`, `frontend/app/layout.tsx` |
| AI processing toggle | `frontend/components/settings/AiModelSettings.tsx` |
| Chat history opt-out toggle | `frontend/components/settings/AiModelSettings.tsx` |
| Automated accessibility audit command | `frontend/package.json` (`test:a11y:ci`) |
| Authenticated WCAG 2.1 A/AA route evidence | `frontend/scripts/run-a11y-ci.mjs`, `reports/app-readiness/a11y-ci-report.json` |
| Failure-mode/export-delete Playwright evidence | `frontend/tests/e2e/app-readiness-evidence.spec.ts`, `reports/app-readiness/playwright-app-readiness-report.json` |
| Keyboard navigation evidence | `frontend/tests/e2e/keyboard-navigation-evidence.spec.ts`, `reports/app-readiness/keyboard-navigation-report.json` |
| NVDA manual screen reader checklist | `reports/app-readiness/nvda-manual-checklist.md` |
| UI placeholder audit | `reports/app-readiness/ui-placeholder-audit.md` |
| Local release evidence | `reports/release-readiness/local-release-evidence-2026-05-23.md` |
| Conservative copy/disclosure pass | `frontend/public/manifest.json`, `frontend/app/about/page.tsx`, `frontend/app/about/ai-limitations/page.tsx`, `frontend/app/about/cloud-services/page.tsx`, `frontend/app/legal/privacy/page.tsx`, `frontend/components/Chat/ChatInterface.tsx`, `frontend/components/settings/AiModelSettings.tsx`, `frontend/components/CloudDisclosureBanner.tsx`, `docs/PRIVACY_POLICY.md` |

## Documentation Cleanup Policy

- Keep current planning in this file only.
- Keep release go/no-go criteria in `docs/RELEASE_CHECKLIST.md`.
- Keep active documentation discoverable from `README.md` and `docs/README.md`.
- Do not add new `PROJECT.md`, `ROADMAP.md`, `current_plan.md`, assessment TODOs, or archived planning summaries without first folding actionable items into this file.
