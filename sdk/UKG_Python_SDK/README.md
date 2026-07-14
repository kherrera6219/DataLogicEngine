# DataLogicEngine Python SDK — v0.7.0

This package contains thin clients for an installed DataLogicEngine service.
The backend owns admission policy, DMRF routing, deterministic DSQP context,
TruthCore/KA execution, retrieval, provider calls, validation, persistence, and
the authoritative trace.

The supported public entry points are:

- `UKGClient` and `UKGAsyncClient` for the versioned HTTP API;
- `UKGOverlay` as an asynchronous compatibility facade over
  `POST /api/v1/gateway/chat`;
- coordinate and optional DSQP data helpers that do not execute a governed
  request.

`UKGClient.gateway` and `UKGAsyncClient.gateway` implement the supported
`dle-gateway.v1` client contract: sync chat, live governed SSE, durable job
create/status/result/cancel, active-request cancellation, capability discovery,
client-owned trace reads, idempotency, typed errors, and bounded retry.

Client-side provider and TruthEngine orchestration were removed in v0.6. Direct
imports of `TruthEngine` and `TruthEngineAPI` remain as service-client shims.

## Install

```bash
pip install -e .
```

## Quick start

Start and configure DataLogicEngine first. Provider credentials belong to the
installed service, not the SDK process.

```python
import asyncio
import os

from ukg_sdk import UKGOverlay


async def main():
    client = UKGOverlay(
        base_url=os.getenv(
            "DATALOGICENGINE_API_URL",
            "http://127.0.0.1:5000/api/v1",
        ),
        api_key=os.getenv("DATALOGICENGINE_API_KEY"),
    )
    result = await client.run(
        query="Explain the governed request lifecycle.",
        mode="standard",
        meta={"source": "python_example"},
    )
    print(result["answer"])
    print(result["trace_id"], result["status"])


asyncio.run(main())
```

`confidence` is `None` until a versioned evidence-confidence formula is
implemented. The validation stage remains available in the authoritative trace.

See `docs/API_REFERENCE.md` and `docs/HOWTO.md`.
