# CP18-D Knowledge Algorithm subsystem wiring audit

**Audit date:** 2026-07-25  
**Audited commit:** `15b5d7e79760fbc36365abfc7eae9b17da31b5ce`  
**Scope:** live source wiring for the canonical governed request path, DMRF,
TruthCore Layers 1-10, Layer 9, Layer 10, Quad Persona/DSQP, the 12-step
refinement workflows, TruthGate, TruthMemory, TruthLink, simulation,
retrieval/graph/memory, ingestion, MCP, providers/gateway, operations,
API/SDK, and the desktop Algorithms page.

## Decision

**FAIL / NO-GO. The application is not yet wired so every applicable
Knowledge Algorithm has a reachable, governed production call path.**

CP18-A established the 213-capability authority, CP18-B established a canonical
manifest/controller, and CP18-C closed the source implementation gaps. Those
results are real and retained. They do not satisfy CP18-D:

- only 42 of 213 canonical KAs have a statically detected execution call site;
- 171 of 213 have no detected execution call site;
- only 11 of 213 are marked `production_enabled`;
- 41 of 213 have no detected individually named test function;
- the product TruthCore preflight executes one KA in standard mode and two in
  enhanced mode, not the documented ten-layer workflow;
- the ten-layer and 12-step implementations that call more KAs are private,
  disconnected, broken, simulated, or otherwise outside the product path.

The crosswalk's call-site detector cannot recognize every dynamically
parameterized call, so `42` is a conservative static count rather than proof
that exactly 171 KAs are unreachable. The live caller trace below independently
confirms that the missing coverage is material, not a scanner-only artifact.

## What is wired correctly

1. The canonical manifest has 213 distinct implementation owners and zero
   implementation gaps.
2. `CanonicalKAController` is the implementation authority beneath
   `KAMasterController`, `KAEngine`, and `KALoader`.
3. The product request path is singular: admission, DMRF, retrieval,
   deterministic DSQP construction, TruthCore preflight, provider execution,
   validation, convergence, and persistence are owned by
   `GovernedExecutionOrchestrator`.
4. DMRF's gate, tier, 17-axis route, audit record, and TruthLink publication
   execute on that path.
5. DSQP constructs all four axes 8-11 profiles, and those profiles are included
   in the provider prompt. This is causal persona context, although it is not
   KA-driven persona analysis.
6. TruthCore preflight's executed KA outputs are included in the provider
   prompt.
7. The authenticated KA API can list and directly invoke canonical IDs, blocks
   non-production KAs unless the caller explicitly opts in, and is covered by
   route boundary tests.
8. The generated authority and capability inventory are current and their
   verification commands pass.

## Subsystem disposition

