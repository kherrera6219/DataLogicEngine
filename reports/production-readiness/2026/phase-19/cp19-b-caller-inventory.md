# Phase 19 CP19-B Knowledge Algorithm caller inventory

Date: 2026-07-25  
Checkpoint: CP19-B  
Status: passed at source-contract scope  
Release effect: none; rebuild and production/public release remain blocked

## Outcome

All existing production Python call sites under `backend/` and `core/` now use
the canonical typed Knowledge Algorithm result boundary. The retained legacy
methods exist only as compatibility definitions; no production caller invokes
`execute_algorithm`, `execute_legacy`, or `execute_ka`.

The source verifier scanned 621 production Python files, found 32 typed
execution/helper call sites, verified 18 migrated internal/API/SDK caller
surfaces, and found zero legacy execution call sites.

## Migrated caller surfaces

| Surface | Canonical contract disposition |
|---|---|
| KA Master | Internal orchestration and background execution use `KAExecutionResult`; the historical envelope remains an external compatibility method. |
| TruthCore | Preflight, routing, workflow steps, and direct KA invocation consume typed results and named output fields. |
| Layer 6 | KA-039 and KA-116 consume their real output schemas; failure adds explicit risk and validation evidence. |
| Layer 7 | KA-002, KA-040, and KA-021 consume real schemas; a required execution failure produces a failed plan. |
| Layer 8 | Required KA checks consume named canonical fields and the gate fails closed on contract failure. |
| Layer 9 | L9-specific KAs and KA-008/010/022/025 consume their live semantics and schemas; injected-controller failures refine rather than silently skip. |
| Layer 10 | Required calls use typed results and named fields; the remaining identity drift produces HALT instead of releasing unchanged content. |
| Quad Persona adapter | KA-012 consumes `persona_results`; missing confidence is recorded as unmeasured/zero rather than invented. |
| Refinement | Each step consumes the typed result and records success, failure, trace, and unchanged-confidence provenance. |
| Core KA engine/loader | Both compatibility facades expose an internal `execute_typed` boundary backed only by the canonical controller. |
| Query Persona | The loader call is typed and a failed required call no longer falls back to a different KA with fabricated confidence. |
| POV | KA-028 and KA-057 use their real inputs and named outputs. |
| Simulation | Routing, selection, persona, and pipeline consumers read typed results; trace IDs replace private execution IDs and missing confidence is zero. |
| SEKrE | Conditional enhancement calls use typed results and canonical trace IDs. |
| KA API | Single and batch execution serialize the canonical typed result, trace ID, and duration at the HTTP boundary. |
| Python SDK | The authenticated API-backed executor retains the canonical result and has no private handler registry. |
| TypeScript SDK | The generated `dle.ka-execution-result.v1` type is the client contract authority. |

## Real-controller evidence

- Layer 9 completed its real-controller path using L9-KA-001 through
  L9-KA-006 plus KA-008, KA-010, KA-022, and KA-025.
- Layer 10 proved fail-closed behavior against the currently wrong KA-108
  semantic mapping: the result is HALT and the candidate answer is not
  released.
- The core engine and loader returned `dle.ka-execution-result.v1`.
- Simulation routing consumed KA-113 and KA-031 outputs; persona execution
  consumed KA-012; POV execution consumed KA-028 and KA-057.
- API authentication/shape regressions and Python SDK canonical-client tests
  pass.

## Boundaries retained for later checkpoints

CP19-B repairs result-shape consumption. It does not claim semantic completion
for subsystems that did not previously have a direct KA caller. The following
work remains in the mandatory plan order:

- CP19-C: manifest selector and bounded dependency DAG;
- CP19-D: one governed L1-L10 product path;
- CP19-E: correct Layer 9/Layer 10 identity, full required suites, and trace
  parity;
- CP19-F: causal KA-backed Quad Persona and DSQP;
- CP19-G: one canonical production 12-step workflow;
- CP19-H: Truth/data/knowledge lifecycle call paths and effects;
- CP19-I: simulation, MCP, provider, security, operations, and effect ports;
- CP19-J: complete API/SDK/desktop/accessibility workflow;
- CP19-K through CP19-M: 213-row proof, clean source qualification, rebuild,
  and exact installed acceptance.

These are not waivers. Data, MCP, provider, and operations surfaces with no
pre-existing direct KA call are integration work for CP19-H/CP19-I, not
contract-migration successes.

## Evidence

- `scripts/verify_ka_contract_parity.py`
- `reports/production-readiness/2026/phase-19/cp19-b-contract-parity-verification.json`
- `tests/knowledge_algorithms/test_phase19_cp19b_contract_parity.py`

