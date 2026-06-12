# DataLogicEngine — Complete Audit Plan v2.0
**Built from:** live MCP scan + full conversation history review | 1,049 commits | June 10, 2026
**Goal:** Every folder audited, every file in the right place, every feature correctly wired, dead code removed, app complete and to best practices.

---

## Audit Status Summary

### Execution progress (updated 2026-06-11)

| Session | Scope | Status | Commit | Key result |
|---|---|---|---|---|
| AUDIT-SPRINT-1/2/3 | dup classes, import inversions, compliance stubs | ✅ done | (pre-plan) | — |
| ROUTES RT-1..RT-18 | all 22 route files | ✅ done | `df29906b` `0eb2b0bb` `cc01c15b` | completed 2026-06-07/08 (plan listed them stale) |
| **Sprint 0** | N3 legacy axes, N4 Axis 4/5 | ✅ done | `821737d1` | + fixed honeycomb_api Axis-5→Axis-3 500 bug, added auth |
| **A4** | `local_model_acceleration/` | ✅ done | `821737d1` | A4-1 coroutine lifecycle, A4-2 keepalive reload, A4-3 spec |
| **A3** | `llm_gateway/` + N2 | ✅ done | `1ddeec49` | N2 defense supervisor wired; 4 status endpoints secured; A4-4/5/8 |
| **A1a** | `truth_core/` + `truth_gate/` | ✅ done | `86486a78` | A1a-1 fixed hardcoded audit latency |
| **A1b** | `truth_memory/` + `truth_link/` + top-level | ✅ done | `5027fc3b` | resolved A3-3/A1a-3, A4-7 |
| **A2** | `dsqp/` | ✅ done | `4390c608` | matches disclosure (deterministic slice); validator process-aware (A2-1) |
| **A2-2** | DSQP LLM-assisted construction | ✅ done | `a1784a17` | query-derived personas; offline fallback kept |
| **A5** | `dmrf/` | ✅ done | `5d8dc848` | all 17 axes; no MLflow conflict; frost_bridge real; A5-1 wired DMRFDesktopConfig |
| **A6a** | `core/simulation/` L1–L5 map | ✅ done | `2afe2d14` | L5 override fixed; 12 dead legacy files removed |
| **A6b** | `core/simulation/` L6–L10 + SEKRE | ✅ done | `pending` | L6–L10 map; **N1 SEKRE wired**; no deletions (already clean) |
| **— PHASE 1 COMPLETE —** | live query path (8/8) | ✅ | — | N1+N2 wired; −5,150 LOC dead code removed |
| **A7+A8** | `knowledge_algorithms/` (125 KAs) | ✅ done | `pending` | 125/125 registry resolve; 0 orphan configs; 117 real + 8 compact-real + 0 stub; KA-113 multi-signal (A7-1); KA-005 tiering + A5-3 (A8) |
| **A9** | `core/persona/quad/` | ⏭ NEXT | — | quad persona system |
| A10–A32 | rest of Phases 2–4 | ☐ | — | see session sequence below |

Per-session findings and verdicts are recorded in `REPO_AUDIT_LOG.md`.
Live test baseline: **2056 passed / 21 skipped** + KA-113/KA-005 tests.
**Phase 1 COMPLETE (8/8); Phase 2 in progress.** The `knowledge_algorithms`
audit (A7+A8) is complete: registry 125/125 resolves, configs complete, all KAs
rated (117 real + 8 compact-real + 0 stub). Next is **A9** (`core/persona/quad/`).
Both June-10-scan disconnected components are wired: N2 (defense_supervisor, A3)
and N1 (SEKRE, A6b).

### Open carry-over findings (tracked across sessions)

