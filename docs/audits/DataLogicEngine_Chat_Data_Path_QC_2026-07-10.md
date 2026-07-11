# DataLogicEngine Chat Data Path QC

**Date:** 2026-07-10  
**Scope:** Packaged desktop enhanced chat, Google Gemini routing, DMRF/DSQP execution, trace persistence, and Trace Explorer rendering.

## Verified path

```text
ChatInterface
  -> POST /api/v1/gateway/chat
  -> authenticated GatewayRequest
  -> one gateway run_id
  -> governance checks
  -> desktop DMRF control plane
  -> TruthGate, tier, 17-axis route
  -> concurrent DSQP axes 8-11
  -> SDK overlay reuses the DMRF persona chain
  -> selected Google Gemini provider executes the final model call
  -> moderated result and telemetry are merged
  -> TraceRun, TraceStage, TracePersona, TraceKAInvocation, TraceAxisVector
  -> gateway response returns the same run_id and real trace summary
  -> ChatTracePanel fetches /trace/runs/{run_id}/bundle
```

## Findings

1. Desktop enhanced chat did not enable DMRF by default even though active architecture documents describe DMRF as the request control plane.
2. DMRF used the synchronous DSQP adapter while running inside an asynchronous request.
3. DMRF and the SDK overlay independently constructed the same four personas, producing duplicate provider work and avoidable latency.
4. The SDK overlay persisted a trace before moderation and before DMRF metadata was attached. The later final persistence call would not add missing stages because stage rows already existed.
5. DMRF steps, the 17-axis vector, KA invocations, and provider identity were not fully persisted into the trace contract.
6. `TraceRun.to_dict()` returned nested model data while the frontend reads `model_name` and `provider_used`.
7. The gateway API hardcoded confidence to `0.85`, returned no trace summary, and always reported zero evidence regardless of the actual response object.
8. Trace statuses such as `ok` were not normalized to `pass`, so completed stages could appear unfinished.
9. Trace bundle duration summed only stage durations and could omit most of the provider latency.
10. High-tier audit anchoring attempted `asyncio.run()` inside the active gateway event loop.

## Corrections

- Enabled DMRF by default for packaged desktop enhanced chat while preserving explicit opt-out and server deployment configuration.
- Changed DMRF to await concurrent DSQP construction.
- Reused the DMRF persona chain in the SDK overlay and removed premature trace persistence.
- Merged DMRF control-plane steps with SDK stages before a single final persistence operation.
- Persisted axis routing, personas, KA invocations, provider/model identity, normalized statuses, completion time, confidence, and end-to-end latency.
- Returned real confidence and renderer-compatible trace summary values from the gateway API.
- Updated trace serialization to match frontend field names.
- Avoided nested event-loop execution during audit anchoring.

## Validation

- Backend, DMRF, SDK, gateway API, persistence, and trace contract: 74 tests passed.
- Frontend chat and trace contract: 34 tests passed.
- Frontend TypeScript type check: passed.
- Ruff checks for changed Python modules: passed.

## Installed-app acceptance check

After installing the rebuilt desktop package, submit one new enhanced chat prompt and confirm:

1. Provider/model shows Google and `gemini-3.1-pro-preview`.
2. The response and Trace Explorer use the same run ID.
3. Trace stages include DMRF control-plane and SDK/KA records.
4. Four DSQP personas appear once, not twice.
5. Confidence, model, provider, coordinate, completion time, and latency are populated.
6. Evidence remains zero only when no structured local evidence was retrieved.
7. Runtime logs contain no OpenAI attempt, duplicate DSQP pass, schema mismatch, or trace persistence failure for the run.
