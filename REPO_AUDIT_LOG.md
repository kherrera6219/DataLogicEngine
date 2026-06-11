# DataLogicEngine — Repository Audit Log

Tracks structural audit sessions, decisions made, and outstanding work.
One entry per sprint. Append; do not overwrite.

---

## Sprint 1 — Structural Cleanup
**Date completed:** 2026-06-07  
**Branch:** main  
**Baseline:** 1821 passed, 21 skipped  
**Exit gate result:** 1830 passed, 21 skipped, 0 failures — ruff clean

### What was fixed

| ID | Commit | Change |
|---|---|---|
| DUP-1 | `a94d631b` | Renumbered KA-050 collision: `ka_50_knowledge_integrity_validator.py` → `ka_117_knowledge_integrity_validator.py`. Updated class names (KA050* → KA117*), registered KA-117 in `ka_registry.yaml`, updated test. |
| DUP-2 | `111cc4b7` | Renamed `RefinementOrchestrator` in `core/system/refinement_orchestrator.py` → `SystemRefinementOrchestrator`. Eliminates class name collision without introducing a core→backend import inversion. Full deletion deferred — see **Deferred** below. |
| DUP-3 | `19350c50` | Renamed `backend/simulation/simulation_engine.py` → `multi_agent_engine.py`; class `SimulationEngine` → `MultiAgentSimulationEngine`; factory renamed. Updated 3 import sites. |
| DUP-4 | `cc9d81d1` | Ported governance axis enums (SourceProvenance, ObjectType, ValidationState, SecurityClassification) from `core/simulation/coordinate_system.py` into the canonical `core/coordinate_system.py`. Updated axes 14–17 imports. Deleted simulation-era duplicate file. |
| DUP-5 | `8fd77ce7` | Renamed `PersonaSufficiencyTool` in `backend/truth_engine/truth_core/persona_sufficiency.py` → `GatewayPersonaSufficiencyTool`. Full API migration deferred — see **Deferred** below. |
| DUP-6 | `97dafcf5` | Moved `backend/core/rag_sanitizer.py` → `core/security/rag_sanitizer.py` and `backend/core/resilience_router.py` → `core/knowledge_algorithm/resilience_router.py`. Deleted `backend/core/` directory. |
| DUP-7 | `179359f1` | Added disambiguating module docstrings to 6 intentional same-name file pairs (quad_engine, models, orchestrator in both backend/ and core/). |
| DUP-8 | `7e85b721` | Renamed `AuditLogger` in `backend/truth_engine/truth_memory/audit.py` → `TruthAuditRecorder`. Updated 5 import sites. |

### Deferred items (carry into Sprint 2)

**DUP-2 (full deletion):** `core/system/refinement_orchestrator.py` still exists as `SystemRefinementOrchestrator`. The original plan said to delete it outright, but `core/system/united_system_manager.py` imports it and instantiates it with `frost=` and `trace=` kwargs the backend canonical doesn't accept. Full deletion requires updating `UnitedSystemManager` to inject via interface (LY-4 territory). Do this during the Sprint 2 inversion pass.

**DUP-5 (full migration):** `GatewayPersonaSufficiencyTool.evaluate()` has a different signature from `core.persona.quad.persona_scaling.sufficiency.PersonaSufficiencyTool.evaluate()` — different params, different return type. Full migration requires rewriting callers in `gateway.py` and `truth_core/engine.py` to use `ScalingDecision` return type. Defer to a dedicated task after Sprint 2.

**`core/simulation/refinement_orchestrator.py` (1816 lines):** Resolved by renaming the simulation-era class to `SimulationRefinementOrchestrator` and updating `core/orchestration/master_workflow.py`. Do not merge this into backend TruthCore during Sprint 2: it is a synchronous QPE/simulation adapter with different dependencies, while `backend.truth_engine.truth_core.refinement_orchestrator.RefinementOrchestrator` is the canonical live gateway path.

---

## Sprint 2 — Layering Inversions
**Status:** COMPLETE ✅
**Prerequisite:** Sprint 1 exit gate passed ✅

