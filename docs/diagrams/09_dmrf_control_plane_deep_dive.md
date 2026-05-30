# DMRF Control Plane Deep Dive

## Purpose

This diagram maps the DMRF control plane as implemented in code. DMRF is the orchestration layer that connects injection defense, TruthGate, tier classification, 17-axis routing, DSQP persona construction, TruthCore workflow planning, evidence freshness scoring, convergence/refinement policy, TruthMemory persistence, MLflow-style tracking, TruthLink publishing, FROST snapshots, and observability.

This is one of the core architectural maps for DataLogicEngine because it shows the actual runtime brain that coordinates the platform's research concepts.

## Primary Code Paths

- `backend/dmrf/orchestrator.py`
- `backend/dmrf/models.py`
- `backend/dmrf/injection_defense.py`
- `backend/dmrf/tier_classifier.py`
- `backend/dmrf/router.py`
- `backend/dmrf/evidence_model.py`
- `backend/dmrf/convergence_policy.py`
- `backend/dmrf/frost_bridge.py`
- `backend/dmrf/mlflow_tracker.py`
- `backend/dmrf/observability.py`
- `backend/dmrf/truth_integration/`
- `backend/dsqp/dsqp_orchestrator.py`

## Mermaid Architecture Diagram

```mermaid
flowchart TD
    Query[Query + Context + Offline Flag]
    Orchestrator[DMRFOrchestrator\nbackend/dmrf/orchestrator.py]
    Result[DMRFResult\nrun_id + ok + tier + axis_vector + steps + dsqp_chain + gate_result + convergence + warnings]

    Query --> Orchestrator
    Orchestrator --> Result

    subgraph MODELS[DMRF Data Models]
        AxisVector[AxisVector\naxes + confidence + active_axes + frost_layer_depth + truth_engine_mode]
        TierClassification[TierClassification\ntier + confidence + rationale + raw + capped_from]
        Step[DMRFStep\nname + status + outputs + snapshot_id + timestamps]
        Bundle[Export Bundle\nquery_digest + steps + gate + convergence + warnings]
    end

    Result --> AxisVector
    Result --> TierClassification
    Result --> Step
    Result --> Bundle

    subgraph PIPE[Control Plane Pipeline]
        Injection[1 InjectionDefense\ndetect prompt injection, traps, obfuscation, persona hijack, resource exhaustion]
        Gate[2 TruthGate Adapter\nTruthGateGateway.evaluate]
        Classifier[3 TierClassifier\ntrivial/moderate/high_stakes/extreme/autonomous]
        Router[4 DMRFRouter\n17-axis AxisVector]
        DSQP[5 DSQPOrchestrator\npersona axes 8-11]
        CorePlan[6 TruthCore Adapter\nworkflow_steps(tier, axis17)]
        Evidence[7 EvidenceModel\nfreshness score + stale flag]
        Convergence[8 ConvergencePolicy\nshould_refine + adjusted confidence]
        Memory[9 TruthMemory Adapter\noptional DB-backed persistence]
        MLflow[10 DMRFMLflowTracker\ntracking record]
        Link[11 TruthLink Adapter\npublish completion/export bundle]
        Observability[12 DMRFObservability\ntier counters + FROST depth]
    end

    Orchestrator --> Injection
    Injection -->|safe| Gate
    Injection -->|blocked| Result
    Gate -->|passed| Classifier
    Gate -->|blocked| Result
    Classifier --> Router
    Router --> DSQP
    DSQP --> CorePlan
    CorePlan --> Evidence
    Evidence --> Convergence
    Convergence --> Memory
    Memory --> MLflow
    MLflow --> Link
    Link --> Observability
    Observability --> Result

    subgraph SNAP[FROST Step Snapshots]
        FrostBridge[FROSTBridge\nsnapshot_step]
        FrostService[FROSTService\nsnapshot + verify_snapshot]
        Snapshot[Per-Step Snapshot ID\nverified or snapshot_failed warning]
    end

    Injection -. record_step .-> FrostBridge
    Gate -. record_step .-> FrostBridge
    Classifier -. record_step .-> FrostBridge
    Router -. record_step .-> FrostBridge
    DSQP -. record_step .-> FrostBridge
    CorePlan -. record_step .-> FrostBridge
    Evidence -. record_step .-> FrostBridge
    Convergence -. record_step .-> FrostBridge
    MLflow -. record_step .-> FrostBridge
    Link -. record_step .-> FrostBridge
    FrostBridge --> FrostService
    FrostService --> Snapshot
    Snapshot --> Step

    subgraph TRUTH[Truth Engine Integration]
        GateAdapter[gate_adapter.py]
        CoreAdapter[core_adapter.py]
        MemoryAdapter[memory_adapter.py]
        LinkAdapter[link_adapter.py]
        TruthGate[TruthGateGateway]
        TruthCore[TruthCoreEngine]
        TruthMemory[TruthMemoryManager]
        TruthLink[TruthLinkBus]
    end

    Gate --> GateAdapter --> TruthGate
    CorePlan --> CoreAdapter --> TruthCore
    Memory --> MemoryAdapter --> TruthMemory
    Link --> LinkAdapter --> TruthLink

    subgraph GOV[Governance Logic]
        Risk[Axis 15 Risk Domain]
        Axis17[Axis 17 FROST Mode]
        Target[Target Confidence\n0.95 normal / 0.995 high-stakes+]
        OfflineCap[Desktop Offline Cap\nno tier above high_stakes]
    end

    Router --> Risk
    Router --> Axis17
    Classifier --> OfflineCap
    Convergence --> Target
```

## Runtime Execution Order

