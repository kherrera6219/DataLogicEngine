# CP19-K per-KA qualification matrix

**Matrix version:** `2026.08.01-cp19k.6`
**Status:** `cp19_k_in_progress`
**Release decision:** NO-GO; rebuild not authorized

## Current result

The generated matrix contains all 213
canonical capabilities. 34 rows are fully
qualified and 179 remain open. A row closes
only when its individually reviewed evidence has an exact named semantic test,
both selector fixtures, a real owning-path test, an accepted limitation, causal
trace proof, and applicable security, effect, and performance evidence.

The complete row detail is in `ka-qualification-matrix.json` and
`ka-qualification-matrix.csv`.

## Completed batches

| Batch | Date | Qualified KAs | Scope |
|---|---|---:|---|
| `cp19-k-batch-01-governed-l1` | 2026-08-01 | 3 | Canonical governed L1 normalization, adversarial blocking, and candidate decomposition |
| `cp19-k-batch-02-dmrf-routing` | 2026-08-01 | 2 | Production-admitted DMRF query classification and complexity routing |
| `cp19-k-batch-03-simulation-core` | 2026-08-01 | 7 | Causal simulation planning, resource admission, counterfactual context, and artifact proposal |
| `cp19-k-batch-04-mcp-admission` | 2026-08-01 | 3 | MCP credential discovery, policy admission, access admission, and authorization-bound connector receipts |
| `cp19-k-batch-05-mcp-result-governance` | 2026-08-01 | 6 | MCP risk and threat-model admission plus fail-closed connector-result release governance |
| `cp19-k-batch-06-mcp-records-recovery` | 2026-08-01 | 4 | MCP structured logging with durable audit/receipt records plus fail-closed recovery planning and authoritative plan receipts |
| `cp19-k-batch-07-provider-boundary` | 2026-08-01 | 2 | Pre-call context-budget governance and post-call measured monitoring at the canonical provider boundary |
| `cp19-k-batch-08-operations-observability` | 2026-08-02 | 7 | Authenticated content-free diagnostics visualization, dashboard, report planning, alerting, profiling, debugging, and optimization recommendations |

## Gate decision

CP19-K remains active. This partial matrix does not authorize CP19-L, rebuilding,
installed acceptance, signing, or production/public release.
