# CP19-C selector and dependency-DAG audit

**Date:** 2026-07-25
**Status:** Passed at source checkpoint
**Release effect:** None; production remains NO-GO and rebuilding remains blocked

## Finding

The CP19-A manifest contained the metadata needed for selection but no canonical
selector, typed plan, dependency executor, or truthful plan/execution state
model. Selection policies and fixture destinations were descriptive only.
Subsystem callers would therefore have needed private ID lists or direct KA
calls.

The dependency inventory contained 122 declared edges and three reciprocal
cycles:

- `KA-065` Knowledge Regression Tester ↔ `KA-1099` System Integrity Auditor;
- `KA-1099` System Integrity Auditor ↔ `KA-117` Knowledge Integrity Validator;
- `KA-1100` Autonomous System Evolution Controller ↔ `KA-1111` Long-Horizon
  Goal Drift Monitor.

Those cycles made deterministic prerequisite execution impossible.

## Correction

The runtime manifest remains the only selector identity and contract authority.
CP19-C adds:

- `ManifestKASelector`, which consumes normalized intent, 17-axis coordinate
  values, domain, layer, persona, risk, owner, stage, category, explicit
  capability requests, policy, scopes/context, service capability, prior
  results, request mode, and request-wide budgets;
- `KASelectionPlan`, which classifies all 213 KAs as selected, denied,
  unavailable, skipped, or blocked and separately identifies required,
  optional, and dependency roles;
- deterministic transitive dependency expansion, namespaced
  `dependency_results`, cycle/depth/fan-out/selected-count/input/deadline checks,
  and topological execution batches;
- `KAPlanExecutor`, which uses bounded `TaskGroup` structured concurrency for
  independent pure KAs, cancels siblings when required work fails, re-raises
  parent cancellation, serializes effect proposals, and never marks a proposal
  as applied;
- truthful planned, candidate, selected, admitted, dependency, executing,
  executed, skipped, blocked, unavailable, failed, cancelled, timed-out, and
  effect-proposed trace states; and
- 213 generated fixture files, each containing a positive and negative selector
  case. The intentionally reserved `KA-033` positive request proves mandatory
  denial rather than pretending a reserved capability executed.

The reciprocal relationships are corrected into prerequisite order without
renaming, deleting, merging, or duplicating any capability:

1. `KA-065` performs regression testing without depending on downstream
   integrity aggregation.
2. `KA-117` consumes `KA-065` and `KA-1094` contradiction evidence.
3. `KA-1099` consumes completed `KA-065` and `KA-117` results.
4. `KA-1111` consumes long-horizon planning from `KA-1112`.
5. `KA-1100` consumes `KA-1111`, `KA-1107`, and `KA-1108` before admitting an
   evolution action.

The corrected graph has 119 edges and zero cycles. Every dependency result uses
the canonical `dle.ka-execution-result.v1#output` envelope under the
`dependency_results` namespace.

## Qualification

- 213 positive selector fixtures verified;
- 212 executable capabilities selected under evaluation fixtures;
- one reserved capability denied exactly as designed;
- 213 negative fixtures verified not selected;
- 213/213 primary owners and 213/213 implementation entrypoints present;
- dependency identity, ordering, cycle, depth, fan-out, count, input, and
  critical-path budget checks pass;
- required-failure, policy denial, unavailable service, deadline, output-size,
  parent cancellation, structured-concurrency, serialized effect-proposal, and
  real-controller paths are covered by focused tests; and
- effect application remains unauthorized pending CP19-I.

Machine evidence:
`cp19-c-selector-dag-verification.json`.

## Boundary and next checkpoint

CP19-C establishes the reusable selector/DAG substrate. It does not claim that
the ten layers are already inside the public governed lifecycle, that effect
ports are applied, or that the rebuilt-installed application has passed. CP19-D
must now place applicable L1-L10 stage plans inside the one
`GovernedExecutionOrchestrator` answer lifecycle.
