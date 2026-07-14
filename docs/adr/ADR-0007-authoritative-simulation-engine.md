# ADR-0007: Authoritative Simulation Engine

## Document metadata

| Field | Value |
|---|---|
| Status | Accepted - Phase 10 engineering selection; production qualification open |
| Date | 2026-07-14 |
| Owner | Platform Architecture |
| Decision scope | User-triggered simulation workflow and internal simulation provider calls |
| Supersedes | Duplicate production authority implied by legacy/core simulation entry points |
| Superseded by | None |

## Context

DataLogicEngine had three overlapping simulation concepts:

1. a user-triggered multi-agent debate engine under `backend/simulation/`;
2. a large layered core engine under `core/simulation/simulation_engine.py`;
3. a legacy UAE/FROST engine under `core/simulation/legacy_simulation_engine.py`.

The live route correctly stopped at `SIMULATION_PHASE10_BOUNDARY`, but old
TruthCore and core-system initialization still imported duplicate engines. The
core/legacy paths use in-process state, synthetic or turn-derived confidence,
templated output, and no production provider, budget, restart, or store authority.
`FROSTService` itself is a snapshot/delta service and should not be confused with
a complete simulation workflow.

Phase 10 requires one versioned engine, hard provider/tool budgets, durable
progress and lifecycle state, evidence-backed results, safe cancellation, and no
recursive call into the full governed pipeline for each debate turn.

## Decision

The sole user-triggered simulation engine is the backend multi-agent debate
workflow, rebuilt around `dle-simulation.v1`.

- `backend/simulation/multi_agent_engine.py` is the selected workflow base.
- Every run uses an immutable `SimulationPlan` that declares participants,
  debate turns, maximum provider calls, and output-token ceiling before work.
- Provider access occurs only through a simulation-specific adapter exposing
  `generate_simulation_turn`. It has no `process` or `execute` entry point and
  enforces cancellation, deadline, call, and token budgets.
- Confidence remains `not_measured`/null until explicit validators and evidence
  calculate a versioned result. Turn count, text length, and agreement cannot
  create confidence.
- PostgreSQL owns sessions, steps, events, calls, evidence, checkpoints, and
  artifact references; Redis owns content-free lease/state/progress/cancel
  coordination; the app-owned S3 service will retain large transcripts and
  artifacts. Neo4j/Chroma materializations are optional and revisioned.
- `FROSTService` may be reused behind the checkpoint/artifact interface for
  deterministic snapshot hashing and verification. It is not an execution
  authority.
- `core/simulation/simulation_engine.py` and
  `core/simulation/legacy_simulation_engine.py` are historical/reference code.
  Production routes, TruthCore initialization, and new application code must not
  import or execute them. Production entry points no longer import or instantiate
  those engines.

## Alternatives considered

### Make the layered core engine authoritative

Rejected. It contains the broadest historical feature set, but rehabilitating
its duplicate orchestration, synthetic confidence, in-memory lifecycle, and many
layer dependencies would increase the production and security surface without a
clear user-contract advantage.

### Make the legacy UAE/FROST engine authoritative

Rejected. It encodes simulated confidence progression and historical artifact
semantics and has no production provider/budget/durability contract.

### Keep multiple engines selectable

Rejected. Multiple production authorities would duplicate policy, provider,
budget, persistence, testing, and UI behavior and violate the plan's one-engine
requirement.

### Remove FROST entirely

Rejected for now. Snapshot hashing, verification, branch, and rollback concepts
may be useful behind the selected engine's checkpoint interface after they pass
store, security, and recovery qualification.

## Consequences

Positive:

- one small, auditable execution path;
- exact preflight provider ceilings;
- no recursive governed pipeline calls per turn;
- truthful null confidence until validators exist;
- clear persistence and UI authority for the durable workflow.

Costs and constraints:

- the selected engine carries the durable lifecycle implementation and must
  retain contract compatibility;
- old core imports and tests must be classified as compatibility or archived;
- FROST cannot claim production use merely because its snapshot component is
  retained;
- installed provider, restart, recovery, UI, performance, and cancellation
  qualification remain open.

## Acceptance boundary

This ADR accepts the engineering architecture only. CP10-A through CP10-E now
pass at the source/engineering boundary: durable authority, restart safety,
pause/resume/cancel/retry, fixed-seed determinism, validator/evidence confidence
truth, desktop contracts, and provider budget/cost enforcement are implemented.
This does not make simulation production-ready. Rebuilt-installed live-provider,
service/materialization, artifact, lifecycle, and UI acceptance remain open.

## Implementation references

- `backend/simulation/contracts.py`
- `backend/simulation/provider_adapter.py`
- `backend/simulation/providers.py`
- `backend/simulation/jobs.py`
- `backend/simulation/validation.py`
- `backend/simulation/multi_agent_engine.py`
- `backend/routes/simulation_routes.py`
- `migrations/versions/d9e0f1a2b3c4_add_durable_simulation_authority.py`
- `reports/production-readiness/2026/phase-10/inventory.md`
- `reports/production-readiness/2026/phase-10/summary.md`
- `tests/unit/test_phase10_simulation_authority.py`
