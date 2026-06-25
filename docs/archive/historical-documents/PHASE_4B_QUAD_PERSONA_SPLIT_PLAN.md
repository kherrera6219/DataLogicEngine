# Phase 4b — Quad Persona File Split Execution Plan

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.3.0 |
| Created | 2026-06-04 |
| Last updated | 2026-06-04 |
| Branch | `phase-4b-quad-persona-file-split` |
| Status | Complete — implemented and locally validated |
| Scope | Mechanical refactor only |

## Purpose

Phase 4b splits the three oversized files in `core/persona/quad/` into smaller
subpackages while preserving import compatibility and behavior.

This is deliberately separate from Phase 5. Do **not** fix correctness bugs in
this branch unless the owner explicitly expands the scope. Known Phase 5 items
remain deferred: naive/aware datetime handling, random confidence jitter, salted
`hash()` embeddings, unreachable confidence threshold, mutable class-level config
state, and axis 9/10 secondary-influence mapping.

## Source documents reviewed

- `docs/HANDOFF_quad_persona.md`
- `docs/REPO_AUDIT_LOG.md`
- `TODO.md`
- `README.md`
- `core/persona/quad/__init__.py`
- `core/persona/quad/mathematical_framework/`
- `core/persona/quad/persona_scaling/`
- `core/persona/quad/pod_orchestrator/`
- `tests/persona/quad/test_persona_scaling.py`

## Non-negotiable constraints

1. Preserve behavior.
2. Preserve existing public import paths.
3. Keep old module-level imports working through package `__init__.py` re-exports.
4. Avoid broad caller rewrites unless a circular import makes it necessary.
5. Keep Phase 5 correctness changes out of this branch.
6. Add/update focused import-smoke tests so future refactors do not break wrappers.
7. Update this plan after the move if any new wrappers, imports, or tests are discovered.

## Current import inventory to preserve

### `core.persona.quad.mathematical_framework`

Current import users found by repository search:

- `backend/memory/unified_memory_service.py`
- `backend/knowledge_algorithms/ka_38_consensus_engine.py`
- `backend/truth_engine/truth_core/refinement_orchestrator.py`
- `backend/truth_engine/truth_core/personas.py`
- `tests/unit/test_phase5_phase_c.py`

Compatibility target:

```python
from core.persona.quad.mathematical_framework import (
    KnowledgePoint,
    MemoryVertex,
    MemoryEdge,
    DynamicWeightFunctions,
    KnowledgeSpaceMapper,
    StructuredMemoryGraph,
    DeepRecursiveLearning,
    IntegrationFunction,
    RefinementWorkflow12Step,
    QuadPersonaMathematicalSystem,
)
```

### `core.persona.quad.persona_scaling`

Current import users found by repository search:

- `core/persona/quad/pod_orchestrator.py` before split; now internal imports use package submodules.
- `core/simulation/pov_engine_enterprise.py`
- `tests/persona/quad/test_persona_scaling.py`

Compatibility target:

```python
from core.persona.quad.persona_scaling import (
    DEFENSE_SUBSYSTEM_PROFILES,
    SECTOR_SUBSYSTEM_PROFILES,
    REGULATORY_PROFILES,
    COMPLIANCE_PROFILES,
    HighAssuranceDetector,
    SubsystemDetector,
    PersonaSufficiencyTool,
    create_sufficiency_tool,
)
```

### `core.persona.quad.pod_orchestrator`

Current import users found by repository search:

- `backend/llm_gateway/gateway.py`
- `core/simulation/pov_engine_enterprise.py`
- `backend/truth_engine/truth_core/engine.py`
- `tests/persona/quad/test_persona_scaling.py`

Compatibility target:

```python
from core.persona.quad.pod_orchestrator import (
    PersonaBuilder,
    PodSynthesizer,
    CrossPodDeconfliction,
    PodOrchestrator,
    create_pod_orchestrator,
)
```

## Implemented file layout

### 1. `mathematical_framework/`

`core/persona/quad/mathematical_framework.py` was replaced by:

```text
core/persona/quad/mathematical_framework/
  __init__.py
  weights.py
  memory_graph.py
  refinement.py
  integration.py
```

Allocation:

- `weights.py`
  - `DynamicWeightFunctions`
  - `KnowledgeSpaceMapper`
