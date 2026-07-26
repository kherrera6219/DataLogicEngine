# CP19-I extended subsystem and authoritative effect integration

**Date:** 2026-07-25

**Status:** Passed at source checkpoint

**Release effect:** None; production remains NO-GO and rebuilding remains blocked

## Finding

CP19-H connected the Truth, ingestion, retrieval, graph, memory, and lifecycle
owners, but the durable simulation job, MCP connector, provider gateway, and
security/operations consumers still did not execute their applicable KAs
through the one manifest/controller boundary. Effect-oriented KA outputs also
had an available-service check but the selector did not enforce the declared
effect-proposal count. Simulation, MCP, and provider effects therefore lacked
one common, content-hashed receipt shape tied to their causal KA plan.

## Runtime authority

Manifest `2026.07.25-cp19i.1` retains all 213 canonical identities and one
implementation/controller per identity. It production-enables 149 capabilities
in total. The extended registry contains four owner/consumer groups, 81
operation references, and 65 distinct canonical IDs. Reuse between provider,
MCP, and security/operations operations is a governed consumer edge, not a
duplicate implementation. The dependency graph remains 136 edges with zero
cycles.

`ExtendedSubsystemCoordinator` reads that registry from the canonical manifest
and uses only `ManifestKASelector`, `KAPlanExecutor`, and
`CanonicalKAController`. No subsystem-private registry, provider client,
connector, database, queue, or answer path was added.

## Simulation and durable job path

- The durable simulation job executes bounded resource planning,
  reasoning-boundary validation, compatibility routing, and orchestration KAs
  before provider preflight or any provider call.
- A failed or semantically blocked KA plan records
  `SIMULATION_KA_ADMISSION_BLOCK`, makes zero provider calls, and creates no
  simulation artifact.
- The completed simulation result executes `KA-1091` as an unapplied outcome
  proposal before the existing job service persists the two required
  artifacts.
- The job service records a SHA-256-bound, idempotent applied receipt tied to
  the KA plan; the KA never claims the artifact write.

## MCP, security, and operations path

- Existing consent, authenticated-principal, and scope enforcement remains the
  authority. The KA admission plan runs afterward and before the connector
  call.
- `KA-022`, `KA-136`, `KA-137`, `KA-177`, and `KA-179` provide bounded risk,
  threat, sensitive-input, policy, and access proposals. Inline credentials
  block before the connector receives a request.
- Governed connector output then executes `KA-010`, `KA-096`, `KA-097`,
  `KA-175`, and `KA-182` for bias, content-free logging/audit, declared-control
  review, and threat-signal proposals. Prompt-injection output stays explicitly
  untrusted; planned security work is not presented as a scan or applied
  response.
- The durable MCP execution ledger now retains content-free KA plan evidence
  and a hashed authoritative connector receipt. Alembic revision
  `f1a2b3c4d5e6` is the single schema head.

## Provider and gateway path

- `KA-1072` validates that required provider context fits the declared input
  budget before provider discovery, history persistence, or an external call.
- The existing gateway remains the only provider client, call-budget owner,
  timeout/retry owner, and usage-ledger writer.
- After a real successful call and durable usage-ledger write, `KA-084`
  evaluates measured latency without inventing quality labels.
- The provider stage retains content-free request/monitoring evidence and a
  SHA-256-bound receipt tied to the existing idempotency key. A failed
  post-call KA check prevents answer release, retains the already-applied
  call's receipt, and does not retry that call.

## Effect budget and receipt boundary

The selector now rejects a plan when its effect-oriented proposal count exceeds
`KABudget.max_effects`. Authoritative callers declare bounded proposal counts;
zero rejects before execution. This budget authorizes KA proposal evaluation
only. It does not authorize a store, connector, provider, policy, or operations
effect.

`AuthoritativeEffectReceipt` accepts only a completed owning-service effect,
nonempty service/operation/resource/idempotency identity, and valid request and
result SHA-256 values. It rejects proposal or fabricated states. Simulation,
MCP, and provider services bind their receipts only after their existing
authoritative work completes.

## Proof

- 20 focused Phase 19 integration tests pass;
- 126 affected simulation, MCP, provider, governed-execution, selector, and
  lifecycle tests pass;
- all 767 Knowledge Algorithm tests pass;
- all 2,550 source tests pass with 19 skipped and 21 known warnings;
- all six TypeScript SDK tests pass;
- the 25-revision migration chain has one base and one head;
- manifest, runtime-authority, capability-inventory, integration-authority,
  selector/DAG, product-version, documentation, and source-hygiene gates pass;
- the retained KA upgrade verifier now passes against canonical deterministic
  `KA-136` and `KA-005` instead of importing the retired KA-117 threat-model
  prototype;
  and
- Python compilation and critical Ruff checks pass.

## Boundary and next checkpoint

CP19-I does not claim the authenticated KA product API/SDK/desktop
plan-confirm-execute-cancel-history-trace-artifact/effect workflow, complete
213-row individually named proof, rebuild authorization, installed acceptance,
signing, accessibility, external review, provider-human acceptance, or soak
completion. CP19-J is active. The signed rebuild remains blocked through
CP19-L; exact rebuilt-installed acceptance remains CP19-M.
