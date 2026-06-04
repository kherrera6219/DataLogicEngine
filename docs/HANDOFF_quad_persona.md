# Handoff — Quad Persona Consolidation

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-06-04 |
| Status | Active — in progress |
| Owner | Platform Architecture |
| Review cadence | Per phase |

## Purpose

Single handoff for the quad-persona consolidation so any contributor (or a future
session / Codex) can resume with full context. Phases 1–4 are merged to `main`;
Phases 4b, 5, and 6 remain. Companion reports (shared with the user, also in the
audit trail): `quad_persona_audit.md`, `quad_persona_provider_report.md`,
`quad_persona_consolidation_report.md`, `assess_core_persona.md`,
`assess_dsqp_backend.md`, `quad_persona_master_audit_plan.md`. Running log:
`docs/REPO_AUDIT_LOG.md`.

---

## Current state (after Phase 4, `main` @ 4898eb2e)

**Canonical persona system (source of truth):**
- `backend/dsqp/` — REAL, deterministic seven-component persona construction for
  axes 8–11; wired into the DMRF/TruthCore live request path.
- `core/system/PersonaConstructionService` — REAL, live, uses `backend/dsqp`.

**Shared quad-persona library (relocated, REAL, load-bearing):**
- `core/persona/quad/` — `models.py`, `quad_models.py`, `pod_models.py`,
  `persona_scaling.py`, `pod_orchestrator.py`, `mathematical_framework.py`,
  `axis_role_mapper.py`, `persona_loader.py`, `quad_engine.py`,
  `config/quad_config.yaml`. Imported by ~19 sites in `backend/`, `core/`,
  `scripts/`, `demos/`. Tests at `tests/persona/quad/`.

**Removed:** the top-level `quad_persona/` package (relocated), the broken
`create_quad_persona_engine` crash path on `/direct-query`, the duplicate/shadowed
root engine, and the orphaned `core/persona/` stub package.

**Still separate (intentionally untouched):**
- `backend/quad_persona/quad_engine.py` — the async LLM-consultation engine
  (reached only via gateway `mode=="quad"`). Has a broken import (see Phase 6).
- `core/simulation/query_persona_engine.py` — a different KE/SE/RE/CE engine, not
  an axes-8–11 duplicate. Leave alone.

### Completed commits
| Phase | Commit | Summary |
|---|---|---|
| 1 | `47b760de` | Route `/direct-query` to canonical DSQP; fix live TypeError; regression test |
| 2 | `7398f0a6` | De-duplicate root engine; extract models; 1703→~290 lines; fix factory |
| 3 | `6c21774b` | Remove orphaned `core/persona/` stub package |
| 4 | `4898eb2e` | Relocate library to `core/persona/quad/`; migrate imports; move tests |

---

## Remaining work

### Phase 4b — Split the oversized library files (mechanical, low-risk)

All three now live in `core/persona/quad/`. Split each into a sub-package with a
re-export `__init__.py` so importers don't change.

| File | Lines | Proposed split |
|---|---|---|
| `mathematical_framework.py` | 840 | `mathematical_framework/` → `weights.py` (DynamicWeightFunctions, KnowledgeSpaceMapper), `memory_graph.py` (KnowledgePoint, MemoryVertex, MemoryEdge, StructuredMemoryGraph), `refinement.py` (DeepRecursiveLearning, RefinementWorkflow12Step), `integration.py` (IntegrationFunction, QuadPersonaMathematicalSystem) |
| `persona_scaling.py` | 783 | `profiles.py` (hardcoded profile dicts) + `sufficiency.py` (HighAssuranceDetector, SubsystemDetector, PersonaSufficiencyTool) |
| `pod_orchestrator.py` | 752 | `builder.py` (PersonaBuilder) + `synthesis.py` (PodSynthesizer, CrossPodDeconfliction) + `orchestrator.py` (PodOrchestrator) |

The `__init__.py` of each must re-export the public names consumers import
(`DynamicWeightFunctions`, `MemoryEdge/Vertex`, `StructuredMemoryGraph`,
`IntegrationFunction`, `DeepRecursiveLearning`, `PersonaSufficiencyTool`,
`create_pod_orchestrator`, `PodOrchestrator`, etc.). Verify with the import smoke
test pattern used in Phase 4.
**Tests:** `tests/persona/quad/test_persona_scaling.py` (34 tests) must stay green.

### Phase 5 — Fix library correctness bugs (verified line numbers on `main`)

