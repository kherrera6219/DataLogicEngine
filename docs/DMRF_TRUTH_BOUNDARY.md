# DMRF vs Truth Engine boundary

| Field | Value |
|---|---|
| Date | 2026-09-27 |
| Status | Code-aligned product language; one display defect open |

## Live path

1. **Gateway** admits the request and selects virtual model.
2. **GovernedExecutionOrchestrator** runs L1–L10.
3. **DMRF** contributes tier/axis routing and injection defense on that path.
4. **Truth integration** on the live path is adapter-level (gate/scores), not a second private generative workflow.
5. **TraceRun** stores evidence; Truth Engine UI shows **telemetry from traces**.

## Naming

| Label in UI | Honest meaning |
|---|---|
| Truth Engine page | Gate/decision telemetry and scores from stored runs |
| Truth score | Average numeric confidence among available traces — not a separate AGI core or a calibrated probability of truth |

The current `frontend/app/truth-engine/page.tsx` display uses `0.0%` when no
trace has numeric confidence. That is an unmeasured state, not a measured zero;
the UI defect is open in root `TODO.md`. Do not interpret this placeholder as
evidence that a run failed TruthGate.

Public TruthCore entry points that process user queries must route through the **gateway / governed path** (enforced by `tests/governed_execution/test_single_path.py`).

## Not live product claims

- Standalone multi-agent TruthCore replacing the gateway
- Blockchain/web3 truth-link as required desktop dependency
