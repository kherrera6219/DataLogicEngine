# CP19-G canonical 12-step refinement integration

**Date:** 2026-07-25
**Status:** Passed at source checkpoint
**Release effect:** None; production remains NO-GO and rebuilding remains blocked

## Finding

CP19-F completed the causal persona path, but no single working production
12-step refinement workflow existed. The repository retained separate
TruthCore, simulation, system, and Quad Persona variants. One could not
construct because it imported a nonexistent registry, one incremented
confidence heuristically, others used simulated or demonstration logic, and
the private TruthCore variant swallowed per-step failures. None was the
provider, trace, persistence, or release path. The governed product only
performed a bounded provider retry.

## Correction

The runtime manifest now carries one versioned
`dle.refinement-workflow-registry.v1` owned by
`GovernedExecutionOrchestrator`. It defines exactly 12 unique ordered steps:

1. structured decomposition;
2. alternative branches;
3. missing information and unresolved claims;
4. input, source, and evidence validation;
5. deep causal and analytical review;
6. self-critique and contradiction review;
7. ethics, security, privacy, risk, and compliance;
8. recursive-learning decision;
9. semantic and intent alignment;
10. authorized external validation;
11. synthesis and measured scoring; and
12. memory and lifecycle proposal.

`CanonicalRefinementWorkflow` is entered only from the committed initial L9
`refine` decision. It executes steps serially, consumes committed prior layer
and KA results, and executes new applicable KAs only through the canonical
manifest selector and bounded DAG executor. Every step records `executed`,
`skipped`, `blocked`, or `failed`; a required failure accounts for all remaining
steps as skipped and stops before the provider rewrite.

CP19-G production-qualifies `KA-003`, `KA-005`, `KA-011`, and `KA-025` for
their bounded deterministic refinement roles. `KA-025` now measures the actual
dependency graph, depth, unknown dependencies, and cycles instead of returning
a fixed DAG result. `KA-011` explicitly reports that confidence adjustment is
not measured. These outputs are structure and heuristic observations, not
external evidence, calibrated probability, or release authority.

The current manifest remains one 213-capability authority with 132 live
registry entries and zero unregistered Layer 9 implementations. It now has 29
production-enabled capabilities and 131 dependency edges with zero cycles. The
corrected `KA-003` prerequisite reflects its real self-contained pre-synthesis
gap comparison.

## Provider, validation, effect, and trace boundary

The 12 steps make zero provider subcalls. After all findings are collected, the
orchestrator may make exactly one provider rewrite. The rewritten candidate is
then revalidated through L6, L7, L8, and the complete fail-closed L9 suite
before the complete L10 release gate. A second refinement cycle is not
authorized.

External validation is explicitly skipped unless a separately qualified and
authorized service exists; the trace does not claim it occurred. Step 12 emits
one deterministic memory/lifecycle proposal with `applied: false`, no receipt,
and an explicit requirement for L10 release plus an authoritative service.
Validated-memory promotion is not performed by the refinement workflow.

The retained TruthCore, core simulation, system, and Quad mathematical
implementations now declare `PRODUCTION_ENTRYPOINT = False` and an explicit
reference disposition. The public governed assembly imports only the canonical
workflow. The private historical TruthCore workflow may lazy-load its legacy
adapter for compatibility tests, but it is not constructed by the governed
product path.

## Causal and adversarial proof

- the manifest registry has exactly 12 unique ordered steps;
- all 12 steps are accounted in both success and required-failure runs;
- the normal refinement fixture records 10 executed and two truthful skips;
- the rewrite prompt contains the committed step accounting and constraints;
- provider accounting is one initial candidate plus at most one rewrite;
- refinement KAs make zero provider subcalls;
- the rewritten candidate re-enters L6-L9 and reaches L10 only afterward;
- required `KA-003` failure blocks after the initial candidate and before the
  rewrite;
- the lifecycle proposal is unapplied and has no receipt;
- external validation is not claimed when unauthorized;
- the five retained workflow variants are non-production entrypoints; and
- no second runtime registry, KA ID, implementation owner, or product answer
  path was created.

## Boundary and next checkpoint

CP19-G closes finding F-06 at the source checkpoint. It does not establish the
authoritative Truth/data/knowledge lifecycle, extended subsystem/effect
integration, complete API/SDK/desktop workflow, complete per-KA proof,
clean-source rebuild authorization, or installed acceptance. CP19-H is active
and the rebuild remains blocked through CP19-L.
