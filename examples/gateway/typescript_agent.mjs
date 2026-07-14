import { DataLogicEngineClient } from "@datalogicengine/sdk";

const client = new DataLogicEngineClient({
  ...(process.env.DATALOGICENGINE_API_URL
    ? { baseUrl: process.env.DATALOGICENGINE_API_URL }
    : {}),
  apiKey: process.env.DATALOGICENGINE_API_KEY,
});

const result = await client.chat([
  { role: "user", content: "Review the supplied task against governed evidence." },
], {
  virtualModel: "dle-enhanced",
  meta: { client_kind: "agent" },
});

console.log({ response: result.response, runId: result.run_id });