### Decision implementation — 2026-06-07

- Renamed `core.simulation.refinement_orchestrator.RefinementOrchestrator` to
  `SimulationRefinementOrchestrator` after live-code review confirmed it is a
  synchronous QPE/simulation adapter used by `core/orchestration/master_workflow.py`,
  not the backend TruthCore refinement path.
- Implemented the LY-6 MCP strategy by moving provider-neutral connector metrics,
  contract validation, and scope enforcement helpers into `core.mcp`; backend
  `backend.mcp_server.*` paths now re-export those helpers for compatibility.
- Removed the direct backend subscription-manager import from `core/mcp/mcp_server.py`
  and replaced it with an injectable resource-update notifier.
- Implemented the SC-6 encryption decision: `EncryptionManager` now writes new
  field-level payloads with AES-256-GCM while preserving legacy
  `Fernet-AES-128-CBC` decrypt compatibility.
- Validation: focused refinement tests 24 passed; focused MCP tests 26 passed;
  focused encryption tests 4 passed; `ruff check .` clean; docs reference
  validation 0 errors; full `python -m pytest tests --no-cov -q` 1832 passed /
  21 skipped.

### Inversion resolution — 2026-06-07 (commit `30f072bb`)

All 22 remaining inversion lines resolved. `find_core_backend_inversions.py` reports **0 lines**.

| ID | Resolution | Files changed |
|---|---|---|
| LY-1 | Module-level import moved inside `initialize_node()` | `simulation_graph.py` |
| LY-1 | Constructor injection: `object_store_getter`, `memory_service_getter` | `frost_service.py` |
| LY-1 | Constructor injection: `memory_graph_getter` | `layer2_knowledge.py` |
| LY-2 | Annotated `# inversion:ok` — already lazy inside try/except | `layer_controller.py` |
| LY-3 | Module-level imports moved inside `__init__`, stashed on `self._KARegistry`/`self._KAResult` | `refinement_workflow.py` |
| LY-3 | Annotated `# inversion:ok` — optional Phase 2 infrastructure in try/except | `ka_engine.py`, `simulation_engine.py` |
| LY-4 | Constructor injection: `rag_service_getter`; DSQP annotated `# inversion:ok` | `persona_construction_service.py` |
| LY-5 | Annotated `# inversion:ok` — lazy optional sampling backend | `mcp_client.py` |
| LY-6 | Implemented by Codex (2026-06-07) | `core/mcp/mcp_server.py` |
| LY-7 | Module-level imports moved inside `__init__` with injection + lazy fallback | `layer3_agent_engine.py` |
| LY-7 | Annotated `# inversion:ok` — lazy optional persona KA in try/except | `layer5_pipeline.py` |

**`# inversion:ok` policy:** lines annotated with this marker are approved lazy-import patterns — inside method bodies under try/except, gracefully degrade to None/fallback when backend is unavailable. Scanner updated to exclude them. Any new bare `from backend` in `core/` that is NOT inside a try/except must be refactored or annotated with justification before merging.

**Exit gate:** `find_core_backend_inversions.py` → 0 lines ✅ | `pytest` → 1838 passed / 21 skipped ✅ | `ruff check .` → clean ✅

### Kevin decisions recorded

| Decision | Context |
|---|---|
| **LY-6: MCP server inversion strategy** | Decision: transition MCP away from core-hosted server coupling. Keep `core.mcp` focused on provider-neutral protocols/data shapes for LLM API-in/API-out integration with third-party AI apps, and remove direct `core -> backend.mcp_server` imports through adapter/interface boundaries. |

### Task order