| ID | Finding | Resolve in | Status |
|---|---|---|---|
| A3-3 / A1a-3 | Tier 2+ audit-commit gate excluded `"moderate"` (= Tier 2 per `dmrf` `TIER_ORDER`), skipping Tier 2 audit bundles | A1b | ✅ resolved `5027fc3b` |
| A4-7 | exact-cache hit serves a Tier 2+ answer with no new `TruthAuditEvent` | A1b | ✅ resolved `5027fc3b` |
| A2-2 | DSQP deterministic `_answer_question` produces axis-keyed role scaffolds, not full query-derived construction; implement LLM-assisted answers before external IP filing | A2-2 build | ✅ resolved 2026-06-11 (`dsqp_answer_generator.py`; offline fallback kept) |
| A3-4 | defense supervisor `user_role` always "user"; HONEYPOT treated as BLOCK | A10 | ☐ |
| A5-2 | five overlapping pattern-injection defenses (shield/guardrail/supervisor/truthgate/dmrf) — confirm union, consider consolidation | A10 | ☐ |
| A5-3 | `DMRFTierClassifier.ka_controller` unused; also KA-005 never emitted a tier (TruthCore tiering branch dead) | A8 | ✅ resolved 2026-06-11 (KA-005 emits `suggested_tier`; DMRF param dropped) |
| A3-5 | governance `record_audit_event` / daily-usage no-op without db session | A26 | ☐ |
| A1a-2 | `truth_core/router.py` `LLMRouter` parallel dead code, stale model names | A6b / cleanup | ☐ |
| A1a-4 | `_execute_refinement_step` "Mock result" fallback when no KA controller | A6 | ☐ |
| A18-pre | `tests/integration/test_api_endpoints.py` + `tests/knowledge_algorithms/` share a `drop_all_test_tables` conftest name → collection error when collected together | A18 | ☐ |
| SC-2 | Encryption: Fernet→AES-256-GCM decision (note: AES-256-GCM landed in Sprint 2 `EncryptionManager`; confirm docs) | A10 / A31 | ☐ |

---

## Newly Investigated Items — Live Code Read Verdicts

### N1 · `core/self_evolving/sekre_engine.py` — ✅ RESOLVED (A6b, 2026-06-11): wired post-L10 in SimulationEngine

**What it is:** SEKRE = Self-Evolving Knowledge Refinement Engine. 620 lines, fully implemented. Analyzes simulation results, processes user feedback, generates improvement suggestions, applies them to the knowledge base. This is the Layer 10 meta-cognitive self-improvement component described in the UKG architecture.

**Current state:** Zero importers anywhere in the codebase. `SekreEngine` is never instantiated or called. Constructor expects `graph_manager`, `memory_manager`, `united_system_manager`, `simulation_validator` — all exist in `core/system/` — but nothing passes them in.

**Correct location:** `core/self_evolving/sekre_engine.py` — correct. No move needed.

**Wiring tasks:**
- Instantiate `SekreEngine` in `core/system/system_initializer.py` with constructor injection
- Call `SekreEngine.analyze_simulation_results()` from `core/simulation/simulation_engine.py` post-L10 on Tier 3+ runs
- Call `SekreEngine.process_feedback()` from the feedback API endpoint (create endpoint if none exists)
- Add `sekre_status` to `/health` and Electron IPC `get-db-status`
- Add SEKRE to `backend.spec` PyInstaller collection
- Write tests: analysis, feedback processing, auto-improve toggle, memory storage

---

### N2 · `prompts/defense_supervisor.txt` — VERDICT: Disconnected, wire into security pipeline

**What it is:** A 30-line LLM system prompt for a "Security Supervisor" that evaluates user inputs for prompt injection, Crescendo (gradual poisoning), social engineering, and DAN-style override attempts. Outputs structured JSON: `is_safe`, `threat_score`, `threat_type`, `reason`, `recommended_action` (ALLOW/BLOCK/HONEYPOT).

**Current state:** Zero importers. Never loaded by any Python file.

**Wiring tasks:**
- During A3 (gateway audit) and A10 (security audit): determine whether `backend/security/prompt_injection_shield.py` or `backend/security/ai_guardrail.py` should own this prompt — whichever handles LLM-backed screening
- Wire: load prompt from file in the owning module; call as LLM screening step for every Tier 2+ query
- Move to `backend/security/prompts/defense_supervisor.txt` (next to the code that uses it), or keep at root and document the path
- Add to `backend.spec` PyInstaller datas so it is bundled in the installer
- Test: prompt loads, screening call returns valid JSON structure

---

### N3 · Duplicate axis files (axes 14–17) — VERDICT: 4 legacy files safe to delete

**Confirmed:** `axis_system.py` loads the canonical set (`axis14_acquisition_lifecycle.py`, `axis15_risk_threat.py`, `axis16_ethics_trust.py`, `axis17_frost_mode.py`). The 4 legacy files are never imported anywhere.

| Delete | Keep |
|---|---|
| `axis14_provenance.py` | `axis14_acquisition_lifecycle.py` |
| `axis15_object_type.py` | `axis15_risk_threat.py` |
| `axis16_validation_state.py` | `axis16_ethics_trust.py` |
| `axis17_security.py` | `axis17_frost_mode.py` |