| Subsystem | Status | Live wiring result |
|---|---|---|
| Canonical chat/gateway | Partial | One governed path exists, but TruthCore preflight selects only `KA-113` and, for enhanced mode, `KA-001`. No manifest-driven capability selector dispatches the other applicable KAs. |
| DMRF | Partial | Gate, tiering, 17-axis routing, audit, and link publication are live. DMRF does not select/execute the wider KA catalog. |
| TruthCore Layers 1-10 | Fail | `_execute_workflow()` contains layer logic but has no production caller. Public `process()` re-enters the canonical gateway; the canonical gateway calls only the two-step preflight. |
| Layer 9 | Fail | Six L9 KAs are referenced only by the private workflow. `L9-KA-007` is declared but never executed. KA results are read using the obsolete flat result shape. |
| Layer 10 | Fail | The private sentinel calls some KAs, omits required L10 KAs, records one unexecuted KA as invoked, and uses several wrong canonical IDs. It is not on the product path. |
| Quad Persona / DSQP | Partial | DSQP profile construction is live and prompt-causal. It does not invoke `KA-012` or another KA selector. The async backend Quad engine and heuristic core Quad engine are not product callers. |
| 12-step refinement | Fail | The canonical gateway performs at most one provider refinement retry. The KA-backed 12-step TruthCore orchestrator is reachable only from the private ten-layer workflow. Another 12-step workflow cannot instantiate; other variants are heuristic/simulated. |
| TruthGate | Partial | The DMRF entry gate is live but does not use the KA controller. The KA-enhanced L8 gateway is private-path only and ignores nested KA outputs. |
| TruthMemory / TruthLink | Partial | DMRF audit persistence and event publication are live. Lifecycle, provenance, drift, containment, promotion, and release KAs are not selected by these modules. |
| Simulation | Fail | Canonical KA result parsing leaves the planned pipeline empty; persona KA availability checks always fail; optional infrastructure imports reference a missing package. |
| Retrieval / graph / memory | Fail for KA integration | The product path uses direct services. Applicable retrieval, lineage, lifecycle, drift, pruning, containment, and promotion KAs lack owning-subsystem dispatch. |
| Ingestion | Fail for KA integration | The ingestion pipeline does not call the canonical KA controller; `KA-071` through `KA-078` have no detected call sites. |
| MCP / provider / operations | Fail for broad KA integration | No selector dispatches applicable policy, security, operations, governance, or tool-containment KAs. Provider construction sees only the preflight's one or two KA outputs. |
| Self-evolving/SEKrE | Fail | It looks for non-canonical `KA_ENHANCE_*` IDs, finds none, and falls back to local basic enhancement instead of canonical KAs. |
| API / SDK / desktop UI | Partial | Direct-by-ID API/SDK execution exists. The desktop Algorithms page is a read-only catalog; it has no test/execute workflow, trace view, or effect confirmation surface. |

## Release-blocking findings

### F-01 - Critical: CP18-D selector and call-path coverage is absent

The canonical controller resolves and executes a caller-supplied ID; it is not
a capability selector. `KAMasterController._select_flow()` is a partial keyword
`elif` chain and is not called by the canonical governed request path. Its
branches cover only a minority of the catalog. `KA-031` can rank a small
hard-coded set but no production caller consumes its selected pipeline.

The current crosswalk reports:

- 213 canonical capabilities;
- 42 with a detected execution call site;
- 171 without one;
- 172 with a detected named test function;
- 41 without one.

This fails `DLE-FR-011` and CP18-D's requirement for a reachable owning-system
path plus positive and negative selector proof for every KA.

### F-02 - Critical: the production TruthCore path is not the ten-layer system

`TruthCoreDMRFAdapter.execute()` calls
`TruthCoreEngine.execute_governed_preflight()`. That preflight hard-codes:

- standard mode: `KA-113`;
- enhanced mode: `KA-113`, then `KA-001`.

`TruthCoreEngine._execute_workflow()` contains the broader layer sequence, L8,
L9, L10, persona scaling, memory, and 12-step refinement. It is called by tests
only. Public TruthCore session processing explicitly avoids it and enters the
canonical gateway instead. Consequently, passing isolated layer tests does not
prove that Layers 1-10 execute in the application.

### F-03 - Critical: canonical-result migration broke subsystem consumers

`KAMasterController.execute_algorithm()` now returns a compatibility envelope:

```text
{success, ka_id, output, execution_time_ms, trace_id, canonical_result}
```

TruthCore Layers 6-10, the persona enhancer, AGI planner, and refinement
orchestrator still read KA-specific fields at the top level. Examples include
`result.get("contradictions")`, `result.get("entropy_score")`,
`result.get("risk_adjustment")`, and `result.get("refined_content")`. The real
values are under `result["output"]`, so defaults are used and KA decisions are
silently discarded.

The focused subsystem suite exposed the same contract fracture:

```text
179 passed, 1 failed
tests/truth_engine/test_layer10_ka_suite.py:
KeyError: 'entropy_score'
```

Most other layer tests inject mock controllers that return the obsolete flat
shape, which is why they do not detect the live integration failure.

### F-04 - Critical: Layer-10 identity drift and fabricated invocation evidence

The Layer-10 sentinel contains canonical-ID mismatches:

