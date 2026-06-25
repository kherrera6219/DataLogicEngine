# AI Reasoning Execution Sequence

## Purpose

This diagram maps the actual DataLogicEngine reasoning path from user query to governed result. It is grounded in the implementation modules that perform injection screening, TruthGate evaluation, risk tier classification, 17-axis routing, DSQP persona construction, TruthCore workflow planning, evidence freshness scoring, convergence/refinement decisions, memory persistence, MLflow tracking, TruthLink publishing, and observability.

This diagram is intended to help judges verify that DataLogicEngine does not simply pass a prompt to an LLM provider. It routes the query through a structured reasoning control plane before and after any model/provider interaction.

## Primary Code Path

The central implementation path is:

```text
backend/dmrf/orchestrator.py
```

Supporting modules inspected for this map:

- `backend/dmrf/injection_defense.py`
- `backend/dmrf/truth_integration/gate_adapter.py`
- `backend/dmrf/tier_classifier.py`
- `backend/dmrf/router.py`
- `backend/dsqp/dsqp_orchestrator.py`
- `backend/dsqp/dsqp_chain.py`
- `backend/dmrf/truth_integration/core_adapter.py`
- `backend/dmrf/evidence_model.py`
- `backend/dmrf/convergence_policy.py`
- `backend/dmrf/truth_integration/memory_adapter.py`
- `backend/dmrf/truth_integration/link_adapter.py`
- `backend/dmrf/mlflow_tracker.py`
- `backend/dmrf/observability.py`
- `backend/llm_gateway/`
- `backend/truth_engine/`

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    autonumber

    actor User as User / Judge / Operator
    participant FE as Frontend\nChat / Runs / Trace UI
    participant API as Flask API\n/api/v1/*
    participant DMRF as DMRFOrchestrator\nbackend/dmrf/orchestrator.py
    participant Inject as InjectionDefense\nbackend/dmrf/injection_defense.py
    participant TG as TruthGate Adapter\ntruth_integration/gate_adapter.py
    participant TGG as TruthGateGateway\nbackend/truth_engine/truth_gate/
    participant Tier as TierClassifier\nbackend/dmrf/tier_classifier.py
    participant Router as 17-Axis Router\nbackend/dmrf/router.py
    participant DSQP as DSQPOrchestrator\nbackend/dsqp/dsqp_orchestrator.py
    participant Chain as DSQPChain\nbackend/dsqp/dsqp_chain.py
    participant Core as TruthCore Adapter\ntruth_integration/core_adapter.py
    participant TCE as TruthCoreEngine\nbackend/truth_engine/truth_core/
    participant Evidence as EvidenceModel\nbackend/dmrf/evidence_model.py
    participant Conv as ConvergencePolicy\nbackend/dmrf/convergence_policy.py
    participant Gateway as LLM Gateway\nbackend/llm_gateway/
    participant Provider as Model Provider\nOpenAI / Anthropic / Azure / Gemini
    participant Memory as TruthMemory Adapter\ntruth_integration/memory_adapter.py
    participant Link as TruthLink Adapter\ntruth_integration/link_adapter.py
    participant Obs as DMRF Observability\nbackend/dmrf/observability.py
    participant Store as Data Stores\nSQL / Object / Trace / Audit

    User->>FE: Submit AI reasoning query
    FE->>API: POST request with query, context, auth/session/API key
    API->>API: Apply auth, CSRF/origin checks, middleware, rate limits, sanitization
    API->>DMRF: process(query, context, offline?)

    DMRF->>Inject: detect(query)
    Inject-->>DMRF: {safe, category, reasons}

    alt Injection defense blocks query
        DMRF-->>API: DMRFResult(ok=false, warning=blocked:category)
        API-->>FE: Safe failure response
        FE-->>User: Display blocked/recoverable result
    else Query passes injection defense
        DMRF->>TG: evaluate(query, context)
        TG->>TGG: evaluate({query, tenant_id, user_context, budget_limit})
        TGG-->>TG: gate_result
        TG-->>DMRF: gate_result

        alt TruthGate blocks query
            DMRF-->>API: DMRFResult(ok=false, warning=truth_gate_block)
            API-->>FE: Governed block response
            FE-->>User: Display policy/trust failure
        else TruthGate passes
            DMRF->>Tier: classify(query, context, offline)
            Tier-->>DMRF: tier, confidence, rationale, capped_from?

            DMRF->>Router: route(query, tier, context)
            Router-->>DMRF: AxisVector\naxes 1-17, confidence, FROST depth, Truth mode

            DMRF->>DSQP: construct_all_sync(query, axis_vector, context)
            DSQP->>Chain: construct persona for Axis 8 Knowledge Expert
            DSQP->>Chain: construct persona for Axis 9 Sector Expert
            DSQP->>Chain: construct persona for Axis 10 Regulatory Expert
            DSQP->>Chain: construct persona for Axis 11 Compliance Expert
            Chain-->>DSQP: ExpandedPersona objects + validation
            DSQP-->>DMRF: profiles, failures, partial flag, timeout_seconds

            DMRF->>Core: workflow_steps(tier, axis17_context)
            Core->>TCE: get_workflow_steps(tier, axis17_context)
            TCE-->>Core: workflow step list
            Core-->>DMRF: workflow_steps

            DMRF->>Evidence: score({observed_at})
            Evidence-->>DMRF: domain, age_days, decay_lambda, freshness_score, stale

            DMRF->>Conv: should_refine(confidence, target_confidence, iteration, evidence_age_days)
            Conv-->>DMRF: should_refine, adjusted_confidence, reason

            opt Provider-backed reasoning required by route/workflow
                DMRF->>Gateway: Governed provider request / gateway call
                Gateway->>Provider: Model API request
                Provider-->>Gateway: Model response
                Gateway-->>DMRF: Governed model result + usage/latency metadata
            end

            opt db_session available
                DMRF->>Memory: persist(result, truth_session_id)
                Memory->>Store: Write trace/audit/provenance state
                Store-->>Memory: Persist confirmation
                Memory-->>DMRF: persisted
            end

            DMRF->>Obs: record(tier, frost_depth, run_id)
            DMRF->>Link: publish("completed", result.export_bundle())
            Link->>Store: Publish/export bundle or event transport
            Store-->>Link: Publish confirmation
            Link-->>DMRF: link_result

            DMRF-->>API: DMRFResult\nsteps + axis vector + DSQP chain + workflow + convergence + warnings
            API-->>FE: Response with trace/run/audit metadata
            FE-->>User: Display answer, trace, stages, evidence, personas, export options
        end
    end
```

## Control-Plane Stages

| Stage | Code | What it does |
|---|---|---|
| 1. Request entry | `app.py`, route modules | Receives API request after auth, CSRF/origin checks, middleware, and rate limits. |
| 2. DMRF start | `backend/dmrf/orchestrator.py` | Creates a `DMRFResult`, records steps, and coordinates the reasoning pipeline. |
| 3. Injection defense | `backend/dmrf/injection_defense.py` | Blocks instruction override, logical trap, obfuscated payload, persona hijack, and resource exhaustion patterns. |
| 4. TruthGate | `backend/dmrf/truth_integration/gate_adapter.py`, `backend/truth_engine/truth_gate/` | Evaluates query against trust, tenant, user context, and budget controls before deeper reasoning. |
| 5. Tier classification | `backend/dmrf/tier_classifier.py` | Assigns `trivial`, `moderate`, `high_stakes`, `extreme`, or `autonomous` based on length, regulated terms, simulation terms, and autonomous-action terms. |
| 6. 17-axis routing | `backend/dmrf/router.py`, `core/axes/axis17_frost_mode.py` | Builds an `AxisVector` with axes 1-17, confidence, FROST layer depth, and Truth Engine mode. |
| 7. DSQP persona construction | `backend/dsqp/dsqp_orchestrator.py`, `backend/dsqp/dsqp_chain.py` | Builds deterministic offline personas for axes 8-11: knowledge, sector, regulatory, and compliance. |
| 8. TruthCore workflow planning | `backend/dmrf/truth_integration/core_adapter.py`, `backend/truth_engine/truth_core/` | Selects workflow steps based on risk tier and Axis 17 context. |
| 9. Evidence scoring | `backend/dmrf/evidence_model.py` | Scores evidence freshness using domain-specific decay lambdas. |
| 10. Convergence/refinement | `backend/dmrf/convergence_policy.py` | Decides whether more refinement is needed based on adjusted confidence, target confidence, iteration, and evidence age. |
| 11. Provider/gateway path | `backend/llm_gateway/` | Routes to configured LLM providers when the selected workflow requires model execution. |
| 12. Memory persistence | `backend/dmrf/truth_integration/memory_adapter.py`, `backend/truth_engine/truth_memory/` | Persists result, trace, provenance, and audit-related state when a database session is available. |
| 13. TruthLink publish | `backend/dmrf/truth_integration/link_adapter.py`, `backend/truth_engine/truth_link/` | Publishes completion/export bundle to the event/export layer. |
| 14. Observability | `backend/dmrf/observability.py`, `app.py` metrics | Records tier, FROST depth, run ID, and exposes Prometheus-style operational metrics. |
| 15. Frontend trace review | `frontend/app/runs/`, `frontend/components/Chat/`, `frontend/lib/api/trace.ts` | Displays reasoning output, trace stages, evidence, personas, claims, and export options. |

## Key Implementation Notes

### Injection defense is fail-fast

`InjectionDefense.detect()` classifies several prompt-risk categories before the query proceeds. If `safe` is false, the DMRF orchestrator returns an `ok=false` result immediately instead of passing the query deeper into the reasoning pipeline.

### TruthGate is the policy/trust entry gate

`TruthGateDMRFAdapter.evaluate()` wraps `TruthGateGateway.evaluate()` and passes the query with tenant, user context, and budget limit. This makes the DMRF path tenant-aware and policy-aware before routing and persona expansion.

### Tier classification changes the route

`DMRFTierClassifier.classify()` assigns risk tier based on query characteristics. Regulated or compliance terms raise the score into high-stakes territory, simulation terms raise it toward extreme, and autonomous-action terms raise it toward autonomous. Desktop offline mode can cap tiers above high-stakes.

### The 17-axis vector is explicit

`DMRFRouter.route()` constructs axes 1-17 and returns an `AxisVector` with aggregate confidence, active axes, FROST depth, and Truth Engine mode. Axes 8-11 are persona axes, Axis 15 is risk/threat context, Axis 16 is ethics/trust/criticality, and Axis 17 is resolved through the FROST axis.

### DSQP builds personas deterministically

`DSQPOrchestrator.construct_all_sync()` builds personas for active persona axes. `DSQPChain.construct()` creates seven-component persona outputs and marks construction mode as deterministic/offline. This allows the reasoning layer to use structured personas without requiring an LLM for persona generation.

### Evidence freshness influences convergence

`EvidenceModel.score()` computes freshness using a domain lambda. `ConvergencePolicy.should_refine()` adjusts confidence based on evidence age and decides whether refinement should continue.

### Persistence and publishing happen after reasoning

When a database session is available, DMRF attempts to persist through TruthMemory. It then records MLflow-style tracking, publishes through TruthLink, records observability, and returns the result bundle.

## Judge Review Notes

A technical judge should compare this diagram directly against `backend/dmrf/orchestrator.py`. The orchestrator contains the high-level sequence in executable form:

```text
InjectionDefense → TruthGate → TierClassifier → 17-Axis Router → DSQP → TruthCore → EvidenceModel → ConvergencePolicy → TruthMemory → MLflow → TruthLink → Observability
```

The most important point: the LLM gateway is not the entire architecture. The gateway is one possible execution branch inside a broader governed reasoning system.

## Related Diagrams

- `docs/diagrams/02_research_to_code_traceability.md`
- Future: `docs/diagrams/04_17_axis_coordinate_model.md`
- Future: `docs/diagrams/05_truth_engine_architecture.md`
