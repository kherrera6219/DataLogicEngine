# DataLogicEngine — Full Audit & Sprint Plan v2.0
**Date:** June 7, 2026 | **Branch:** main | **Scope:** Live code scan — no assumptions from notes

---

## What Changed From v1.0

The previous plan (v1.0) was built from audit log notes and prior session summaries. This version was built from **live code scans run on the current repo**:

- `scripts/find_core_backend_inversions.py` — confirmed 26 inversion lines across 13 files
- `scripts/audit_duplicates.py` — found 8 module name collisions, 17 duplicate class names, 2 cross-tree function duplicates, 278 backend files with no Flask/DB markers
- `scripts/audit_deep.py` — inspected each collision: line counts, importer lists, actual class definitions

The v1.0 plan did **not** cover duplicate detection or file misplacement. This plan adds that as the primary new scope.

---

## Executive Summary — What Was Found

| Category | Count | Severity |
|---|---|---|
| `core → backend` import inversions | 26 lines / 13 files | HIGH — structural |
| Module name collisions (same filename in both trees) | 8 | HIGH — confusion / wrong import risk |
| Duplicate class definitions (same class name, multiple files) | 17 | HIGH — ambiguity about which is canonical |
| Duplicate factory functions (cross-tree) | 2 | HIGH |
| `backend/core/` subdirectory (core logic inside backend) | 2 files | MED — misplaced |
| `backend/` files with no Flask/DB markers (candidates for `core/`) | 278 | MED — most are correct where they are, ~20 are genuinely misplaced |
| KA-050 number collision (two completely different KAs with same ID) | 2 files | HIGH — breaks registry |
| `compliance_manager.py` unconditional "compliant" stub | 1 | SECURITY |
| `EncryptionManager` code vs docs mismatch (Fernet vs AES-256-GCM) | 1 | SECURITY |

---

## Part 1 — Duplicate & Misplaced File Findings

### 1A. Module Name Collisions

Eight filenames exist in both `backend/` and `core/`. Not all are problems — some are intentional shims — but each needs a verdict.

| Filename | backend/ path | core/ path | Verdict |
|---|---|---|---|
| `integrity.py` | `backend/security/integrity.py` (29 lines) | `core/security/integrity.py` (51 lines) | **Already resolved.** backend version is a confirmed backwards-compatible re-export shim (commit `2ee572d9`). Canonical = `core/security/integrity.py`. Keep shim until all import sites migrated, then remove. |
| `location_context_engine.py` | `backend/location_context_engine.py` (18 lines) | `core/simulation/location_context_engine.py` (537 lines) | **Already resolved.** backend version is an explicit wrapper that calls `super().__init__()` on the core class. Canonical = `core/simulation/`. Wrapper exists for legacy compatibility only — track importers and remove when zero. |
| `quad_engine.py` | `backend/quad_persona/quad_engine.py` (345 lines) | `core/persona/quad/quad_engine.py` (473 lines) | **Intentionally separate.** backend version = gateway-only async LLM-consultation path (mode="quad"). core version = shared library with deterministic local fallback. Both load-bearing. Different responsibilities. Document clearly; do not merge. |
| `models.py` | `backend/dmrf/models.py` | `core/persona/quad/models.py` | **Different domains.** DMRF result models vs quad persona data models. No conflict — Python module paths are distinct. Add module docstrings making the domain explicit. |
| `orchestrator.py` | `backend/dmrf/orchestrator.py` | `core/simulation/orchestrator.py` | **Different domains.** DMRF routing orchestrator vs simulation step orchestrator. Same as above — distinct paths, add docstrings. |
| `refinement_orchestrator.py` | `backend/truth_engine/truth_core/` (158 lines) | `core/simulation/` (1816 lines) AND `core/system/` (105 lines) | **3-way collision — ACTION REQUIRED.** See section 1B. |
| `simulation_engine.py` | `backend/simulation/` (325 lines) | `core/simulation/` (1380 lines) | **2 different engines — ACTION REQUIRED.** See section 1B. |
| `exceptions.py` | `backend/utils/exceptions.py` | `core/knowledge_algorithm/exceptions.py` | **Different domains.** HTTP/API exception types vs KA execution exceptions. No conflict. Add docstrings. |