**Tasks:** Confirm no test imports legacy files → delete all 4 → run `pytest tests/axes/` → green → commit.

---

### N4 · Missing Axis 4/5 files — VERDICT: Gap needs resolution

**Confirmed:** `axis_system.py` uses `axis3_domain.py` (`DomainManager`) as `BranchManager` for Axis 4 with a comment noting the reuse. Axis 5 (Node System) has no dedicated manager and no registration.

**Tasks:**
- Determine if `DomainManager` adequately covers Branch System semantics for Axis 4, or create `axis4_branch.py`
- Determine if Axis 5 needs a dedicated manager or if deliberate absence is acceptable — document the decision
- Register Axis 5 manager or add a comment in `axis_system.py` explaining why it is absent
- Remove the confusing "was DomainManager Axis 3 file" comment

---

## Complete Remaining Audit Scope

### PHASE 1 — Live Query Path (7 sessions)

#### A4 · `backend/local_model_acceleration/` — START HERE
**1 session | 8 files | Sprint 6, never reviewed | Tier 0 = every query**

| File | Audit questions | Expected outcome |
|---|---|---|
| `manager.py` | Initialized at startup? Wired into gateway tier cascade? Error handling if Ollama not running? | Live, graceful degradation confirmed |
| `keepalive.py` | Keeps model in memory between requests? Restarts Ollama on crash? | Keepalive active, failure handled |
| `ollama_client.py` | Streaming correct? Handles model-not-found, OOM, timeout? Sync vs async (cf. gpt-5.5 May 31 fix)? | No event-loop issues |
| `response_cache.py` | Exact match? Cache invalidation on knowledge-base update confirmed (commit `52195e69`)? | Invalidation wired and tested |
| `safety.py` | What safety checks on local model responses? Same/different from `prompt_injection_shield.py`? Relates to N2. | Relationship to N2 clarified |
| `config.py` | Bad config values fail fast or silently degrade? | No silent failures |
| `paths.py` | Ollama binary path correct in both dev and installed app? | Works on clean Windows install |

**Exit gate:** Tier 0 query traced end-to-end. Cache invalidation confirmed on graph update. All failure modes handled. Relationship to N2 (`defense_supervisor.txt`) documented.

---

#### A3 · `backend/llm_gateway/` — Gateway
**1 session | 9 files**

| File | Audit questions |
|---|---|
| `gateway.py` | DMRF flag wired? UKG pipeline actually called or sometimes short-circuits? SekreEngine (N1) called post-response? |
| `complexity_classifier.py` | Same as KA-113 or separate? If separate, do they agree? |
| `escalation_config.py` | All 6 tiers (T0 Ollama → T5 Azure) correctly configured and tested? |
| `model_defaults.py` | All model names current? gpt-5.5 confirmed, others tested? |
| `governance.py` | Enforced per-request or logging only? |
| `tier_availability.py` | Correctly reflects configured API keys? Updates when key saved in Settings? |
| `api.py` | Auth coverage, error handling, rate limiting on all route handlers? |
| N2 wiring | `defense_supervisor.txt` integration assessed here — does the gateway call the security supervisor? |

---

#### A1 · `backend/truth_engine/` — Live Reasoning Pipeline
**2 sessions | 37 files**

**Session A1a — truth_core + truth_gate**

| File | Audit questions |
|---|---|
| `truth_core/engine.py` | Real entry point? All 10 layers called for Tier 3+? |
| `truth_core/router.py` | Tier routing matches spec: T1=L1/L2/L10, T2=L1/L2/L5/L8/L10, T3-5=all? |
| `truth_core/meta_reasoning_controller.py` | Max-5-iteration limit enforced? FINALIZE/REFINE gate working? |
| `truth_core/emergence_controller.py` | L10 emergence gate actually fires or always passes? |
| `truth_core/persona_scaling_bridge.py` | Wired to `core/persona/quad/quad_engine.py`? Or stubbed? |
| `truth_core/agi_planner.py` | L7 AGI planning real or placeholder? |
| `truth_gate/gateway.py` | Blocks bad queries or just logs? Kill-switch if budget exceeded? |
| `truth_gate/opa_policy.py` | OPA evaluated live (subprocess) or Python fallback always used? |
| `truth_gate/quant_backends/` | Real quantization backends or stubs? |
| `truth_gate/trust_validation_gateway.py` | 11 KAs actually invoked? Which ones? |

