# UKG Python SDK — Developer API Reference (v0.5.0)

This is a **developer-facing** reference for integrating the UKG overlay into an LLM provider and your downstream app.

## Core Concepts

- **Overlay**: UKG wraps provider calls (OpenAI/Azure/Anthropic) and enforces routing, safety, evidence validation, TruthEngine checks, and audit trails.
- **FROST**: in-context, nested simulated database (10 tiers) used for *working memory* and simulation state. It is *not* a real DB.
- **UKG/USKD**: structured knowledge indexed by the 17-axis coordinate system. The SDK can persist selected artifacts to Postgres/Redis (optional) while keeping the main reasoning loop in-context.

## Main Entry Points

### `ukg_sdk.client.UKGClient`

Primary facade.

**Constructor**
```python
from ukg_sdk import UKGClient
from ukg_sdk.client import UKGClientConfig

client = UKGClient(
    config=UKGClientConfig(
        base_url="http://localhost:8080",  # or your hosted overlay
        timeout_s=60,
        max_retries=2,
    )
)
```

**Request**
```python
env = client.request(
    method="POST",
    path="/v1/ukg/answer",
    json_body={
        "query": "Explain X",
        "mode": "enterprise",
        "policy_profile": "default",
    },
)
print(env.data["answer"])
```

### Providers

- `ukg_sdk.providers.openai.OpenAIProvider`
- `ukg_sdk.providers.azure_openai.AzureOpenAIProvider`
- `ukg_sdk.providers.anthropic.AnthropicProvider`

Providers expose a unified async `complete()` interface and return a normalized `LLMResponse`.

### Coordinate Resolver

`ukg_sdk.coordinates17.CoordinateResolver17`

- `resolve(input_data) -> Coordinate`
- `Coordinate.as_compact_string() -> str`
- `Coordinate.to_dict() -> dict`

### Memory Adapters

- `ukg_sdk.memory.redis.RedisMemoryAdapter`
- `ukg_sdk.memory.postgres.PostgresMemoryAdapter`

Adapters implement:

- `get(key)`
- `set(key, value, ttl=None)`
- `append_audit(event)` (compliance-grade, append-only)

### KA Registry + Execution Map

- Registry: `ukg_sdk.ka.registry.KARegistry` (loads canonical JSON)
- Execution map: `ukg_sdk.ka.executor.KAExecutor`

`KAExecutor` binds `KA_ID -> callable` and returns normalized `KAExecutionResult` values.

## Error Model

All API surfaces raise `UKGError` subclasses:

- `UKGHttpError` (non-2xx)
- `UKGValidationError`
- `UKGPolicyError`
- `UKGProviderError`

## Artifacts & Audit

- Artifacts are written to the configured artifact store (`local`, `s3`, or `disabled`)
- Audit events are emitted for:
  - KA invocation
  - TruthEngine gates
  - memory read/write
  - provider call + token usage
  - policy veto

See `docs/specs/` and `ukg_sdk/data/` for canonical registries and workflow definitions.
