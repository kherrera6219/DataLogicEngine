# Phase 4b — Quad Persona File Split Execution Plan

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.0.0 |
| Created | 2026-06-04 |
| Branch | `phase-4b-quad-persona-file-split` |
| Status | Active execution plan |
| Scope | Mechanical refactor only |

## Purpose

Phase 4b splits the three oversized files in `core/persona/quad/` into smaller
subpackages while preserving import compatibility and behavior.

This is deliberately separate from Phase 5. Do **not** fix correctness bugs in
this branch unless the owner explicitly expands the scope. Known Phase 5 items
include naive/aware datetime handling, random confidence jitter, salted `hash()`
embeddings, unreachable confidence threshold, mutable class-level config state,
and axis 9/10 secondary-influence mapping.

## Source documents reviewed

- `docs/HANDOFF_quad_persona.md`
- `docs/REPO_AUDIT_LOG.md`
- `TODO.md`
- `README.md`
- `core/persona/quad/__init__.py`
- `core/persona/quad/mathematical_framework.py`
- `core/persona/quad/persona_scaling.py`
- `core/persona/quad/pod_orchestrator.py`
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

- `core/persona/quad/pod_orchestrator.py`
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

## Target file layout

### 1. `mathematical_framework/`

Replace `core/persona/quad/mathematical_framework.py` with a package directory:

```text
core/persona/quad/mathematical_framework/
  __init__.py
  weights.py
  memory_graph.py
  refinement.py
  integration.py
```

Planned allocation:

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

`mathematical_framework/__init__.py` must re-export every public name listed in
the compatibility target.

Expected internal dependencies:

- `weights.py` imports `KnowledgePoint` from `.memory_graph`.
- `integration.py` imports:
  - `DynamicWeightFunctions`, `KnowledgeSpaceMapper` from `.weights`
  - `StructuredMemoryGraph` from `.memory_graph`
  - `DeepRecursiveLearning`, `RefinementWorkflow12Step` from `.refinement`

### 2. `persona_scaling/`

Replace `core/persona/quad/persona_scaling.py` with a package directory:

```text
core/persona/quad/persona_scaling/
  __init__.py
  profiles.py
  sufficiency.py
```

Planned allocation:

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

`persona_scaling/__init__.py` must re-export every public name listed in the
compatibility target.

Expected internal dependencies:

- `profiles.py` imports `SubsystemProfile` from `core.persona.quad.pod_models`.
- `sufficiency.py` imports:
  - `SufficiencySignals`, `ExpansionPlan`, `ScalingDecision`, `SubsystemProfile`
    from `core.persona.quad.pod_models`
  - profile dictionaries from `.profiles`

### 3. `pod_orchestrator/`

Replace `core/persona/quad/pod_orchestrator.py` with a package directory:

```text
core/persona/quad/pod_orchestrator/
  __init__.py
  builder.py
  synthesis.py
  orchestrator.py
```

Planned allocation:

- `builder.py`
  - `PersonaBuilder`
- `synthesis.py`
  - `PodSynthesizer`
  - `CrossPodDeconfliction`
- `orchestrator.py`
  - `PodOrchestrator`
  - `create_pod_orchestrator`

`pod_orchestrator/__init__.py` must re-export every public name listed in the
compatibility target.

Expected internal dependencies:

- `builder.py` imports:
  - `PodType`, `ExpandedPersona` from `core.persona.quad.pod_models`
  - profile dictionaries from `core.persona.quad.persona_scaling`
- `synthesis.py` imports:
  - `PodType`, `ExpandedPersona`, `PodState`, `CrossPodConflict` from
    `core.persona.quad.pod_models`
- `orchestrator.py` imports:
  - `PersonaBuilder` from `.builder`
  - `PodSynthesizer`, `CrossPodDeconfliction` from `.synthesis`
  - required pod models from `core.persona.quad.pod_models`

## Circular import watchlist

The highest-risk circular path is:

```text
pod_orchestrator.builder
  -> persona_scaling profiles
  -> pod_models
```