**Session A1b — truth_memory + truth_link + top-level**

| File | Audit questions |
|---|---|
| `truth_memory/audit.py` | Hash-chain correct? `TruthAuditRecorder` rename (DUP-8) confirmed? |
| `truth_memory/commit_service.py` | Writes `TruthAuditEvent` on every Tier 2+ run? |
| `truth_memory/mlflow_tracker.py` | Live MLflow or silently no-ops? Conflicts with `dmrf/mlflow_tracker.py`? |
| `truth_memory/retention_router.py` | Routes to 7-year local archive? Policy respected? |
| `truth_link/blockchain_adapter.py` | Local simulated anchors confirmed (DB-O)? Still accurate? |
| `truth_link/bus.py` | Redis Streams wired (Phase G-B)? |
| `confidence_calculator.py` | F-CONF-01 formula correct? Matches canonical spec? |
| `federated_sync.py` | Wired to real federated endpoint or dead code? |

**Exit gate:** End-to-end Tier 3 query traced: `engine.py` entry → all 10 layers → `TruthMemory.commit_service` → valid `TruthAuditEvent` hash chain → SekreEngine (after N1 wired).

---

#### A2 · `backend/dsqp/` — Patent Claim
**1 session | 5 files + templates**

| File | Audit question | Expected outcome |
|---|---|---|
| `dsqp_chain.py` | Personas constructed dynamically via 7-part self-questioning at query time, or selected from templates? | Dynamic construction confirmed |
| `dsqp_orchestrator.py` | Calls chain at query time or caches across queries? | Per-query construction |
| `dsqp_validator.py` | Validates DSQP process followed, not just output format? | Real process validation |
| `dsqp_registry.py` | Stores construction specs (correct) or pre-built definitions (wrong)? | Specs, not definitions |
| `templates/` | Fallback path only (acceptable)? | Fallback only |

**Exit gate:** Written statement confirming or challenging that implementation matches technical disclosure. Gaps documented for remediation before any IP conversation.

---

#### A5 · `backend/dmrf/` — 17-Axis Router
**1 session | 19 files**

| File | Audit questions |
|---|---|
| `router.py` | All 17 axes exercised? Convergence policy applied per tier? |
| `convergence_policy.py` | Tier-to-FROST-depth mapping matches DMRF v3.3.0 spec? |
| `tier_classifier.py` | Duplicates or delegates to `llm_gateway/complexity_classifier.py`? |
| `frost_bridge.py` | Actually passes FROST depth to simulation layer stack? Or stub? |
| `truth_integration/` (5 adapters) | All 4 TruthEngine subsystems correctly receive DMRF outputs? |
| `mlflow_tracker.py` | Two MLflow trackers (dmrf + truth_memory) — conflict? Same experiment? |
| `injection_defense.py` | Applied at DMRF inputs AND TruthGate? |
| `desktop_config.py` | Conflicts with `llm_gateway/escalation_config.py`? |

---

#### A6 · `core/simulation/` — 10-Layer Stack
**2 sessions | 49 files**

**Session A6a — Entry layers + legacy/runtime split (L1–L5)**

Goal: definitive layer map — for each layer, which file is live, which are legacy/dead.

| Layer | Files | Question |
|---|---|---|
| L1 | `layer1_entry.py`, `layer1_planning.py`, `layer1_database.py`, `layer1_legacy_entry.py` | Which 1 does `simulation_engine.py` actually call? |
| L2 | `layer2_knowledge.py`, `layer2_retrieval.py`, `layer2_legacy_knowledge.py` | Same question |
| L3 | `layer3_agents.py`, `layer3_agent_engine.py`, `layer3_expert.py` | Agentic enrichment live or scaffolded? |
| L4/POV | `layer4_reasoning.py`, `pov_engine.py`, `pov_engine_enterprise.py`, `pov_delta.py`, `pov_policy.py` | Which is called at L4? |
| L5 | `layer5_integration.py`, `layer5_legacy_integration.py`, `layer5_pipeline.py`, `layer5_schemas.py` | DUP-3: `Layer5IntegrationEngine` duplicate — which is canonical post-sprint? |

**Session A6b — Upper layers + orchestration + cleanup (L6–L10)**

