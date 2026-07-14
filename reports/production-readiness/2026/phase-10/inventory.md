# Phase 10 Live Simulation Inventory

Date: 2026-07-14

Status: **Preserved before-state inventory. The engineering checkpoint is
complete; see `summary.md` and `validation.md`.**

## User-facing authority

- `backend/routes/simulation_routes.py` owns create/list/get/run/step/stop.
- Run/step deliberately enters `governed.v1` simulation mode and receives
  `SIMULATION_PHASE10_BOUNDARY`; it does not execute a legacy engine.
- `SimulationSession` is the only durable simulation table. It stores parameters,
  coarse status/step counts, and one JSON result, but has no durable steps,
  events, provider calls, evidence, checkpoints, artifact references, budget,
  cancellation request, engine/schema version, or restart lease.
- The frontend expects `uid`, while the API returns `session_id`. It subscribes
  to WebSocket progress that the route never emits and exposes only Create and
  Step. The stop route labels stopped work `completed` instead of `cancelled`.

## Candidate A: backend multi-agent debate

Path: `backend/simulation/multi_agent_engine.py`.

Strengths:

- Small, comprehensible user-triggered debate workflow.
- Already requires a simulation-specific `generate_simulation_turn` adapter and
  explicitly refuses recursive `LLMGateway.process` execution.
- Has bounded depth and one overall timeout.
- Matches the current product's scenario/persona/debate/synthesis interaction.

Gaps:

- Entire state is process memory and is deleted after each run.
- No durable lifecycle, restart, pause/resume, cancel, retry, progress, evidence,
  artifact, trace, or store reconciliation.
- Provider call ceiling and cost are not preflighted or enforced by an adapter.
- Confidence is fabricated from debate turn count; impact scores are length-based.
- Prompts and transcripts are unversioned and unbounded except per-turn output.

## Candidate B: core/FROST simulation stacks

Paths: `core/simulation/simulation_engine.py`,
`core/simulation/legacy_simulation_engine.py`, and their layer/orchestrator tree.
`core/system/frost_service.py` is a snapshot/delta service, not a complete
simulation engine.

Strengths:

- Broad layer, persona, refinement, snapshot, and deterministic-fixture coverage.
- FROST snapshot hashing/verification can be reused as a checkpoint/artifact
  component after authority and persistence are redesigned.

Gaps:

- Multiple large in-memory engines and duplicate orchestration entry points.
- Synthetic/fixed confidence, templated arguments, simulated progress, and
  legacy UAE/FROST semantics conflict with the Phase 6 evidence contract.
- No selected provider adapter, preflight spend/call ceiling, durable lifecycle,
  restart lease, or production store authority.
- Still imported by TruthCore initialization, the old master workflow, the
  system initializer, and app orchestrator even though the user-facing route is
  safely deferred.
- Rehabilitating the full stack would preserve duplicate execution authority and
  substantially increase the security and qualification surface.

## Initial selection recommendation

Use the backend multi-agent debate workflow as the sole Phase 10 simulation
engine, rebuilt around versioned contracts, a hard-budget simulation provider
adapter, PostgreSQL/Redis/S3 durability, explicit validators, and real progress.
Retain `FROSTService` only as an optional snapshot/checkpoint implementation.
Disable/archive production imports of the core/legacy engines and preserve them
as historical/reference test material until removal is safe.

This recommendation was accepted in ADR-0007 after the failure-first authority,
recursion, call-budget, confidence-truth, and API identity tests passed.

## First failure-first targets

1. One versioned scenario/budget/plan/result contract with exact depth call caps.
2. A provider adapter that exposes only simulation-turn generation, refuses
   nested governed execution, checks cancellation/deadline, and hard-stops at the
   preflight call/token ceiling.
3. No confidence value unless explicit validators/evidence measure it.
4. No production import or route path to either legacy/core engine.
5. One `session_id` client/API identity and truthful cancelled/deferred states.
6. Durable PostgreSQL step/event/call/checkpoint/artifact authorities and Redis
   content-free lease/state/progress coordination.