---

### 1B. Critical Duplicate Classes — Detailed Verdicts

These are the high-priority cases where the same class name exists in multiple live files and importers are split across both.

---

#### RefinementOrchestrator — 3 definitions

| File | Lines | Purpose (from code) |
|---|---|---|
| `backend/truth_engine/truth_core/refinement_orchestrator.py` | 158 | 12-step refinement with KA IDs (`KA-001`, `KA-017`, `L10-KA-003`...). Integrated into `truth_core/engine.py`. **Live pipeline.** |
| `core/simulation/refinement_orchestrator.py` | 1816 | Full 12-step orchestrator with `graph_manager`, `memory_manager`, `united_system_manager`, `ka_loader` constructor. Original simulation-era implementation. |
| `core/system/refinement_orchestrator.py` | 105 | Thin wrapper. Steps listed as strings (`"S1: Arrow of Time"`). Uses `UnifiedArtifactEnvelope`. Appears to be a scaffold/stub. |

**Verdict:**
- **Canonical = `backend/truth_engine/truth_core/refinement_orchestrator.py`** — this is what the live gateway calls via `truth_core/engine.py`
- `core/system/refinement_orchestrator.py` — 105-line scaffold, no real implementation, no live importers beyond the importer-count noise. **Remove.**
- `core/simulation/refinement_orchestrator.py` — 1816-line original with a different constructor signature. Used by the simulation-era path. Decide: merge its logic into the backend canonical, or keep as the simulation-path orchestrator with a distinct class name (e.g. `SimulationRefinementOrchestrator`). Do not leave two classes with the same name.

---

#### SimulationEngine — 3 definitions

| File | Lines | Purpose |
|---|---|---|
| `backend/simulation/simulation_engine.py` | 325 | "PRODUCTION VERSION" — multi-agent counterfactual simulation using LLM gateway calls. Has `SimulationEvent`, `SimulationResult`, `SimulationEngine`. |
| `core/simulation/simulation_engine.py` | 1380 | Full FROST 10-layer simulation engine. The one imported by `truth_core/engine.py` and the gateway. **The live pipeline engine.** |
| `core/simulation/legacy_simulation_engine.py` | 299 | Explicitly named legacy. Confirmed load-bearing (imported by `persona_api.py`, `truth_engine/api.py`, 3 test files). |

**Verdict:**
- **Canonical = `core/simulation/simulation_engine.py`** (1380 lines) — this is what the live reasoning pipeline calls
- `backend/simulation/simulation_engine.py` — "PRODUCTION VERSION" comment is misleading. It is a different, narrower multi-agent sim used by `backend/truth_engine/api.py` simulation routes. Rename to `MultiAgentSimulationEngine` and move to `backend/simulation/multi_agent_engine.py` to eliminate the name collision
- `core/simulation/legacy_simulation_engine.py` — keep but audit test coverage; when tests no longer need it, remove

---

#### QuadPersonaEngine — 2 definitions

| File | Lines | Importers |
|---|---|---|
| `backend/quad_persona/quad_engine.py` | 345 | `backend/llm_gateway/gateway.py`, `core/persona/quad/__init__.py`, `core/simulation/layer2_legacy_knowledge.py`, 3 test files |
| `core/persona/quad/quad_engine.py` | 473 | Same importer list |

**Verdict:** Intentionally separate (confirmed in quad persona Phase 6). backend = gateway-only async path. core = shared library with deterministic fallback. **Already documented.** The only action needed: both files need a clear module docstring stating their distinct roles so future developers don't try to merge them.

---

#### PersonaSufficiencyTool — 2 definitions