This should be safe because `persona_scaling.profiles` should not import
`pod_orchestrator`. If a circular import appears, prefer narrowing imports to
specific submodules (`persona_scaling.profiles`) instead of broad package imports.

Avoid importing `PodOrchestrator` from `core.persona.quad.pod_orchestrator` inside
`persona_scaling`.

## Test plan

### Focused import smoke test

Add a new test file, for example:

```text
tests/persona/quad/test_phase4b_import_compatibility.py
```

Required assertions:

```python
def test_mathematical_framework_compat_exports():
    from core.persona.quad.mathematical_framework import (
        DynamicWeightFunctions,
        KnowledgePoint,
        MemoryVertex,
        MemoryEdge,
        StructuredMemoryGraph,
        KnowledgeSpaceMapper,
        DeepRecursiveLearning,
        RefinementWorkflow12Step,
        IntegrationFunction,
        QuadPersonaMathematicalSystem,
    )


def test_persona_scaling_compat_exports():
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


def test_pod_orchestrator_compat_exports():
    from core.persona.quad.pod_orchestrator import (
        PersonaBuilder,
        PodSynthesizer,
        CrossPodDeconfliction,
        PodOrchestrator,
        create_pod_orchestrator,
    )
```

Also include a light instantiation test:

```python
def test_phase4b_factories_still_construct():
    from core.persona.quad.persona_scaling import create_sufficiency_tool
    from core.persona.quad.pod_orchestrator import create_pod_orchestrator
    from core.persona.quad.mathematical_framework import QuadPersonaMathematicalSystem

    assert create_sufficiency_tool() is not None
    assert create_pod_orchestrator() is not None
    assert QuadPersonaMathematicalSystem() is not None
```

### Focused existing tests

Run:

```bash
python -m pytest -q --no-cov tests/persona/quad/test_persona_scaling.py tests/persona/quad/test_phase4b_import_compatibility.py
```

### Handoff Group A

Run the Group A tests from `docs/HANDOFF_quad_persona.md`:

```bash
python -m pytest -q --no-cov tests/persona/quad/ tests/unit/test_phase5_phase_c.py tests/unit/test_phase_d_dsqp.py tests/benchmarks/test_dsqp_benchmark.py
```

### Import users

Run tests or import checks covering current import users:

```bash
python -m pytest -q --no-cov \
  tests/persona/quad/ \
  tests/unit/test_phase5_phase_c.py
```

If test files exist for the gateway/truth/memory callers, add them to the local
validation command after discovering the correct targeted tests.

### Static checks

Run:

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

## Execution steps

1. Create/commit this plan.
2. Convert `mathematical_framework.py` into the package layout.
3. Add `mathematical_framework/__init__.py` compatibility re-exports.
4. Run the focused mathematical framework import smoke locally if available.
5. Convert `persona_scaling.py` into the package layout.
6. Add `persona_scaling/__init__.py` compatibility re-exports.
7. Convert `pod_orchestrator.py` into the package layout.
8. Add `pod_orchestrator/__init__.py` compatibility re-exports.
9. Add focused import compatibility tests.
10. Run focused tests.
11. Fix import wrapper breakage only.
12. Update this plan's "Post-move findings" section with anything discovered.
13. Run the broader Group A tests.
14. Open a draft PR and do not merge until CI is green.

## Post-move findings

Update this section after the move.

Template:

```markdown
### Finding N — <short title>

- Discovered during: <split/import/test/static check>
- Impact: <what would break>
- Action added to plan: <wrapper/test/import update>
- Status: <open/done/deferred>
```

## Definition of done

- Three oversized files are replaced by package directories.
- Existing public import paths continue to work.
- Import compatibility tests exist and pass.
- Existing persona scaling tests pass.
- Group A tests pass or any failure is documented with root cause.
- `ruff check` passes for changed files.
- Docs reference validation passes.
- No Phase 5 behavior changes are included.
- Draft PR summarizes import compatibility and validation evidence.
