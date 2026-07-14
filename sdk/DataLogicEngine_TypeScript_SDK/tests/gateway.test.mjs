import assert from "node:assert/strict";
import test from "node:test";

import {
  DataLogicEngineClient,
  DataLogicEngineError,
  GATEWAY_CONTRACT_VERSION,
} from "../dist/index.js";

const result = {
  request_id: "request-123",
  response: "governed answer",
  run_id: "run-123",
  provider_used: "openai",
  model_used: "gpt-5.5",
  virtual_model: "dle-standard",
  gateway_contract_version: GATEWAY_CONTRACT_VERSION,
  contract_version: "governed.v1",
  status: "completed",
  usage: {},
  confidence_score: null,
  citations: [],
};

const job = {
  job_id: "job-123",
  request_id: "request-123",
  status: "queued",
  virtual_model: "dle-standard",
  run_id: null,
  response_status: null,
  error_code: null,
  error_message: null,
  gateway_contract_version: GATEWAY_CONTRACT_VERSION,
  status_url: "/api/v1/gateway/runs/job-123",
  result_url: "/api/v1/gateway/runs/job-123/result",
  cancel_url: "/api/v1/gateway/runs/job-123/cancel",
};

test("chat is automatically idempotent and returns the governed contract", async () => {
  const seen = [];
  const client = new DataLogicEngineClient({
    apiKey: "ukg_test",
    fetch: async (_url, init) => {
      seen.push(JSON.parse(init.body));
      return Response.json({ success: true, data: result });
    },
  });
  const response = await client.chat([{ role: "user", content: "hello" }]);
  assert.equal(response.response, "governed answer");
  assert.equal(seen[0].virtual_model, "dle-standard");
  assert.ok(seen[0].idempotency_key.length >= 8);
});

test("only idempotent writes retry", async () => {
  let calls = 0;
  const client = new DataLogicEngineClient({
    apiKey: "ukg_test",
    retryDelayMs: 0,
    maxAttempts: 2,
    fetch: async () => {
      calls += 1;
      if (calls === 1) throw new TypeError("temporary network failure");
      return Response.json({ data: result });
    },
  });
  await client.chat([{ role: "user", content: "hello" }]);
  assert.equal(calls, 2);
});

test("typed errors preserve status, code, and retry state", async () => {
  const client = new DataLogicEngineClient({
    apiKey: "ukg_test",
    fetch: async () => Response.json(
      { error: "limited", code: "CLIENT_RATE_LIMITED" },
      { status: 429, headers: { "Retry-After": "17" } },
    ),
  });
  await assert.rejects(
    client.chat([{ role: "user", content: "hello" }]),
    (error) => {
      assert.ok(error instanceof DataLogicEngineError);
      assert.equal(error.status, 429);
      assert.equal(error.code, "CLIENT_RATE_LIMITED");
      assert.equal(error.retryAfterSeconds, 17);
      return true;
    },
  );
});

test("buffered SSE is parsed and omits unsupported idempotency", async () => {
  const seen = [];
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode('data: {"type":"stage"}\n\n'));
      controller.enqueue(new TextEncoder().encode('data: {"type":"done"}\n\n'));
      controller.close();
    },
  });
  const client = new DataLogicEngineClient({
    apiKey: "ukg_test",
    fetch: async (_url, init) => {
      seen.push(JSON.parse(init.body));
      return new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
    },
  });
  const events = [];
  for await (const event of client.stream([{ role: "user", content: "hello" }])) {
    events.push(event);
  }
  assert.deepEqual(events.map((event) => event.type), ["stage", "done"]);
  assert.equal("idempotency_key" in seen[0], false);
});

test("durable run methods preserve typed job state and idempotency", async () => {
  const seen = [];
  const client = new DataLogicEngineClient({
    apiKey: "ukg_test",
    fetch: async (url, init) => {
      const path = String(url);
      seen.push({ path, init });
      if (path.endsWith("/result")) return Response.json({ response: "job result" });
      if (path.endsWith("/cancel")) return Response.json({ ...job, status: "cancelled" }, { status: 202 });
      if (path.includes("?limit=")) return Response.json({ jobs: [job] });
      if (init.method === "GET") return Response.json({ ...job, status: "running" });
      return Response.json(job, { status: 202 });
    },
  });
  const created = await client.createRun([{ role: "user", content: "hello" }]);
  const listed = await client.runs();
  const status = await client.run(created.job_id);
  const response = await client.runResult(created.job_id);
  const cancelled = await client.cancelRun(created.job_id);
  assert.equal(created.status, "queued");
  assert.equal(listed[0].job_id, "job-123");
  assert.equal(status.status, "running");
  assert.equal(response.response, "job result");
  assert.equal(cancelled.status, "cancelled");
  const createBody = JSON.parse(seen[0].init.body);
  assert.ok(createBody.idempotency_key.length >= 8);
});