| Bug | Location | Fix |
|---|---|---|
| Naive vs aware datetime → `TypeError` on memory age | `mathematical_framework.py:94,97` (`field(default_factory=datetime.utcnow)`) subtracted at `:432` (`datetime.now(UTC) - memory.timestamp`) | Make `timestamp`/`last_accessed` timezone-aware: `default_factory=lambda: datetime.now(UTC)` |
| Non-deterministic confidence in an auditable system | `pod_orchestrator.py:663-664` (`import random; variation = random.uniform(-0.05, 0.05)`) | Remove the random jitter; derive variation deterministically or drop it |
| Non-reproducible embeddings (salted `hash()`) | `mathematical_framework.py:818` (`np.random.seed(hash(text) % (2**32))`) | Seed from a stable hash, e.g. `int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)` |
| Unreachable convergence threshold | `mathematical_framework.py:619` (`CONFIDENCE_THRESHOLD = 0.995`); conflicts with `config/quad_config.yaml` (`0.7`) | Lower to a reachable value and/or source it from config |
| Mutable class-level state clobbered per instance | `persona_scaling.py:429,445` (`THRESHOLDS`/`POD_CAPS` class dicts) mutated at `:458,461` via `.update()` in `__init__` | Deep-copy into instance attributes before updating |
| Axis 9/10 secondary-influence mislabel | `axis_role_mapper.py:228-239`: primary map says 9=sector, 10=regulatory (`:30-31`), but secondary code writes `axis_vector[10]="Value"` for sector and `axis_vector[9]="Risk"` for regulatory | Reconcile to one axis scheme; fix the secondary indices/comments |

**Tests:** add focused regression tests for each (datetime decay path, threshold
reachability, deterministic embedding, axis vector mapping, threshold isolation).
None of these have direct unit tests today.

### Phase 6 — Decision: `backend/quad_persona` broken LLM wiring

`backend/quad_persona/quad_engine.py` (`_call_llm` ~`:58`, synthesis ~`:218`) does
`from llm_gateway.gateway import get_llm_gateway` — but there is no top-level
`llm_gateway` package and `get_llm_gateway`/`chat_completion` are defined nowhere
(0 grep hits). Every persona call raises `ImportError` → caught → all 4 personas
return `status:"error"` → "Insufficient data for synthesis". The "PRODUCTION /
REAL LLM" banner is aspirational. It ships green only because the one test
(`tests/unit/test_phase5_phase_c.py:~69`) monkeypatches it with a fake engine.

**Options:** (a) wire to the real `backend.llm_gateway` API and add a
non-monkeypatched `_run_quad_analysis` test; or (b) stop labeling it production and
treat it as the experimental `mode=="quad"` path. **Decision required from owner.**

---

## Per-phase gate (must pass before each merge)

1. Affected tests + full `pytest tests/ --no-cov` green (baseline: 1807 passed / 27
   skipped).
2. `ruff check .` clean.
3. `bandit -r backend/ core/ -ll -ii` no new high-severity.
4. `python scripts/verify_docs_references.py` 0 errors.
5. Conventional Commit; branch; rebase on latest `origin/main` (coordinate with
   Codex); fast-forward merge; confirm GitHub CI/CD Pipeline (backend-test, lint,
   governance), Security Scan, and Deploy green. `frontend-build` /
   `windows-packaging-smoke` are long-running and unrelated to persona changes.

### Test groupings (avoid the cross-dir `conftest` shadowing — run unit/integration separately)
- Group A: `tests/persona/quad/ tests/unit/test_phase5_phase_c.py tests/unit/test_phase_d_dsqp.py tests/benchmarks/test_dsqp_benchmark.py`
- Group B: `tests/integration/test_api_endpoints.py tests/contract/test_canonical_v1_route_contracts.py`
- Group C: `tests/dmrf/test_dmrf_integration.py tests/phase_g/test_phase_g_integrations.py tests/knowledge_algorithms/test_phase_e_depth.py`

## Environment notes (sandbox)

The sandbox needs these pip installs that aren't auto-present (CI installs from
`requirements.txt`): `neo4j chromadb bleach user_agents web3` (and `ruff`,
`bandit[toml]` for the gates). Run with `PYTHONPATH=/home/user/workspace/DataLogicEngine`.

## Change notes for v2.6.0

- 2026-06-04: Handoff created after merging Phases 1–4. Documented current state,
  the remaining Phase 4b/5/6 work with verified line numbers, the per-phase gate,
  and sandbox environment notes.