- `memory_graph.py`
  - `KnowledgePoint`
  - `MemoryVertex`
  - `MemoryEdge`
  - `StructuredMemoryGraph`
- `refinement.py`
  - `DeepRecursiveLearning`
  - `RefinementWorkflow12Step`
- `integration.py`
  - `IntegrationFunction`
  - `QuadPersonaMathematicalSystem`
- `__init__.py`
  - Re-exports all legacy public names.

### 2. `persona_scaling/`

`core/persona/quad/persona_scaling.py` was replaced by:

```text
core/persona/quad/persona_scaling/
  __init__.py
  profiles.py
  sufficiency.py
```

Allocation:

- `profiles.py`
  - `DEFENSE_SUBSYSTEM_PROFILES`
  - `SECTOR_SUBSYSTEM_PROFILES`
  - `REGULATORY_PROFILES`
  - `COMPLIANCE_PROFILES`
- `sufficiency.py`
  - `HighAssuranceDetector`
  - `SubsystemDetector`
  - `PersonaSufficiencyTool`
  - `create_sufficiency_tool`
- `__init__.py`
  - Re-exports all legacy public names.

### 3. `pod_orchestrator/`

`core/persona/quad/pod_orchestrator.py` was replaced by:

```text
core/persona/quad/pod_orchestrator/
  __init__.py
  builder.py
  synthesis.py
  orchestrator.py
```

Allocation:

- `builder.py`
  - `PersonaBuilder`
- `synthesis.py`
  - `PodSynthesizer`
  - `CrossPodDeconfliction`
- `orchestrator.py`
  - `PodOrchestrator`
  - `create_pod_orchestrator`
- `__init__.py`
  - Re-exports all legacy public names.

## Circular import watchlist

The highest-risk circular path remains:

```text
pod_orchestrator.builder
  -> persona_scaling.profiles
  -> pod_models
```

Mitigation implemented:

- `pod_orchestrator.builder` imports profile registries directly from
  `core.persona.quad.persona_scaling.profiles`, not from the broader compatibility
  package.
- `persona_scaling.profiles` imports only `SubsystemProfile` from `pod_models`.
- `persona_scaling.sufficiency` imports profile dictionaries from `.profiles` and
  does not import `pod_orchestrator`.

## Added test coverage

Added/expanded:

```text
tests/persona/quad/test_phase4b_import_compatibility.py
```

Coverage added:

- Legacy `core.persona.quad.mathematical_framework` exports.
- Legacy `core.persona.quad.persona_scaling` exports.
- Legacy `core.persona.quad.pod_orchestrator` exports.
- Direct imports for every new submodule location:
  - `mathematical_framework.weights`
  - `mathematical_framework.memory_graph`
  - `mathematical_framework.refinement`
  - `mathematical_framework.integration`
  - `persona_scaling.profiles`
  - `persona_scaling.sufficiency`
  - `pod_orchestrator.builder`
  - `pod_orchestrator.synthesis`
  - `pod_orchestrator.orchestrator`
- Compatibility exports point to the expected new module locations through
  `__module__` assertions.
- Factory/constructor smoke checks for:
  - `create_sufficiency_tool()`
  - `create_pod_orchestrator()`
  - `QuadPersonaMathematicalSystem()`
- Light runtime wiring check:
  - `PersonaSufficiencyTool.evaluate(...)` creates an expanded decision.
  - `PodOrchestrator.orchestrate(...)` consumes that decision and completes an
    expanded-pod flow.

## Required validation commands

Focused tests:

```bash
python -m pytest -q --no-cov tests/persona/quad/test_persona_scaling.py tests/persona/quad/test_phase4b_import_compatibility.py
```

Handoff Group A:

```bash
python -m pytest -q --no-cov tests/persona/quad/ tests/unit/test_phase5_phase_c.py tests/unit/test_phase_d_dsqp.py tests/benchmarks/test_dsqp_benchmark.py
```

Static checks:

```bash
ruff check core/persona/quad tests/persona/quad
python scripts/verify_docs_references.py
```

Before merge, run the full phase gate from `docs/HANDOFF_quad_persona.md`:

```bash
python -m pytest tests/ --no-cov
ruff check .
bandit -r backend/ core/ -ll -ii
python scripts/verify_docs_references.py
```

## Execution checklist