| Area | Questions |
|---|---|
| L6: `layer6_enhancement.py`, `layer6_neural_analysis.py` | Two L6 files — different concerns or duplicate? |
| L7: `layer7_agi_system.py` | Calls `truth_core/agi_planner.py` or independent? |
| L8: `layer8_quantum.py`, `layer8_quantum_computer.py` | Real quantization or aspirational? Which is live? |
| L9: `layer9_recursive.py`, `layer9_recursive_agi.py` | Max-5 iterations enforced? Recursion governor working? |
| L10: `layer10_self_awareness.py`, `layer10_synthesis.py` | Lane A + Lane B both active? Lane B to StructuredMemoryGraph confirmed? |
| `truth_engine.py` | Confirmed orphan — **remove** |
| Orchestration: 4 files | Map execution graph — clean or spaghetti? |
| `agentic/` subdir | What's in it? Wired to L3? |
| N1 wiring | After wiring: `SekreEngine.analyze_simulation_results()` called post-L10 |

**Exit gate:** Authoritative layer map produced. Dead files removed. SEKRE wired. Every layer has single identified live implementation.

---

### PHASE 2 — Reasoning Depth (8 sessions)

#### A7 + A8 · `backend/knowledge_algorithms/` — All 117 KAs + Configs
**4 sessions | 125 Python files + 99 config JSONs**

Per-KA rating: real / heuristic / stub. Confidence scoring variable? 17-axis coordinate used? Config JSON wired?

High-risk KAs requiring real implementations confirmed (not heuristic acceptable):

| KA | Risk | Why |
|---|---|---|
| KA-061 Adversarial Input Shield | 🔴 HIGH | First-line injection defense |
| KA-107 Reasoning Boundary Enforcer | 🔴 HIGH | Prevents unsafe tool use |
| KA-113 Tier/Complexity Router | 🔴 HIGH | Central orchestration decision |
| KA-102 Entropy Scorer | 🟡 MED | L10 emergence signal — F-ENT-02 formula |
| KA-032 Simulation Orchestration Controller | 🟡 MED | Layer stack coordination |
| KA-014 Confidence Scoring | 🟡 MED | F-CONF-01 formula |
| KA-117 Knowledge Integrity Validator | 🟡 MED | Renamed from ka_50 — propagation confirmed? |

Config layer: verify all 99 config JSONs wired to implementations. `ka_33_config.json` absent (reserved slot — expected). No others missing.

**Exit gate:** Every KA rated. All HIGH-RISK confirmed real with tests. No missing config files. KA-117 rename fully propagated.

---

#### A9 · `core/persona/quad/` — Quad Persona System
**1 session | ~20 files**

| Area | Questions |
|---|---|
| `quad_engine.py` (473 lines) | 7-part dynamic role construction at query time confirmed — not template selection |
| Three model files | Different domains or duplicate definitions? |
| `persona_scaling/sufficiency.py` | Canonical after DUP-5 — all importers pointing here? |
| `pod_orchestrator/` | Role vs main quad_engine? Overlap? |
| `mathematical_framework/` | Math formulas from white paper actually implemented? |
| `axis_role_mapper.py` | Axes 8–11 mapped to persona roles at query time? |

---

#### A10 · `backend/security/` — Full Security Audit
**1 session | 28 files**

| File | Risk | Questions |
|---|---|---|
| `prompt_injection_shield.py` | 🔴 HIGH | Same as `defense_supervisor.txt` (N2) or different? Together do they cover Crescendo, DAN, Base64 obfuscation? |
| `ai_guardrail.py` | 🔴 HIGH | Same layer as prompt_injection_shield? Which called first on every query? |
| `zero_trust.py` | 🔴 HIGH | Enforced per-request or declared-only? |
| `active_defense.py` | 🔴 HIGH | Rate limit? Block IPs? Honeypot redirect? Actually triggering? |
| `password_security.py` | 🔴 HIGH | **bcrypt ≥12 rounds or argon2id — confirm. Open since May 2026.** |
| `rbac.py` | 🔴 HIGH | No privilege escalation paths in recent code? |
| `session_manager.py`, `token_manager.py` | 🔴 HIGH | Session rotation? JWT expiry? Concurrent session limit? |
| `pii_redaction.py` | 🔴 HIGH | Applied to TruthMemory audit chain? No PII in `TruthAuditEvent` rows? |
| `dpapi_store.py` | 🟡 MED | Fails gracefully on Linux/Docker? |
| `vulnerability_scanner.py` | 🟡 MED | Actually scanning or stub? |
| `honeypot.py` | 🟡 MED | Wired to alerting or just logs? |
| `secret_resolver.py` | 🟡 MED | Used consistently? Or some components bypass it? |