The actual `DMRFOrchestrator.process()` order is:

```text
1. Create DMRFResult
2. InjectionDefense.detect(query)
3. record_step("injection_defense")
4. If unsafe: ok=false, warning=blocked:<category>, return
5. TruthGateDMRFAdapter.evaluate(query, context)
6. record_step("truth_gate")
7. If blocked: ok=false, warning=<block_reason>, return
8. DMRFTierClassifier.classify(query, context, offline)
9. record_step("tier_classifier")
10. DMRFRouter.route(query, tier, context)
11. record_step("axis_router")
12. DSQPOrchestrator.construct_all_sync(query, axis_vector, context)
13. record_step("dsqp_personas")
14. TruthCoreDMRFAdapter.workflow_steps(tier, axis17)
15. record_step("truth_core_plan")
16. EvidenceModel(axis15 risk domain).score(observed_at)
17. ConvergencePolicy(axis15 risk domain).should_refine(...)
18. record_step("convergence_policy")
19. If db_session: TruthMemoryDMRFAdapter.persist(...)
20. DMRFMLflowTracker.record(result)
21. record_step("mlflow_tracking")
22. TruthLinkDMRFAdapter.publish("completed", result.export_bundle())
23. record_step("truthlink_publish")
24. DMRFObservability.record(tier, frost_depth, run_id)
25. Return DMRFResult
```

## Key DMRF Models

| Model | Code | Purpose |
|---|---|---|
| `AxisVector` | `backend/dmrf/models.py` | Serializable 17-axis routing vector with confidence, active axes, FROST layer depth, and Truth Engine mode. |
| `TierClassification` | `backend/dmrf/models.py` | Classification result with tier, confidence, rationale, raw metadata, and optional offline cap source. |
| `DMRFStep` | `backend/dmrf/models.py` | One telemetry record for a control-plane step, including outputs, snapshot ID, and timestamps. |
| `DMRFResult` | `backend/dmrf/models.py` | Top-level result containing query, run ID, status, tier, axis vector, steps, DSQP chain, gate result, convergence, warnings, and export bundle. |

## Fail-Fast Behavior

DMRF contains two early exit gates:

1. **InjectionDefense** — blocks prompt injection, logical traps, obfuscated payloads, persona hijack, and resource-exhaustion patterns.
2. **TruthGate** — blocks requests based on adversarial input, budget limits, and trust/compliance checks.

If either fails, DMRF returns a structured `DMRFResult` with `ok=false` and warnings instead of continuing into deeper reasoning.

## FROST Snapshot Behavior

Every DMRF step is recorded through `_record_step()`. That method:

1. creates a `DMRFStep`;
2. sends step state to `FROSTBridge.snapshot_step()`;
3. receives a `snapshot_id` and verification result;
4. marks the step `snapshot_failed` if verification fails;
5. appends a warning to the result if needed;
6. completes and stores the step.

This means DMRF produces an auditable step sequence rather than only a final answer.

## Risk, Evidence, and Convergence

DMRF uses Axis 15 risk context to configure evidence and convergence:

```text
Axis 15 risk domain
        ↓
EvidenceModel(domain).score(observed_at)
        ↓
ConvergencePolicy(domain).should_refine(
    confidence=axis_vector.confidence,
    target_confidence=0.995 for high_stakes/extreme/autonomous else 0.95,
    iteration=0,
    evidence_age_days=evidence.age_days
)
```

This makes evidence freshness part of the refinement decision rather than a passive metadata field.

## DSQP Integration

DMRF feeds DSQP with:

```text
query
axis_vector
risk_domain = axis_vector.axes["15"]["value"]
coordinate_path = dmrf.<axis1 value>.<axis2 value>
```

DSQP then constructs persona outputs for axes 8-11 and returns:

```text
profiles
failures
partial
timeout_seconds
```

That result is stored in `DMRFResult.dsqp_chain`.

## Observability Surface

`DMRFObservability` tracks:

- tier counts;
- last run status;
- last tier;
- last FROST depth;
- last run ID;
- Prometheus lines for tier counts and FROST depth.

This gives DMRF a lightweight operational status surface for APIs, desktop IPC, and metrics endpoints.

## Judge Review Path

A technical judge should inspect these files in order:

1. `backend/dmrf/orchestrator.py` — confirms the full execution order and integration points.
2. `backend/dmrf/models.py` — confirms result, step, tier, axis, and export bundle structures.
3. `backend/dmrf/injection_defense.py` — confirms fail-fast prompt/injection screening.
4. `backend/dmrf/tier_classifier.py` — confirms five-tier risk classification and desktop offline cap behavior.
5. `backend/dmrf/router.py` — confirms 17-axis runtime vector generation.
6. `backend/dsqp/dsqp_orchestrator.py` — confirms persona construction for axes 8-11.
7. `backend/dmrf/evidence_model.py` and `backend/dmrf/convergence_policy.py` — confirms evidence freshness and refinement policy.
8. `backend/dmrf/frost_bridge.py` — confirms per-step FROST snapshots and verification.
9. `backend/dmrf/truth_integration/` — confirms TruthGate, TruthCore, TruthMemory, and TruthLink integration.
10. `backend/dmrf/observability.py` — confirms DMRF metrics and status output.

## Interpretation

DMRF is the operational control plane that turns the DataLogicEngine research architecture into executable AI governance. It binds policy, risk tiering, coordinate routing, expert persona construction, Truth Engine workflow selection, evidence scoring, refinement decisions, trace snapshots, persistence, event publication, and metrics.

For contest judges, DMRF is one of the clearest places to see why this project is more than a model wrapper.