| Intended behavior in caller | ID used | Actual canonical capability | Correct current capability |
|---|---|---|---|
| Capability escalation | `KA-108` | Backup Strategy | `KA-1108` |
| Knowledge containment | `KA-109` | System Health | `KA-1109` |
| Knowledge promotion gate | `KA-079` | Data Retrieval | `KA-1079` |
| Safety baseline | `KA-058` | Interactive Clarification & Learning | dedicated safety/containment policy required |
| Privacy baseline | `KA-059` | Predictive Layer Preemption | `L10-KA-003` / applicable privacy KA |

The sentinel appends `L10-KA-006` to `kas_invoked` without executing it.
`L10-KA-003`, `L10-KA-005`, and `L10-KA-007` are declared in the Layer-10 suite
but are not executed by the sentinel. `L9-KA-007` has the same declared-but-not-
called condition in Layer 9. These defects make the trace misleading and can
allow default-pass behavior in safety-sensitive logic.

### F-05 - High: the simulation KA path is functionally empty

Three independent defects prevent the intended simulation dispatch:

1. `_run_routing_step()` reads `results.output`, but `KAEngine` already places
   the KA output directly in `results`. The router falls back to `medium`, and
   the selected pipeline becomes `[]`.
2. Persona dispatch checks whether a string KA ID is contained in
   `KAEngine.list_algorithms()`, which returns dictionaries. The condition is
   always false and every persona component uses fallback text.
3. Layer infrastructure imports `backend.knowledge_algorithm.*`, a package
   that does not exist, leaving the axis mapper, truth engine, and workflow
   loader unset.

A direct live probe reproduced:

```text
complexity={'tier': 'medium'}
planned_pipeline=[]
axis_mapper=False
truth_engine=False
string_in_list_algorithms=False
```

### F-06 - High: no single working 12-step production refinement system exists

The repository retains several separate 12-step concepts:

- `backend/truth_engine/truth_core/refinement_orchestrator.py` calls 12 KAs but
  is reached only from the private ten-layer workflow and suppresses each step
  failure;
- `core/simulation/refinement_workflow.py` calls 12 KAs but cannot instantiate
  because `backend.knowledge_algorithm.registry` does not exist;
- `core/system/refinement_orchestrator.py` simulates progress by adding `0.05`
  confidence per step and does not call KAs;
- `core/simulation/refinement_orchestrator.py` is a legacy heuristic workflow
  with placeholder behavior and no canonical KA dispatch;
- the Quad mathematical workflow is deterministic demonstration logic and does
  not invoke canonical KAs;
- the production gateway performs one bounded provider retry, not the
  documented 12-step KA workflow.

The broken constructor was reproduced with:

```text
ModuleNotFoundError: No module named 'backend.knowledge_algorithm'
```

### F-07 - High: Quad Persona construction is live, but KA persona reasoning is not

The governed path correctly constructs deterministic DSQP profiles for axes
8-11 and includes them in the provider request. However:

- it does not execute `KA-012` or a persona-specific KA selector;
- `backend/quad_persona/quad_engine.py` has no product caller;
- `core/persona/quad/quad_engine.py` documents itself as demo-only and returns
  heuristic/static perspectives;
- TruthCore's `PersonaEnhancer` is private-path only and its `KA-012` fallback
  reads the obsolete flat result shape.

The application therefore has causal persona metadata, but not the intended
governed KA-backed multi-persona reasoning chain.

### F-08 - High: silent degradation violates CP18-D trace semantics

Many layer callers catch broad exceptions and log `skipped`, then continue with
optimistic defaults. Other examples continue when the controller is absent,
return heuristic outputs, or mark the workflow completed after failed
refinement steps. The most serious case is Layer 10, where a KA can be reported
as invoked without a call.

Required KAs must produce distinct `planned`, `selected`, `admitted`,
`executed`, `failed`, `skipped`, and `effect_applied` trace records. A missing
or failed required safety KA must fail closed rather than become an invisible
default.

## Other findings

### F-09 - Medium: existing tests overstate integration coverage