**Exit gate:** Every HIGH-RISK file confirmed real. Password hashing ≥12 rounds confirmed. N2 wired. No conflicting security layers.

---

#### A11 · `core/axes/` — 17-Axis System Cleanup
**1 session | 24 files → ~20 after cleanup**

- Delete 4 legacy files (N3 verdict)
- Resolve Axis 4/5 gap (N4 verdict)
- Confirm `axis_system.py` registers all 17 axes correctly
- Confirm `core/coordinate_system.py` is canonical and `core/simulation/coordinate_system.py` deleted (DUP-4)

---

#### A12 · `backend/storage/` — Storage Layer
**1 session | 8 files**

| File | Questions | Linked open item |
|---|---|---|
| `graph_store.py` | Neo4j traversal live — re-confirm (DB-N) | DB-N done per TODO |
| `vector_store.py` | ChromaDB collections actually have data — verify (DB-C) | DB-C done per TODO |
| `uskd_memory_graph.py` | StructuredMemoryGraph wired to pipeline — verify (DB-M) | DB-M done per TODO |
| `connection_manager.py` | Rate limiting NOT using `memory://` in multi-worker mode | Open security item |
| `runtime_settings.py` | Flat-file race condition fixed? | RT-10 defines fix |

---

#### A13 · `core/system/` — System Services
**1 session | 10 files**

- `frost_service.py`: checkpointing, rewind, LY-1 fix confirmed
- `persona_construction_service.py`: LY-1 injection confirmed, RAGService + DSQPChain live
- `trace_service.py`: `trace_stage_update` Socket.IO emission confirmed (TV-6)
- `refinement_orchestrator.py`: **DUP-2 — confirm deleted**
- N1 wiring: `SekreEngine` instantiated here with `united_system_manager` + `graph_manager` + `memory_manager` + `simulation_validator` injected

---

#### A14 · `sdk/UKG_Python_SDK/` — Python SDK
**1 session | ~25 files**

- API surface matches current backend including Sprint 6?
- `providers/local_slm.py` wired to `local_model_acceleration/` (A4)?
- `coordinates17.py` current with canonical axes 14–17?
- `tenlayer.py` "simplified" note still accurate?
- SDK version current?

---

### PHASE 3 — Frontend (4 sessions)

#### A15 · `frontend/app/` — All 18 Pages
**2 sessions**

Every page: auth guard, correct API endpoints, error states, loading states. Special attention: `truth-engine/` page full end-to-end trace render confirmation (browser smoke with auth + backend running). `settings/` page only works after RT-3 (register `settings_bp`) is executed.

#### A16 · `frontend/components/` — All Components
**1 session | ~40 files**

TV trace viewer renders real data (post TV wiring). `MessageBubble.tsx` has thumbs-down → feedback endpoint → SekreEngine hook (post N1). Dashboard shows real metrics.

#### A17 · `frontend/lib/`, `hooks/`, `contexts/`
**1 session | ~30 files**

Socket.IO trace stream receiving `trace_stage_update` events end-to-end. All API client paths correct. Auth token refresh working.

---

### PHASE 4 — Quality, Infrastructure, and Completion (11 sessions)

