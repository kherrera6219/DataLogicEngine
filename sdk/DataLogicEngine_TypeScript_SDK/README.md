# DataLogicEngine TypeScript SDK

Thin TypeScript/JavaScript client for the installed `dle-gateway.v1` contract.
It never accepts provider credentials and never runs a second reasoning stack.

```ts
import { DataLogicEngineClient } from "@datalogicengine/sdk";

const client = new DataLogicEngineClient({
  apiKey: process.env.DATALOGICENGINE_API_KEY!,
});

const result = await client.chat([
  { role: "user", content: "Summarize the approved evidence." },
]);

console.log(result.response, result.run_id);
```

Synchronous chat retries are protected by an automatically generated
idempotency key. `client.stream()` exposes live governed stage events and
validation-gated answer chunks without claiming raw provider-token delivery.
The client also supports `capabilities()`, durable `createRun()`/`run()`/
`runResult()`/`cancelRun()`, active-request `cancel()`, and client-owned
`trace()` reads. Private-network use remains an installed qualification gate.

See `docs/GATEWAY_COMPATIBILITY.md` and `examples/gateway/` in the main
repository for the exact v1 matrix and runnable patterns.