The focused suites are valuable and mostly green, but they primarily prove
isolated component behavior. Private-method tests invoke
`TruthCoreEngine._execute_workflow()` directly, and multiple layer tests use
mock controllers with the pre-CP18-B result shape. They do not prove reachability
from the desktop/chat/API product path.

The inventory's `172` named-test count is also a static reference detector, not
proof of one semantic functional test per KA. Forty-one KAs have no detected
named test at all.

### F-10 - Medium: active validation documents are semantically stale

`docs/REQUIREMENTS_TRACEABILITY.md`,
`docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md`,
`docs/DEVELOPER_GUIDE.md`, and
`docs/VERIFICATION_VALIDATION_REPORT.md` still stop at older CP18-C batch/count
snapshots. The root plan, TODO, and handoff contain the newer zero-
implementation-gap status. The documentation reference gate passes because it
checks structural references, not cross-document semantic freshness.

The KA manifest and capability-inventory generators also embed Phase 18 in
current limitation, guarantee, work-queue, and checkpoint labels. Phase 19 must
retain CP18 labels where they are historical provenance and migrate every
current/future qualification statement plus all generated Python, TypeScript,
JSON, and Markdown consumers.

## Verification performed

| Check | Result |
|---|---|
| Generated KA capability inventory check | Pass; four files current, zero changes |
| KA runtime authority verification | Pass |
| Focused governed/TruthCore/Quad/simulation/assembly tests | **Fail: 179 passed, 1 failed** |
| Standalone `RefinementWorkflow()` construction | **Fail: missing `backend.knowledge_algorithm`** |
| Simulation routing/persona live probe | **Fail: empty pipeline, missing infrastructure, false KA availability** |
| Enhanced TruthCore preflight probe | Pass for exactly `KA-113` and `KA-001`; confirms limited product scope |

## Required remediation sequence

1. Establish one result contract at every caller boundary. Either update all
   subsystem consumers to use `KAExecutionResult.output` or provide one
   explicitly versioned compatibility adapter; add a contract test using the
   real controller for every subsystem.
2. Replace the partial keyword chain with a versioned manifest-driven selector
   that evaluates intent, domain, risk, tier/layer/persona, evidence,
   dependencies, budgets, and policy.
3. Validate the selected dependency DAG, then execute it through
   `CanonicalKAController` with request-wide budget, cancellation, trace, and
   effect semantics.
4. Integrate the applicable ten-layer stages into the one governed product
   path. Do not revive a second provider/persistence path.
5. Correct every Layer-9/Layer-10 canonical ID, execute all required L9/L10 KAs,
   remove fabricated invocation entries, and fail closed on required safety
   failures.
6. Consolidate the 12-step definitions into one governed production workflow
   and retire or explicitly mark non-production variants.
7. Repair simulation result parsing, KA membership checks, imports, and
   selector-to-pipeline execution before relying on simulation tests.
8. Wire applicable KAs into DSQP/personas, retrieval/graph/memory, ingestion,
   MCP/tool policy, providers, operations, security, and lifecycle owners.
9. Add positive and negative selector fixtures, one named functional test per
   KA, real-controller subsystem integration tests, effect receipts, and causal
   trace/replay assertions.
10. Execute Phase 19 CP19-A through CP19-L before rebuilding; CP19-M installed
    acceptance remains blocked until the source/integration gate passes.

## Final conclusion

The KA implementations now exist, but the application does not yet use them as
the documented dynamic production system. The largest risk is not missing
source files; it is disconnected and contract-incompatible orchestration that
can appear successful while KA outputs are ignored.

## Post-audit phase disposition

After this audit, Phase 18 was closed with an incomplete-transfer disposition.
The failed findings were not waived or reclassified as passed. Section 27 of
`PRODUCTION_COMPLETION_PLAN_2026.md` transfers all unresolved work to Phase 19,
Canonical KA system-of-systems integration and qualification. CP19-L replaces
the unpassed Phase 18 source exit; CP19-M retains rebuilt-installed acceptance.
The rebuild and release remain blocked.