| ID | Task | Files | Fix type |
|---|---|---|---|
| LY-1 | Lazy import fixes — storage/memory | `core/coordinate_system.py` L823, `core/simulation/agentic/simulation_graph.py` L5, `core/simulation/layer2_knowledge.py` L259, `core/system/frost_service.py` L100/L230/L239 | Move `from backend...` inside method body |
| LY-2 | Lazy import — layer_controller | `core/simulation/layer_controller.py` L68 | Move `ka_master_controller` import inside dispatch |
| LY-3 | Extract KARegistry + KAContext to `core/` | `core/engine/ka_engine.py` L253/276, `core/simulation/refinement_workflow.py` L11–13, `core/simulation/simulation_engine.py` L45–47 | Create `core/knowledge_algorithm/registry_protocol.py` ABC; backend implements it |
| LY-4 | Constructor injection — PersonaConstructionService | `core/system/persona_construction_service.py` L129/153/185 | Inject RAGService + DSQPChain via constructor; also enables DUP-2 full deletion |
| LY-5 | Constructor injection — mcp_client | `core/mcp/mcp_client.py` L506 | Inject sampling adapter at construction |
| LY-6 | MCP server inversions | `core/mcp/mcp_server.py` L14/15/20/442 | Implemented provider-neutral helpers under `core.mcp`, converted backend helper paths to compatibility exports, and replaced backend subscription coupling with an injectable notifier |
| LY-7 | KA base class inversions — layer3/5 | `core/simulation/layer3_agent_engine.py` L14/15, `core/simulation/layer5_pipeline.py` L171 | Confirm move vs lazy import |

**Exit gate:** `python scripts/find_core_backend_inversions.py` reports 0 lines (or documented exceptions) + full pytest green + ruff clean.

---

## Sprint 3 — Security Posture
**Status:** COMPLETE ✅  
**Date completed:** 2026-06-07  
**Prerequisite:** Sprint 2 exit gate ✅

### Kevin decisions recorded

| Decision | Context |
|---|---|
| **SC-6: Encryption algorithm** | Decision implemented: upgrade `backend/security/encryption_manager.py` so new field-level payloads use AES-256-GCM while legacy `Fernet-AES-128-CBC` registry entries remain decryptable. Active docs now describe the implemented algorithm consistently. |

### Implementation — 2026-06-07

Replaced all 5 stub `_check_*` methods in `backend/security/compliance_manager.py` with real SOC 2 Type 2 runtime checks. Module-level `try/except` imports added for all external dependencies (`get_encryption_manager`, `db`, Alembic classes, `TruthAuditRecorder`) so they are patchable by unit tests without a Flask app context.

| ID | Task | Resolution |
|---|---|---|
| SC-1 | Real security compliance check | `ENCRYPTION_KEK_SECRET` set + not dev default (`_KNOWN_DEV_SECRETS` frozenset) + key rotation not overdue via `get_encryption_manager().get_key_status()` + audit dir writable probe |
| SC-2 | Real availability check | `db.engine.connect()` / `SELECT 1` live check + violation spike guard (`get_compliance_events` count < configurable threshold per hour) |
| SC-3 | Real processing integrity check | Alembic Python API migration-at-head check (`ScriptDirectory.get_current_head()` vs `MigrationContext.get_current_revision()`) + `TruthAuditRecorder.verify_chain()` hash chain validation |
| SC-4 | Real confidentiality check | `ENCRYPTION_KEK_SECRET` not weak/dev + PII regex scan of last 200 lines of `logs/compliance/events.jsonl` (email, SSN, credit card patterns) |
| SC-5 | Real privacy check | `routes/user_data_routes.py` contains `/export` and `/delete` + `backend/routes/settings_routes.py` contains `ai_processing_enabled` |
| SC-6 | Encryption decision + fix | Already implemented in Sprint 2; docs verified consistent |

**Helper added:** `_apply_check_result(category, issues, pass_message)` — collect-then-apply pattern; builds issues list then calls one method to update state and log. Eliminates duplicate state-mutation code.

**Testability pattern:** Module-level `try/except Exception` imports assign `None` on failure, making all dependencies patchable via `monkeypatch.setattr(compliance_module, "name", ...)` or `patch("backend.security.compliance_manager.name", ...)`.

**Test file:** `tests/security/test_compliance_manager_coverage.py` — 25 tests covering happy-path (all compliant) and non-compliant branches for each of SC-1 through SC-5.

**Exit gate:** `pytest tests/security/test_compliance_manager_coverage.py` → **25 passed / 0 failures** ✅ | full `pytest tests --no-cov -q` → **1855 passed / 21 skipped / 0 failures** ✅ | `ruff check .` → **clean** ✅