- [x] Create/commit this plan.
- [x] Convert `mathematical_framework.py` into the package layout.
- [x] Add `mathematical_framework/__init__.py` compatibility re-exports.
- [x] Convert `persona_scaling.py` into the package layout.
- [x] Add `persona_scaling/__init__.py` compatibility re-exports.
- [x] Convert `pod_orchestrator.py` into the package layout.
- [x] Add `pod_orchestrator/__init__.py` compatibility re-exports.
- [x] Add focused import compatibility tests.
- [x] Add direct submodule location tests.
- [x] Add light sufficiency-to-orchestrator wiring test.
- [x] Run focused tests.
- [x] Run broader Group A tests.
- [x] Run static checks.
- [x] Open draft PR.
- [x] Confirm local validation before merge.

## Post-move findings

### Finding 1 — File-to-package import compatibility is the main breakage risk

- Discovered during: split planning and repository import search.
- Impact: Existing callers import from `core.persona.quad.mathematical_framework`,
  `core.persona.quad.persona_scaling`, and `core.persona.quad.pod_orchestrator`.
  Replacing `.py` modules with directories would break callers unless package
  `__init__.py` files re-export the same names.
- Action added to plan: Added compatibility `__init__.py` wrappers and dedicated
  import-smoke tests.
- Status: Done and locally validated.

### Finding 2 — Avoid broad package imports in internal split modules

- Discovered during: circular import watchlist review.
- Impact: `pod_orchestrator.builder` needs profile registries from persona scaling.
  Importing from the broad compatibility package could create future circular risk.
- Action added to plan: `pod_orchestrator.builder` imports from
  `persona_scaling.profiles` directly.
- Status: Done and locally validated.

### Finding 3 — Phase 5 correctness bugs were intentionally deferred from Phase 4b

- Discovered during: code review while splitting.
- Impact: `MemoryVertex` still uses naive `datetime.utcnow`, pod confidence still
  uses random jitter, and `QuadPersonaMathematicalSystem._embed_query` still uses
  salted Python `hash()`. These are correctness/auditability issues but are Phase 5,
  not Phase 4b.
- Action added to plan: No behavior fix included; document as deferred so the
  Phase 4b PR stays mechanical.
- Status: Closed by the follow-on Phase 5 correctness pass.

### Finding 4 — Local validation completed in Windows checkout

- Discovered during: follow-up live-code review.
- Impact: The Phase 4b validation commands now have local evidence in the Windows
  checkout.
- Evidence:
  - `python -m pytest -q --no-cov tests/persona/quad/test_persona_scaling.py tests/persona/quad/test_phase4b_import_compatibility.py` — 35 passed.
  - `python -m pytest -q --no-cov tests/persona/quad/ tests/unit/test_phase5_phase_c.py tests/unit/test_phase_d_dsqp.py tests/benchmarks/test_dsqp_benchmark.py` — 46 passed.
  - `python -m ruff check core/persona/quad tests/persona/quad` — clean.
  - `python -m ruff check .` — clean.
  - `python scripts/verify_docs_references.py` — 0 errors.
  - `python -m pytest tests/ --no-cov` — 1821 passed, 21 skipped.
- Status: Done.

### Finding 5 — Import smoke alone is insufficient

- Discovered during: owner review question after first draft PR.
- Impact: A pure import smoke test can prove wrappers exist but not that the new
  submodule locations are importable directly or that the sufficiency-to-pod path is
  still wired in a usable way.
- Action added to plan: Expanded `test_phase4b_import_compatibility.py` with direct
  submodule imports, `__module__` location assertions, and a light runtime wiring
  check from `create_sufficiency_tool().evaluate(...)` to
  `create_pod_orchestrator().orchestrate(...)`.
- Status: Done and locally validated.

## Definition of done

- [x] Three oversized files are replaced by package directories.
- [x] Existing public import paths have compatibility re-export wrappers.
- [x] Import compatibility tests exist.
- [x] Direct new-location tests exist.
- [x] Light sufficiency-to-orchestrator wiring test exists.
- [x] Import compatibility tests pass.
- [x] Existing persona scaling tests pass.
- [x] Group A tests pass.
- [x] `ruff check` passes for changed files.
- [x] Docs reference validation passes.
- [x] No Phase 5 behavior changes are included.
- [x] Draft PR summarizes import compatibility and validation evidence.