| File | Lines | Who imports it |
|---|---|---|
| `backend/truth_engine/truth_core/persona_sufficiency.py` | 174 | `gateway.py`, `truth_core/engine.py`, 3 test files |
| `core/persona/quad/persona_scaling/sufficiency.py` | 382 | Same importer list |

**Verdict:** Both import lists are identical — same 5 files import both? That cannot be right. Live check needed: which import path is actually used in each importer. Most likely `gateway.py` and `engine.py` use the `backend/` path (smaller, tighter integration), and the `core/` path is the richer Phase 5-corrected version. **Action: audit each importer, migrate to `core/persona/quad/persona_scaling/sufficiency.py` (the canonical Phase 5 version), then delete `backend/truth_engine/truth_core/persona_sufficiency.py`.**

---

#### UnifiedCoordinateSystem / AxisCoordinate — 2 definitions

| File | Lines | Role |
|---|---|---|
| `core/coordinate_system.py` | 1105 | Full 17-axis system with Nuremberg numbering, octopus/honeycomb traversal. 13 importers (all axis managers). **Canonical.** |
| `core/simulation/coordinate_system.py` | 618 | Simulation-era coordinate system. Defines same `AxisCoordinate` and `UnifiedCoordinateSystem` class names. |

**Verdict:** `core/coordinate_system.py` is the canonical one imported by all 17 axis manager files. `core/simulation/coordinate_system.py` is legacy simulation code defining the same classes independently. **Action: audit importers of `core/simulation/coordinate_system.py`; migrate to `core/coordinate_system.py`; remove the simulation-era duplicate.**

---

#### AuditLogger — 2 definitions (both in backend/)

| File | Lines | Role |
|---|---|---|
| `backend/security/audit_logger.py` | 734 | Full SOC 2 audit logger with event types, retention, export |
| `backend/truth_engine/truth_memory/audit.py` | 191 | TruthMemory-specific audit event recorder |

**Verdict:** Different domains — security-level vs reasoning-trace-level. Different responsibilities. Not a true conflict. Rename the truth_memory version to `TruthAuditRecorder` or similar to eliminate the class name collision and make the distinction obvious.

---

#### KA050Input / KA-050 Number Collision

| File | Class | What it does |
|---|---|---|
| `backend/knowledge_algorithms/ka_50_knowledge_integrity_validator.py` | `KA050KnowledgeIntegrityValidator` | Validates knowledge graph snapshot structure |
| `backend/knowledge_algorithms/ka_50_summarization.py` | `KA050Summarization` | Summarizes text |

**Verdict:** Two completely different KAs assigned the same number. Both define `class KA050Input(BaseModel)` — this will cause import collisions in any registry that loads both. **Action: renumber one. Summarization is a common KA — assign it the next available number (check `ka_registry.yaml` for the highest used ID, assign KA-115 or the actual next free slot). Update `ka_registry.yaml` and all references.**

---

### 1C. Misplaced Files

#### `backend/core/` — 2 files that belong in `core/`

| File | What it does | Where it belongs |
|---|---|---|
| `backend/core/rag_sanitizer.py` | `RAGSanitizer` — detects prompt injection patterns in RAG content. Pure logic, no Flask. | `core/security/rag_sanitizer.py` |
| `backend/core/resilience_router.py` | `ResilienceRouter` — graceful degradation wrapper for KA execution. Pure logic. | `core/knowledge_algorithm/resilience_router.py` |

Both have zero Flask/DB dependencies. They're pure domain logic sitting in `backend/core/` which is itself a confusing name (a `core/` directory inside `backend/` that is separate from the root `core/` package).

**Action:** Move both files to their correct `core/` locations. Update import sites. Delete `backend/core/` directory.

---

#### The 278-file "misplaced backend" list