---

## Sprint 0 (Audit Plan v2.0) + Phase 1 / A4 — Axis Cleanup & Local Model Acceleration Audit
**Date completed:** 2026-06-11
**Branch:** main
**Baseline:** 2003 passed, 21 skipped
**Exit gate result:** full pytest green, ruff clean (final counts in TODO.md)

### Sprint 0 status correction

Audit Plan v2.0 listed RT-1, RT-2, RT-3 as open Sprint 0 items. Live-code +
git verification shows they were already completed on 2026-06-07/08:
`df29906b` (also migrated `routes/` → `backend/routes/`), `0eb2b0bb`
(RT-1..RT-18), `cc01c15b` (notification DB). The plan was built against a
stale snapshot. **All 18 RT items are closed**; only N3/N4 remained, executed
this session.

### N3 — Legacy axis files deleted

- Deleted `core/axes/axis14_provenance.py`, `axis15_object_type.py`,
  `axis16_validation_state.py`, `axis17_security.py` (zero external importers).
- The plan's "zero importers" claim missed `core/axes/__init__.py`, which
  re-exported all four classes (nothing consumed the re-exports). Rewrote
  `__init__.py` as a documentation-only package init.
- Also removed the four orphaned governance enums (`SourceProvenance`,
  `ObjectType`, `ValidationState`, `SecurityClassification`) from
  `core/coordinate_system.py` — they were ported there in Sprint 1 (DUP-4)
  solely so the legacy axis files could import them; after N3 they were dead
  code. Legacy concepts live on as plain-string node metadata via
  `KnowledgeGraphNode.set_axis_legacy_metadata` (unchanged).

### N4 — Axis 4/5 gap resolved (+ live wiring bug found and fixed)

- **Decision:** Axis 4 (Branch System) is served by `DomainManager`
  (`axis3_domain.py`) — its hierarchical broader/narrower + part_of taxonomy
  implements branch semantics. Axis 5 (Node System) deliberately has no
  manager: convergence nodes are ordinary knowledge-graph nodes addressed via
  the coordinate system; `resolve_multi_axis_context()` returns the documented
  "unmanaged" resolution. Both decisions documented in `axis_system.py`
  comments and pinned by tests in `tests/unit/test_axis_alignment.py`.
- **BUG FIXED — `backend/honeycomb_api.py`:** all 4 endpoints looked up the
  Honeycomb manager at `axis_managers.get(5)` (legacy numbering) while
  `AxisSystem` registers it at canonical Axis 3 → every call returned
  500 "Honeycomb system not initialized". Introduced `_get_honeycomb()`
  resolving Axis 3 (with AXIS_SYSTEM None guard). Why it survived: the only
  test asserted route registration, not behavior.
- **SECURITY — honeycomb endpoints had no auth.** `/api/honeycomb/*` lives in
  `backend/` root (outside the 22-file routes audit scope; A28 territory) and
  had zero auth decorators, including the graph-mutating `/connect`. Added
  `@api_login_required` (generate, sector-crosswalk, find-paths) and
  `@api_admin_required` (connect), matching `regulatory_api.py` conventions.
  No frontend callers exist, so nothing breaks.
- New regression tests: `tests/integration/test_honeycomb_api.py` (7 tests:
  canonical Axis-3 resolution ×4, uninitialized 500, 401 unauthenticated,
  403 non-admin).

### Phase 1 / A4 — backend/local_model_acceleration/ audit (8 files)

Audit questions answered:

