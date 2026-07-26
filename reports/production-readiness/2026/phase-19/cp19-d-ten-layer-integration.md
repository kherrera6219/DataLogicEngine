# CP19-D canonical ten-layer integration

**Date:** 2026-07-25  
**Status:** Passed at source checkpoint  
**Release effect:** None; production remains NO-GO and rebuilding remains blocked

## Finding

The one `GovernedExecutionOrchestrator` already owned admission, DMRF routing,
retrieval, DSQP construction, provider execution, output validation,
convergence, trace persistence, and result release. Those operations were not
represented as the documented ten-layer reasoning lifecycle. The product path
called a TruthCore preflight that directly executed `KA-113` and, in enhanced
mode, `KA-001`; the fuller private TruthCore workflow separately owned answer
assembly and memory writes and therefore could not safely be called as another
public lifecycle.

The request context also lacked one typed state capable of carrying route,
evidence, persona, KA, candidate, validation, convergence, effect, and release
data causally from layer to layer.

## Correction

CP19-D adds transport-neutral L1-L10 stage executors and one typed
`GovernedReasoningState`. The state carries:

- request and trace identity;
- normalized query, tier, and 17-axis coordinate;
- trace-bound evidence IDs and DSQP axes 8-11 profiles;
- per-layer selector plan, typed KA result, decision, effect, and trace links;
- provider candidate, claims, citations, validators, measured confidence, and
  convergence; and
- the explicit L10 release decision.

The only public governed lifecycle now executes:

1. L1 normalization, adversarial admission, tier/risk routing, and coordinate
   binding;
2. L2 source-identified bounded retrieval;
3. L3 evidence-acquisition plan, disclosure, and budget recording;
4. L4 deterministic DSQP axes 8-11 context;
5. L5 one causal provider candidate plan;
6. the existing provider ledger/call boundary;
7. L6 evidence, provenance, contradiction, validator, and confidence
   measurement;
8. L7 evidence-dependency and reasoning-boundary review;
9. L8 governance, trust, privacy, security, and compliance gate;
10. L9 bounded finalize/refine/abstain/block convergence; and
11. L10 release before successful transactional trace/result persistence.

The numbering above separates the provider boundary; the durable reasoning
trace itself is exactly L1 through L10.

L1 derives a recipe from mode, DMRF tier, and risk. It submits only the
applicable production-qualified `KA-004`, `KA-061`, and `KA-001` set to the
CP19-C manifest selector/DAG. Typed normalization and shield results are
consumed directly. Coordinate text is retained as governed context rather than
being reinterpreted as a free-text selector query, preventing regulatory
Axis-17 values from over-selecting unqualified KAs.

The product path does not call `TruthCoreEngine._execute_workflow()` or
`execute_governed_preflight()`. The legacy preflight remains a direct
compatibility test surface. Historical trace hydration accepts former stage
names read-only; new traces bind retrieval to L2, validation to L6, and KA
invocations to L1.

## Causal and failure proof

- changing the selected `KA-004` normalized query changes the query sent to the
  provider;
- `KA-061` block/veto stops before retrieval and provider execution;
- changing retrieved evidence changes the final answer and trace-bound claim
  evidence;
- enhanced nonconvergence performs one bounded rewrite and re-enters L6-L9;
- repeated nonconvergence abstains;
- provider failure never creates L6-L10 success records;
- an L10 halt returns no answer and persists only the governed failure trace;
- success persistence occurs only after an L10 release record;
- local review records L1-L5, explicit L6-L9 not-applicable states, and an L10
  local-review release without calling a provider;
- the HIPAA/regulatory local-review regression proves selector scope remains
  production-qualified; and
- application reload now releases any prior lazy compatibility runtime lock,
  keeping the full Windows source suite stable after configuration-boundary
  tests.

## Boundary and next checkpoint

CP19-D establishes the canonical ten-layer lifecycle and causal shared state.
It does not claim full semantic execution of all Layer-9 and Layer-10 KAs.
CP19-E must correct the remaining ID drift, execute every required
`L9-KA-001` through `L9-KA-007` and `L10-KA-001` through `L10-KA-007`, derive
invocation lists from committed child traces, and fail closed on every missing,
failed, timed-out, privacy, containment, escalation, or release result.

Persona-KA depth, the canonical 12-step workflow, data/knowledge/effect
integration, per-KA proof, rebuilding, installed acceptance, and release remain
owned by CP19-F through CP19-M.