| Session | Area | Key questions |
|---|---|---|
| A18 | `tests/` (20 subdirs) | 21 skipped tests justified? StrataMind benchmark runnable? Resilience tests inject real failures? Dual-engine (SQLite + PostgreSQL) confirmed? |
| A19 | `backend/services/` | RAG actually populating context? Audio/video real or stub? |
| A20 | `backend/middleware/` | All 9 active in app factory? Correct ordering? |
| A21 | `backend/mcp_server/` | LY-4 inversion fix confirmed? Sampling/subscriptions working? |
| A22 | `backend/ingestion/` | Populates ChromaDB (linked to A12)? Async queue and Neo4j sync working? |
| A23 | `backend/memory/` | `unified_memory_service.py` wraps StructuredMemoryGraph as DB-M claimed? |
| A24 | `backend/observability/` | Sentry wired? SLO alerts firing? Metrics Prometheus-compatible? |
| A25 | `backend/operator/` | What is this pattern? Used by anything? If not: document or remove. |
| A26 | `backend/tracing/` | Separate from TruthMemory? Both fire on query? |
| A27 | `backend/schemas/` | `request_schemas.py` vs `api_request_schemas.py` — duplicate? |
| A28 | `backend/*.py` root-level | `graphql_schema.py` live or dead? `celery_app.py` workers running? `app.py` factory correct after N1 wiring? |
| A29 | `core/engine/`, `core/graph/`, `core/memory/`, `core/nlp/`, `core/orchestration/` | All wired to pipeline? `graph_manager.py` interface matches SekreEngine (N1) expectations? |
| A30 | `config/`, `migrations/`, `deploy/`, `k8s/` | Migration head correct? k8s manifests include Ollama (Sprint 6)? `.env.template` has `OLLAMA_*` vars? |
| A31 | `docs/` (~50 md files) | `ARCHITECTURE.md` current with Sprint 6? `SECURITY.md` consistent with SC-2? `openapi.yaml` current? |
| A32 | `scripts/` | Audit scripts clean and committed? `seed_data.py` guarded? Stale files cleaned up? |

---

## Complete Session Sequence

`✅` done · `⏭` next · `☐` pending

```
Sprint 0  ✅ (RT-1..RT-18 already done 2026-06-07/08; this session did N3 + N4)
  RT-1..RT-18  ✅ already complete
  N3     ✅ Delete 4 legacy axis files
  N4     ✅ Resolve Axis 4/5 gap in axis_system.py (+ honeycomb Axis-3 bug fix)

Phase 1 — Live query path:
  A4 ✅ → A3 ✅ → A1a ✅ → A1b ✅ → A2 ✅ → A5 ✅ → A6a ✅ → A6b ✅   [PHASE 1 COMPLETE]

  Interleaved:
  N2   ✅ Wired defense_supervisor.txt during A3
  N1   ✅ Wired SekreEngine post-L10 in SimulationEngine (A6b)
  A2-2 ✅ DSQP LLM-assisted construction (dsqp_answer_generator.py)

Phase 2 — Reasoning depth (8 sessions):
  A7 → A8a → A8b → A9 → A10 → A11 → A12 → A13 → A14

  Execute remaining RT tasks (RT-4 through RT-18) before Phase 3.

Phase 3 — Frontend (4 sessions):
  A15 → A16 → A17

Phase 4 — Quality + ops (11 sessions):
  A18 → A19 → A20 → A21 → A22 → A23 → A24 →
  A25 → A26 → A27 → A28 → A29 → A30 → A31 → A32
```

---

## Total Estimate

| Phase | Sessions |
|---|---|
| Sprint 0 | 1 |
| Phase 1 | 7 |
| Phase 2 | 8 |
| Phase 3 | 4 |
| Phase 4 | 11 |
| **Total** | **~31 sessions** |

---

## Definition of Done

The audit is complete when ALL of the following are true:

1. Every folder in this plan has been audited via live MCP code reads
2. Every file is in its architecturally correct location
3. Every feature is wired to the live pipeline — no disconnected modules (SEKRE, defense_supervisor confirmed wired)
4. Every duplicate resolved to a single canonical implementation
5. All dead code removed: orphaned files, legacy layer variants, unused prompt files
6. Security: all HIGH-RISK security files confirmed real; password hashing ≥12 rounds confirmed; `defense_supervisor.txt` wired into security pipeline
7. SEKRE wired into post-L10 feedback loop on Tier 3+ runs
8. All 117 KAs rated (real/heuristic/stub); all HIGH-RISK KAs confirmed real with tests
9. All 17 axes load correctly from single authoritative files; no duplicates
10. `core/simulation/` layer map produced — single live implementation identified per layer
11. DSQP audit written statement confirming implementation matches technical disclosure
12. Full pytest green (≥1,855 passed, 21 skipped max, 0 failures)
13. `ruff check .` clean
14. Both SQLite and PostgreSQL pass for all phases (dual-engine requirement)
15. Installer smoke test passes on clean Windows install
16. `TODO.md`, `HANDOFF.md`, and `REPO_AUDIT_LOG.md` updated after every session

---

*DataLogicEngine Complete Audit Plan v2.0 — June 10, 2026*
*Built from: live MCP scan + full 9-session conversation history review*
*Previous plan: `docs/audits/DataLogicEngine_Complete_Audit_Plan.md` (v1.0, superseded)*
