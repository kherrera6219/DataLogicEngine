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
**Status:** NOT STARTED  
**Prerequisite:** Sprint 2 exit gate

### Kevin decisions required before coding

| Decision | Context |
|---|---|
| **SC-6: Encryption algorithm** | Decision implemented: upgrade `backend/security/encryption_manager.py` so new field-level payloads use AES-256-GCM while legacy `Fernet-AES-128-CBC` registry entries remain decryptable. Active docs now describe the implemented algorithm consistently. |

### Tasks

| ID | Task | What to implement |
|---|---|---|
| SC-1 | Real security compliance check | Key loaded + not expired + audit dir writable |
| SC-2 | Real availability check | DB connection + no exception spike |
| SC-3 | Real processing integrity check | Last hash chain valid + migration at head |
| SC-4 | Real confidentiality check | Key not dev value + no PII in plain audit log |
| SC-5 | Real privacy check | Export + deletion endpoints reachable; AI toggle wired |
| SC-6 | Encryption decision + fix | Code and all docs describe same algorithm consistently |

**Exit gate:** All 5 compliance checks have real logic, no stub returns, code and docs agree on encryption algorithm, pytest green.
