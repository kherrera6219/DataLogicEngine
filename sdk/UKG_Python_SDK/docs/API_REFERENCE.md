# Python SDK API reference — v0.6

## `UKGOverlay`

Asynchronous compatibility client for `POST /api/v1/gateway/chat`.

```python
UKGOverlay(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout_s: float = 120.0,
    verify_tls: bool = True,
)

await overlay.run(
    *,
    query: str,
    user_id: str = "anonymous",
    session_id: str | None = None,
    correlation_id: str | None = None,
    meta: dict | None = None,
    temperature: float = 0.2,
    max_tokens: int = 1024,
    tier_override: str | None = None,
    mode: str = "standard",
    provider: str | None = None,
    model: str | None = None,
) -> dict
```

The result includes `answer`, `trace_id`, `contract_version`, `status`, measured
usage, evidence/claim summary fields, warnings, and nullable `confidence`.

## `UKGClient` / `UKGAsyncClient`

General synchronous and asynchronous HTTP clients. Both accept `base_url`,
`api_key`, `timeout`, retry count, and retry delay. Subclients expose sessions,
runs, exports, and compliance resources.

## `TruthEngine` / `TruthEngineAPI`

Deprecated names retained as thin synchronous clients to the governed gateway.
Supplying legacy TruthGate, memory, KA executor, or registry components raises a
clear migration error; these classes cannot create a second execution pipeline.

## `WorkflowRunner`

Loads the bundled workflow metadata, selects a tier deterministically, and can
return a planning preview. It does not execute an answer.

## Data helpers

`CoordinateResolver17`, `Coordinate17`, and the optional `DSQPClient` are local
data/client helpers. Their output is not an authoritative governed result unless
it is submitted to and recorded by the installed backend.
