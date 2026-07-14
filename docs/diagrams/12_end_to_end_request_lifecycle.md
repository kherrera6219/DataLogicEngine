# End-to-End Governed Request Lifecycle

> **Document metadata**
> - Document version: v2.0.0
> - Last reviewed: 2026-07-13
> - Status: Active architecture review map
> - Owner: Platform Architecture
> - Contract: `governed.v1`

## Purpose

This is the reviewer-facing walkthrough for the Phase 5 canonical request path.
It shows the one backend-owned causal lifecycle used by built-in chat and
approved answer clients, the exact trace boundary, and the capabilities that are
deliberately deferred.

A governed request is not prompt to model to answer. It is an authenticated,
policy-controlled, source-aware, bounded execution that returns an explicit
result or failure with one stable trace ID.

## Primary code paths

- `backend/governed_execution/contracts.py`
- `backend/governed_execution/orchestrator.py`
- `backend/governed_execution/retrieval.py`
- `backend/governed_execution/prompt.py`
- `backend/governed_execution/validation.py`
- `backend/governed_execution/trace_persistence.py`
- `backend/llm_gateway/gateway.py`
- `backend/llm_gateway/api.py`
- `frontend/components/Chat/LiveTracePanel.tsx`
- `frontend/lib/api/types.ts`

## Canonical lifecycle

```mermaid
flowchart TD
    U["Owner or approved client"] --> T["Authenticated API or built-in chat transport"]
    T --> R["GovernedRequest governed.v1"]
    R --> A["Admission, recursion guard, cancellation, mode check"]
    A --> SIM{"Simulation mode?"}
    SIM -- Yes --> SB["Phase 10 capability-unavailable stage"]
    SIM -- No --> D["DMRF injection defense, TruthGate, tier, 17-axis route"]
    D --> ALLOW{"Policy allows?"}
    ALLOW -- No --> BLOCK["Typed policy-block result"]
    ALLOW -- Yes --> RET["Bounded retrieval with stable source IDs"]
    RET --> DSQP["Deterministic DSQP axes 8-11 context"]
    DSQP --> TC["TruthCore workflow selection and required KA preflight"]
    TC --> MODE{"Local review?"}
    MODE -- Yes --> LOCAL["Local review without provider-answer claim"]
    MODE -- No --> PROMPT["One prompt with policy, evidence, personas, KAs, query"]
    PROMPT --> PROVIDER["Bounded provider execution"]
    PROVIDER --> VALIDATE["Output, claim, citation, and policy validation"]
    LOCAL --> VALIDATE
    VALIDATE --> STORE["Transactional run, stage, evidence, and claim persistence"]
    SB --> STORE
    BLOCK --> STORE
    STORE --> RESULT["GovernedResult or GovernedFailure plus stable trace_id"]
    RESULT --> UI["Chat status and Trace Explorer"]
```

## Success sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as Authenticated transport
    participant GOV as Governed orchestrator
    participant DMRF as DMRF and TruthGate
    participant RET as Retrieval
    participant CORE as DSQP, TruthCore, and KAs
    participant LLM as Provider boundary
    participant VAL as Validator
    participant DB as Transactional trace store
    participant UI as Client and Trace Explorer

    User->>API: Submit prompt
    API->>GOV: GovernedRequest(governed.v1) with server-owned principal
    GOV->>GOV: Admit and start stable trace_id
    GOV->>DMRF: Defense, gate, tier, axes
    DMRF-->>GOV: Allowed policy/routing record
    GOV->>RET: Retrieve bounded local context
    RET-->>GOV: Source-identified evidence
    GOV->>CORE: Deterministic personas, workflow, required KAs
    CORE-->>GOV: Exact executed inputs and outputs
    GOV->>LLM: One approved prompt
    LLM-->>GOV: Provider output and measured usage
    GOV->>VAL: Validate output, claims, citations, policy
    VAL-->>GOV: Validation record
    GOV->>DB: Persist exact run/stages/evidence/claims atomically
    DB-->>GOV: Stored
    GOV-->>API: GovernedResult
    API-->>UI: Status, answer, trace_id, sources, claims, nullable confidence
```

## Failure and cancellation rules

```mermaid
flowchart LR
    P["Policy block"] --> NP["No provider call"]
    PF["Provider failure"] --> NV["No completed validation stage"]
    C["Cancellation"] --> NC["No additional provider or tool calls"]
    I["Internal failure"] --> STOP["Stop later stages"]
    S["Simulation request"] --> B["Stop after admission at Phase 10 boundary"]
    NP --> TRACE["Persist only actual stages"]
    NV --> TRACE
    NC --> TRACE
    STOP --> TRACE
    B --> TRACE
    TRACE --> ID["Return one stable trace_id"]
```

Failure kinds are `policy_block`, `validation_failure`, `provider_failure`,
`cancelled`, `internal_failure`, and `capability_unavailable`. A policy or
capability decision is not relabeled as a network failure.

## Supported modes

| Mode | Phase 5 behavior |
|---|---|
| `standard` | Full bounded governed lifecycle with the standard required KA set. |
| `enhanced` | Full bounded lifecycle with the approved deeper KA preflight set. |
| `local_review` | Local retrieval/review path; it does not claim a provider answer. |
| `simulation` | Explicit Phase 10 capability-unavailable result immediately after admission. |

Compatibility values `chat`, `trace`, and `explain` map to `standard`; `quad`
maps to `enhanced`. `run_ukg_pipeline=false` is deprecated and cannot bypass
governance.

## Trace truth contract

Every admitted outcome uses one trace ID. Persistence records only work that
executed:

1. actual stage status, timestamps, and measured duration;
2. DMRF policy/tier/axis outputs;
3. accepted source-identified evidence;
4. DSQP contributions and KA inputs/outputs that influenced execution;
5. provider identity, model, usage, and failure metadata when called;
6. claims/citations and validation state when validation ran;
7. typed terminal failure when the run did not complete.

Planned stages, fixed durations, default routing confidence, and unexecuted KAs
are not inserted. Answer and claim confidence remain null when unmeasured.

## Phase boundary

Phase 5 proves causal execution, a single path, and trace truth. Phase 6 must
prove provenance, evidence sufficiency, claim support, contradiction handling,
category-specific validators, calibrated confidence, convergence, and KA
validity. The later rebuilt installed application must still complete real
OpenAI and Gemini runs with resolvable traces for CP5-E.
