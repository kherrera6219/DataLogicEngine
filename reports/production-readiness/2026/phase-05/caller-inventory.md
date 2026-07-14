# Phase 5 Governed-Execution Caller Inventory

Date: 2026-07-13

The inventory classifies answer-producing callers separately from diagnostic
and subsystem tools. An approved answer-producing caller must enter
`backend.governed_execution.GovernedOrchestrator` through `LLMGateway.execute()`
or construct the same `GovernedRequest` directly for the owned orchestrator.

| Surface | Entry | Canonical disposition |
|---|---|---|
| Built-in chat | `backend/chat.py` | Constructs `GovernedRequest`; canonical orchestrator. |
| Versioned external gateway chat | `backend/llm_gateway/api.py` | Converts the authenticated request to `GovernedRequest`; canonical orchestrator. |
| Gateway compatibility method | `LLMGateway.process()` | Thin compatibility conversion; delegates to `execute()`. |
| Gateway stream | `LLMGateway.process_stream()` | Delegates to the governed request path; transport currently emits the completed governed result. |
| Offline replay | `backend/llm_gateway/api.py` | Reconstructs a governed request and uses the same orchestrator. |
| REST API facade | `backend/rest_api.py` | Constructs `GovernedRequest`; canonical orchestrator. |
| Versioned query facade | `backend/routes/api_routes.py` | Constructs `GovernedRequest`; canonical orchestrator. |
| TruthCore session API | `backend/truth_engine/api.py` -> `TruthCoreEngine.process()` | Public compatibility adapter enters the canonical gateway; private workflow helper is not a public answer path. |
| High-stakes KA workflow | `backend/routes/ka_routes.py` | Uses the TruthCore public adapter and therefore the canonical orchestrator. |
| Persona direct query | `backend/persona_api.py` | Uses `local_review`; no provider answer is fabricated. |
| Persona governed query | `backend/persona_api.py` | Uses `simulation`; returns the explicit Phase 10 unavailable boundary. |
| Simulation routes | `backend/routes/simulation_routes.py` | Enter `simulation` mode and stop immediately after admission at the Phase 10 boundary; no retrieval, DSQP, KA, provider, or tool side effects. |
| Simulation engine provider hook | `backend/simulation/multi_agent_engine.py` | Does not call the gateway recursively; reserved for a future Phase 10 `generate_simulation_turn` boundary. |
| Video request helper | `backend/services/video_service.py` | Constructs `GovernedRequest`; canonical orchestrator. |
| Python SDK overlay | `sdk/UKG_Python_SDK/ukg_sdk/overlay.py` | Thin HTTP client to `/api/v1/gateway/chat`; no local orchestration. |
| Python SDK TruthEngine/API | `sdk/UKG_Python_SDK/ukg_sdk/truth_engine/` | Thin service clients; no duplicate TruthCore execution. |
| SDK workflow helper | `sdk/UKG_Python_SDK/ukg_sdk/workflow.py` | Local planning preview only; it does not claim or produce a governed answer. |

## Explicit non-answer surfaces

- Provider connection tests are control-plane diagnostics and do not create a
  governed answer.
- DSQP profile endpoints are diagnostics/configuration surfaces, not an answer
  path.
- Direct individual KA execution is an explicit algorithm tool contract, not a
  governed LLM-answer facade. Phase 6 owns the validity of KA evidence/output.
- Graph, search, ingestion, trace export, backup, and administrative APIs do not
  produce governed model answers.

## Residual boundaries

- Simulation behavior is intentionally unavailable until Phase 10 and is not
  counted as completed functionality.
- Native token-by-token provider streaming and async job productization remain
  later gateway work; they must reuse this contract rather than create a second
  orchestrator.