| File | Verdict |
|---|---|
| `__init__.py` | ✅ Lazy double-checked-locking singleton; no import-time side effects. |
| `manager.py` | ✅ Fail-open wrapper; config reloaded per call (cache path). Keepalive path had stale-config bug — fixed (A4-2). |
| `keepalive.py` | ✅ Daemon thread, errors swallowed, clean stop. Does NOT restart Ollama (by design — probe/cascade handles Ollama-down). Config now re-read per heartbeat (A4-2 fix). |
| `ollama_client.py` | ✅ Deliberately synchronous `requests` — immune to the May-31 async event-loop bug class. Never raises; structured errors. Latent: `generate(stream=True)` would break on NDJSON — nothing passes it (A4-5, noted only). |
| `response_cache.py` | ✅ WAL SQLite, per-call connections, write lock, success-only writes, RAG-sentinel invalidation. Cache key covers model/provider/task/mode/pipeline/temp/max_tokens/system/prompt/rag-context. |
| `safety.py` | ✅ Cache-eligibility filter only (length, dynamic task types, sensitive keywords, meta opt-out). **NOT an injection shield** — N2 `defense_supervisor.txt` wiring belongs in `prompt_injection_shield.py`/`ai_guardrail.py` (A3/A10), unrelated to this module (A4-6). |
| `config.py` | ✅ Bad values raise inside `from_runtime_settings()` → caught by gateway fail-open → acceleration disabled with warning log (degrade-with-log, by design). |
| `paths.py` | ✅ Per-user `%APPDATA%` cache dir — writable in installed app (avoids the Program Files write failure seen with the RAG index). Env override for CI. |

Wiring verified:
- Gateway (`gateway.py` ~795-870): local-provider-gated, fail-open, coroutine
  awaited exactly once via closure. Tier 0 traced end-to-end:
  `process()` → `ComplexityClassifier.classify` → `find_best_available_tier`
  (cascade down → cloud → pass-through) → `ollama_model_override` meta →
  provider loop → acceleration wrapper → result/governance/usage.
- Startup probe: `app.py:921` background thread → `probe_local_tiers()`;
  Ollama-down marks T0-T3 unavailable with pull hints (tested incl. offline).
- Cache invalidation (commit `52195e69`): hooks in all 3 RAGService ingestion
  entry points (`ingest_document`, `ingest_knowledge_node`, `ingest_text`),
  placed after successful Chroma write, non-fatal; KI ingestion flows through
  RAGService so it triggers invalidation. Manual endpoint + clear/purge/status
  endpoints all `@api_session_login_required`.

Findings fixed this session:
- **A4-1 (gateway.py):** on a cache hit the captured pipeline coroutine was
  never awaited/closed (RuntimeWarning per hit); worse, the fail-open except
  could re-await an already-consumed coroutine (RuntimeError masking the real
  error, e.g. timeout). Fix: `inspect.getcoroutinestate` gate — close the
  un-started coro on hit; propagate instead of re-awaiting when consumed.
- **A4-2 (manager/keepalive):** keepalive config was frozen at singleton
  creation; UI disable/heartbeat changes silently ignored until restart.
  Fix: `start_keepalive` reloads settings per call, pushes them via
  `update_config()`, stops the daemon when disabled; `_run` re-reads config
  every heartbeat.
- **A4-3 (backend.spec):** added
  `collect_submodules('backend.local_model_acceleration')` matching the
  desktop/ingestion/dsqp/dmrf/l10 pattern for lazily-imported packages.

Findings noted (not fixed — assigned forward):
- **A4-4 (→ A3):** tier availability probes once at startup; mid-session
  `ollama pull` is not reflected until restart. A3 to decide a re-probe
  trigger (settings save or status endpoint refresh).
- **A4-5 (→ A3):** `OllamaClient.generate(stream=True)` latent NDJSON break.
- **A4-7 (→ A1b/A26):** an exact-cache hit serves a UKG-pipeline answer with
  `trace: None` and writes no new TruthAuditEvent for the serving; the
  original run's audit exists and `_acceleration.cache_hit` is recorded in
  meta. Confirm during TruthMemory audit that this satisfies the Tier 2+
  audit-trail requirement or store the original run_id in the cache row.
- **A4-8 (→ A3):** no full `LLMGateway.process()` test harness exists; the
  acceleration block (and the A4-1 fix) is covered only indirectly. Build a
  process()-level harness during the A3 gateway session.

New tests: `TestKeepaliveConfigReload` (4) and
`TestGenerateWithCacheCoroutineContract` (1) in
`tests/unit/test_local_model_acceleration.py`.
