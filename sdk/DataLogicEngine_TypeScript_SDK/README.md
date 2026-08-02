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

Knowledge Algorithms use a separate manifest-selected lifecycle. Review the
server plan before execution, pass the returned exact-plan token when
confirmation is required, then poll the principal-owned run:

```ts
const planned = await client.planKnowledgeAlgorithm("KA-004", {
  input: { query: "Validate this request." },
  idempotency_key: crypto.randomUUID(),
});

const queued = await client.executeKnowledgeAlgorithmPlan(
  planned.run.run_id,
  planned.confirmation_token ?? undefined,
);
const status = await client.knowledgeAlgorithmRun(queued.run.run_id);
const result = await client.knowledgeAlgorithmRunResult(status.run.run_id);
const trace = await client.knowledgeAlgorithmRunTrace(status.run.run_id);
```

The client also exposes `knowledgeAlgorithmRuns()`,
`cancelKnowledgeAlgorithmRun()`, `knowledgeAlgorithmRunArtifacts()`, and
`knowledgeAlgorithmRunEffects()`. The retained one-shot
`executeKnowledgeAlgorithm()` route is compatibility-only and rejects
high-risk or effect-oriented work that requires an exact reviewed plan.

See `docs/GATEWAY_COMPATIBILITY.md` and `examples/gateway/` in the main
repository for the exact v1 matrix and runnable patterns.