The scan flagged 278 backend files with no Flask/DB markers as "candidates for core/". In practice, most of these are **correctly in backend/** — the `backend/truth_engine/`, `backend/knowledge_algorithms/`, `backend/dmrf/`, `backend/dsqp/`, and `backend/security/` directories contain pure-logic modules that are still logically part of the backend application layer, not the core library.

The genuinely misplaced ones are:

| File | Reason it belongs in `core/` |
|---|---|
| `backend/core/rag_sanitizer.py` | Pure security logic, no Flask |
| `backend/core/resilience_router.py` | Pure KA infra, no Flask |
| `backend/location_context_engine.py` | Already a shim wrapping `core/simulation/` — remove the shim once importers are migrated |

Everything else in the 278-file list stays in `backend/` — the scan's "no Flask markers" heuristic is too broad. `backend/knowledge_algorithms/`, `backend/truth_engine/`, `backend/dmrf/`, `backend/dsqp/` are all correct as backend application modules.

---

## Part 2 — Layering Inversions (26 lines / 13 files)

Previously identified, confirmed by live scan. Full file:line inventory:

| File | Lines | Import target | Fix |
|---|---|---|---|
| `core/coordinate_system.py` | L823 | `backend.storage.get_graph_store` | Lazy import inside method |
| `core/engine/ka_engine.py` | L253, L276 | `backend.knowledge_algorithm.registry`, `.context` | Extract KARegistry + create_default_context to `core.knowledge_algorithm` |
| `core/mcp/mcp_server.py` | L14, L15, L20, L442 | `backend.mcp_server.connector_metrics`, `.contract_validation`, `.scope_enforcement`, `.subscriptions` | Discuss with Kevin: move MCP infra to `core.mcp` or inject via interface |
| `core/mcp/mcp_client.py` | L506 | `backend.mcp_server.sampling.sampling_service` | Constructor injection |
| `core/simulation/agentic/simulation_graph.py` | L5 | `backend.storage.graph_store.get_graph_store` | Lazy import inside method |
| `core/simulation/layer2_knowledge.py` | L259 | `backend.storage.get_uskd_memory_graph` | Lazy import inside method |
| `core/simulation/layer3_agent_engine.py` | L14, L15 | `backend.knowledge_algorithms.ka_claim_extraction`, `.ka_29_online_validation` | Move KA base classes to `core.knowledge_algorithm` |
| `core/simulation/layer5_pipeline.py` | L171 | `backend.knowledge_algorithms.ka_12_persona_simulation` | Same strategy as layer3 |
| `core/simulation/layer_controller.py` | L68 | `backend.knowledge_algorithms.ka_master_controller` | Lazy import inside dispatch |
| `core/simulation/refinement_workflow.py` | L11–13 | `backend.knowledge_algorithm.registry`, `.base`, `.context` | Extract to `core.knowledge_algorithm` |
| `core/simulation/simulation_engine.py` | L45–47 | `backend.knowledge_algorithm.axis_mapper`, `.truth_engine`, `.workflow_loader` | Protocol/ABC interfaces in `core` |
| `core/system/frost_service.py` | L100, L230, L239 | `backend.storage.get_object_store`, `backend.memory.get_unified_memory_service` | Lazy imports |
| `core/system/persona_construction_service.py` | L129, L153, L185 | `backend.services.rag_service`, `backend.dsqp` | Constructor injection |

---

## Part 3 — Security Posture

### compliance_manager.py

All five `_check_*_compliance()` methods unconditionally set `status = "compliant"` with the comment "In a real implementation, this would check…". The compliance dashboard permanently shows green regardless of system state.

**Required real checks:**

| Method | Check to implement |
|---|---|
| `_check_security_compliance()` | Fernet key loaded + rotation not overdue + audit log dir writable |
| `_check_availability_compliance()` | DB connection succeeds + no recent unhandled exception spike |
| `_check_processing_integrity_compliance()` | Last `TruthAuditEvent` hash chain valid + migration at head |
| `_check_confidentiality_compliance()` | Encryption key is not a dev/default value + no PII in plain audit log |
| `_check_privacy_compliance()` | User export + deletion endpoints reachable + AI processing toggle wired |

### EncryptionManager

`backend/security/encryption_manager.py` uses `cryptography.fernet.Fernet` (AES-128-CBC + HMAC-SHA256). Multiple docs claim AES-256-GCM. **Kevin decides:** upgrade the implementation or correct the documentation. Both paths are specified in the task table below.

---

## Sprint Plan

Three sprints in priority order. Each has a hard exit gate before the next begins.

---

### Sprint 1 — Structural Cleanup (5–7 days)

Fix the duplicate/collision issues that cause real risk: wrong imports, registry breaks, misleading class names.

| ID | Task | Files | Exit Gate |
|---|---|---|---|
| DUP-1 | Renumber KA-050 collision | Rename `ka_50_summarization.py` → `ka_NNN_summarization.py` where NNN = next free slot in `ka_registry.yaml`. Update registry + all references. | `python -m pytest tests/knowledge_algorithms/ -q --no-cov` passes; `ka_registry.yaml` has no duplicate IDs |
| DUP-2 | Remove `core/system/refinement_orchestrator.py` (105-line scaffold) | Delete file. Verify no live importers. | Full pytest passes; ruff clean |
| DUP-3 | Rename `backend/simulation/simulation_engine.py` → `multi_agent_engine.py` | Rename file + class `SimulationEngine` → `MultiAgentSimulationEngine`. Update all import sites. | `python -m pytest tests/simulation/ -q --no-cov` passes; no file named `simulation_engine.py` in `backend/simulation/` |
| DUP-4 | Resolve `core/simulation/coordinate_system.py` vs `core/coordinate_system.py` | Audit importers of the simulation-era version; migrate to canonical; remove duplicate. | `python -m pytest tests/axes/ tests/unit/test_phase_b_axis_alignment.py -q --no-cov` passes |
| DUP-5 | Migrate `PersonaSufficiencyTool` to canonical `core/persona/quad/persona_scaling/sufficiency.py` | Audit each importer of `backend/truth_engine/truth_core/persona_sufficiency.py`; repoint to core version; delete backend copy. | `python -m pytest tests/unit/test_phase5_phase_c.py tests/persona/quad/ -q --no-cov` passes |
| DUP-6 | Move `backend/core/` files to correct locations | Move `rag_sanitizer.py` → `core/security/`, `resilience_router.py` → `core/knowledge_algorithm/`. Update imports. Delete `backend/core/` dir. | No `backend/core/` directory exists; pytest passes; ruff clean |
| DUP-7 | Add disambiguating docstrings to intentional same-name pairs | `backend/quad_persona/quad_engine.py`, `core/persona/quad/quad_engine.py`, `backend/dmrf/models.py`, `core/persona/quad/models.py`, `backend/dmrf/orchestrator.py`, `core/simulation/orchestrator.py` | Each file has a module docstring stating its role and why it is distinct from its namesake |
| DUP-8 | Rename `AuditLogger` in `backend/truth_engine/truth_memory/audit.py` | Rename class to `TruthAuditRecorder` throughout file + all importers | `python -m pytest tests/truth_engine/ -q --no-cov` passes; no duplicate `AuditLogger` class names |

**Sprint 1 Exit Gate:** `python -m pytest tests/ --no-cov` green (baseline 1821 passed) + `ruff check .` clean + `python scripts/audit_duplicates.py` shows 0 critical collisions + `REPO_AUDIT_LOG.md` updated.

---

### Sprint 2 — Layering Inversions (4–6 days)

Fix the 26 `core → backend` import lines in dependency order: easiest (lazy import) first, hardest (interface extraction) last.

| ID | Task | Files | Fix Type | Exit Gate |
|---|---|---|---|---|
| LY-1 | Lazy import fixes — storage/memory | `core/coordinate_system.py` L823, `core/simulation/agentic/simulation_graph.py` L5, `core/simulation/layer2_knowledge.py` L259, `core/system/frost_service.py` L100/L230/L239 | Move import inside the calling method body | Focused tests for affected modules pass; ruff clean |
| LY-2 | Lazy import fix — layer_controller KA dispatch | `core/simulation/layer_controller.py` L68 | Move `ka_master_controller` import inside dispatch method | pytest tests/simulation/ passes |
| LY-3 | Extract KARegistry + KAContext to `core/` | `core/engine/ka_engine.py` L253/L276, `core/simulation/refinement_workflow.py` L11–13, `core/simulation/simulation_engine.py` L45–47 | Create `core/knowledge_algorithm/registry_protocol.py` with ABC/Protocol; backend registry implements it | pytest tests/knowledge_algorithms/ passes; ruff clean |
| LY-4 | Constructor injection — `PersonaConstructionService` | `core/system/persona_construction_service.py` L129/L153/L185 | Inject `RAGService` and `DSQPChain` via constructor params; callers pass concrete instances | pytest tests/unit/test_phase_d_dsqp.py tests/unit/test_phase5_phase_c.py pass |
| LY-5 | Constructor injection / interface — `mcp_client.py` | `core/mcp/mcp_client.py` L506 | Inject sampling adapter at construction | pytest tests/unit/ -k mcp passes |
| LY-6 | MCP server inversions — discuss strategy with Kevin | `core/mcp/mcp_server.py` L14/L15/L20/L442 | Option A: move MCP infra shared code to `core.mcp`; Option B: inject via interface. Kevin decides. | Kevin decision recorded in REPO_AUDIT_LOG.md; chosen option implemented; tests pass |
| LY-7 | KA base class inversions — layer3/5 | `core/simulation/layer3_agent_engine.py` L14/L15, `core/simulation/layer5_pipeline.py` L171 | Confirm whether `ka_claim_extraction` and `ka_12/29` should move to `core/knowledge_algorithm/` or stay in backend with lazy imports | Tests pass; 0 inversions remaining |

**Sprint 2 Exit Gate:** `python scripts/find_core_backend_inversions.py` reports 0 lines (or only explicitly documented exceptions) + full pytest green + ruff clean.

---

### Sprint 3 — Security Posture (2–3 days)

| ID | Task | File | What to implement | Exit Gate |
|---|---|---|---|---|
| SC-1 | Real security compliance check | `backend/security/compliance_manager.py` | Key loaded + not overdue + audit dir writable | Unit test: non-compliant on expired key; compliant on valid |
| SC-2 | Real availability check | same | DB connection + no exception spike | Unit test: non-compliant on DB failure |
| SC-3 | Real processing integrity check | same | Last hash chain valid + migration at head | Unit test: non-compliant on chain break |
| SC-4 | Real confidentiality check | same | Key not dev value + no PII in plain audit log | Unit test: non-compliant on dev key |
| SC-5 | Real privacy check | same | Export + deletion endpoints reachable; AI toggle wired | Unit test: compliant on seeded DB |
| SC-6 | Encryption decision + fix | `backend/security/encryption_manager.py` + `docs/SECURITY.md` + `docs/ARCHITECTURE.md` | **Kevin decides:** upgrade Fernet → AES-256-GCM, or correct docs to say AES-128-CBC. Both paths fully implemented. | Code and all docs describe same algorithm consistently |

**Sprint 3 Exit Gate:** All 5 compliance checks have real logic + no stub returns + docs and code agree on encryption algorithm + pytest green.

---

## Execution Rules

- **Read before writing.** For every duplicate resolution, read both files fully before deciding which is canonical. The importer count and line count are signals, not verdicts.
- **One task = one commit.** Each ID above is a single conventional commit (`fix(sim): rename MultiAgentSimulationEngine`, etc.).
- **No behavior changes in Sprints 1 and 2.** If a proposed fix requires changing business logic, stop and flag it.
- **KA-050 renumber: check the registry first.** Run `grep "ka_50\|KA-050\|KA_050" ka_registry.yaml` and all route/registry files before picking the new number — do not guess.
- **Kevin's decisions required before proceeding:** LY-6 (MCP server strategy) and SC-6 (encryption upgrade vs doc correction) must not be coded without a direction.
- **Test gate is non-negotiable.** Baseline: 1821 passed, 21 skipped. Any regression stops the sprint.

---

## What Is NOT Covered Here (Deliberately Deferred)

- KA production depth sweep (Sprint 3 from v1.0) — not a structural issue, deferred until Sprint 1+2 complete
- `core/simulation/truth_engine.py` orphan decision — needs one more importer check before verdict
- Folder-by-folder deep reviews (DMRF spec fidelity, DSQP disclosure alignment, L5–L10 KA depth) — these are separate sessions
- Production release gates (NVDA, code signing, CI evidence) — unaffected by this work

---

## Appendix — Raw Scan Output

### Module name collisions (8)
```
exceptions.py          backend/utils/   vs  core/knowledge_algorithm/
integrity.py           backend/security/ vs  core/security/
location_context_engine.py  backend/    vs  core/simulation/
models.py              backend/dmrf/    vs  core/persona/quad/
orchestrator.py        backend/dmrf/    vs  core/simulation/
quad_engine.py         backend/quad_persona/ vs core/persona/quad/
refinement_orchestrator.py  backend/truth_engine/truth_core/ vs core/simulation/ AND core/system/
simulation_engine.py   backend/simulation/ vs core/simulation/
```

### Duplicate class names (17)
```
AuditLogger             backend/security/audit_logger.py
                        backend/truth_engine/truth_memory/audit.py

AxisCoordinate          core/coordinate_system.py
                        core/simulation/coordinate_system.py

ConfidenceVector        core/simulation/truth_engine.py
                        core/system/uae_models.py

EvidenceItem            core/persona/quad/quad_models.py
                        core/simulation/layer5_schemas.py

ExpandedPersona         backend/dsqp/dsqp_chain.py
                        core/persona/quad/pod_models.py

GatekeeperAgent         core/simulation/gatekeeper_agent.py
                        core/simulation/layer3_agents.py

KA050Input              backend/knowledge_algorithms/ka_50_knowledge_integrity_validator.py
                        backend/knowledge_algorithms/ka_50_summarization.py

Layer5IntegrationEngine core/simulation/layer5_integration.py
                        core/simulation/layer5_legacy_integration.py

LocationContextEngine   backend/location_context_engine.py
                        core/simulation/location_context_engine.py

PersonaSufficiencyTool  backend/truth_engine/truth_core/persona_sufficiency.py
                        core/persona/quad/persona_scaling/sufficiency.py

ProblemSpec             core/persona/quad/quad_models.py
                        core/simulation/layer5_schemas.py

QuadPersonaEngine       backend/quad_persona/quad_engine.py
                        core/persona/quad/quad_engine.py

RefinementOrchestrator  backend/truth_engine/truth_core/refinement_orchestrator.py
                        core/simulation/refinement_orchestrator.py
                        core/system/refinement_orchestrator.py

Severity                core/simulation/layer5_schemas.py
                        core/simulation/pov_delta.py

SimulationEngine        backend/simulation/simulation_engine.py
                        core/simulation/legacy_simulation_engine.py
                        core/simulation/simulation_engine.py

UnifiedCoordinateSystem core/coordinate_system.py
                        core/simulation/coordinate_system.py

ValidationError         backend/utils/exceptions.py
                        backend/utils/validation.py
```

### Cross-tree factory function duplicates (2)
```
create_quad_persona_engine()   backend/quad_persona/quad_engine.py
                               core/persona/quad/quad_engine.py

create_simulation_engine()     backend/simulation/simulation_engine.py
                               core/simulation/legacy_simulation_engine.py
```

### backend/core/ misplaced files (2)
```
backend/core/rag_sanitizer.py        → core/security/rag_sanitizer.py
backend/core/resilience_router.py    → core/knowledge_algorithm/resilience_router.py
```

---

*DataLogicEngine Audit & Sprint Plan v2.0 — June 7, 2026 — built from live code scans on main branch*
