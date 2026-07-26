# CP19-F Quad Persona and DSQP causal integration

**Date:** 2026-07-25
**Status:** Passed at source checkpoint
**Release effect:** None; production remains NO-GO and rebuilding remains blocked

## Finding

CP19-E completed the fail-closed Layer 9 and Layer 10 safety suites, but the
candidate-preparation path still constructed DSQP profiles without executing
the applicable persona KAs. The retained persona definitions also encoded a
reversed dependency relationship, invented default confidence, and simulated a
mediator/confidence adjustment. Those outputs could not be treated as measured
reasoning or causal application evidence.

## Correction

The canonical manifest now production-admits the deterministic applicable
persona chain:

1. `KA-012` consumes all four validated DSQP axes 8-11 profiles and emits
   profile-linked findings, constraints, and objections.
2. `KA-013` consumes the committed `KA-012` result and normalizes domain
   authority weights while preserving measured profile status and dissent.
3. `KA-030` consumes the committed `KA-013` result and carries every retained
   objection forward as a mandatory prompt constraint.

The corrected dependency order is `KA-012` -> `KA-013` -> `KA-030`. The
current manifest remains one 213-capability authority with 132 live registry
entries and zero unregistered Layer 9 implementations. It has 25
production-enabled capabilities and 132 dependency edges with zero cycles.

Layer 4 executes `KA-012` once through the canonical selector and bounded DAG
executor. Layer 5 executes `KA-013` and `KA-030` once through the same
authority, then constructs the provider prompt from committed persona findings,
weights, sufficiency, retained dissent, and conflict constraints. Changing a
DSQP profile changes that prompt and the single provider candidate. Required
persona execution failure or insufficient/lost dissent blocks before the
provider call.

The three persona KAs make zero provider subcalls and do not invent a confidence
score, consensus probability, mediator response, or confidence adjustment.
Validated profiles without a numeric coverage score remain explicitly
threshold-only; absence is not replaced by a guessed number. Other
persona-owned KAs remain preserved and selectable for their applicable stages
but are not falsely invoked in this pre-candidate chain.

## Effect and trace boundary

The persona execution result is committed to the governed child-trace cache.
KA invocation evidence is derived from executed child traces only. Persona
analysis emits one proposal-only effect record with `applied: false` and no
receipt. The legacy Quad Persona engines have no direct production caller and
remain noncanonical compatibility/reference surfaces.

## Causal and adversarial proof

- all four axes 8-11 profiles are validated and consumed;
- `KA-012`, `KA-013`, and `KA-030` execute in exact dependency order and once;
- a profile change changes the provider prompt and candidate;
- the canonical provider is called once and persona provider subcalls are zero;
- missing or failed required weighting blocks before the provider;
- every objection is retained and silent dissent is zero;
- confidence and coverage values are not fabricated;
- unrelated persona KAs are not falsely reported as invoked;
- the persona effect remains unapplied and has no receipt; and
- direct legacy Quad Persona production callers remain zero.

## Boundary and next checkpoint

CP19-F closes finding F-07 at the source checkpoint. It does not establish the
canonical 12-step refinement workflow, authoritative data/effect integration,
complete API/SDK/desktop workflow, complete per-KA proof, clean-source rebuild
authorization, or installed acceptance. CP19-G is active and the rebuild
remains blocked through CP19-L.
