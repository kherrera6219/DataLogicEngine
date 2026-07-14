# Python SDK how-to

## Prerequisite

Run an installed or development DataLogicEngine backend and configure its model
providers through the application. The SDK does not accept custody of provider
credentials and does not execute KAs, DMRF, DSQP, retrieval, or TruthCore locally.

## Governed request

```python
import asyncio
from ukg_sdk import UKGOverlay


async def main():
    sdk = UKGOverlay(
        base_url="http://127.0.0.1:5000/api/v1",
        api_key="your-client-key",
    )
    result = await sdk.run(
        query="Review this policy against the retrieved controls.",
        mode="enhanced",
        session_id="optional-session-uuid",
        meta={"workspace": "policy-review"},
    )
    print(result["answer"])
    print(result["trace_id"])


asyncio.run(main())
```

Supported modes are `standard`, `enhanced`, `local_review`, and `simulation`.
Simulation currently returns the explicit Phase 10 capability boundary rather
than invoking the legacy simulation stack.

## General API client

```python
from ukg_sdk import UKGClient

with UKGClient(base_url="http://127.0.0.1:5000/api/v1") as client:
    sessions = client.sessions.list()
```

## Compatibility names

`TruthEngine`, `TruthEngineAPI`, and `WorkflowRunner.run_local_stub()` remain for
source compatibility. The first two call the installed governed endpoint. The
workflow helper only previews tier configuration and never produces a provider
answer.

Low-level provider modules remain package implementation adapters, but passing a
provider to `UKGOverlay` is ignored and recorded as a compatibility warning. New
code should configure providers in DataLogicEngine and pass only client policy
inputs such as requested mode/model where authorized.
