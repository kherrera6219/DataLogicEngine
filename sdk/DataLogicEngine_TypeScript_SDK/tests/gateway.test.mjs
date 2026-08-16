import assert from "node:assert/strict";
import test from "node:test";

import {
  DataLogicEngineClient,
  DataLogicEngineError,
  GATEWAY_CONTRACT_VERSION,
  KA_RUNTIME_MANIFEST,
  KA_RUNTIME_MANIFEST_SHA256,
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

test("generated KA catalog is deduplicated and the client uses canonical routes", async () => {
  assert.equal(KA_RUNTIME_MANIFEST.capability_count, 213);
  assert.equal("KA-133" in KA_RUNTIME_MANIFEST.entries, false);
  assert.equal(
    KA_RUNTIME_MANIFEST.alias_index["generated-v1:KA-133"],
    "KA-1101",
  );

  const seen = [];
  const client = new DataLogicEngineClient({
    apiKey: "ukg_test",
    fetch: async (url, init) => {
      seen.push({ url: String(url), init });
      return Response.json({
        success: true,
        result: {
          algorithm_id: "KA-004",
          executed_at: "2026-07-25T00:00:00Z",
          status: "completed",
          output: { is_valid: true },
          log: "",
          execution_time_ms: 4,
        },
      });
    },
  });

  const response = await client.executeKnowledgeAlgorithm("KA-004", {
    input: { query: "validate" },
    mode: "production",
  });

  assert.equal(response.result.output.is_valid, true);
  assert.ok(seen[0].url.endsWith("/ka/algorithms/KA-004/execute"));
});

test("KA manifest parity compares the server with the generated client authority", async () => {
  const server = {
    manifest_version: KA_RUNTIME_MANIFEST.manifest_version,
    sha256: KA_RUNTIME_MANIFEST_SHA256,
    source: "ka_manifest.v1.generated.json",
    capability_count: KA_RUNTIME_MANIFEST.capability_count,
  };
  const client = new DataLogicEngineClient({
    apiKey: "ukg_test",
    fetch: async (url) => {
      assert.ok(String(url).endsWith("/ka/manifest"));
      return Response.json({ success: true, data: server });
    },
  });

  const matching = await client.verifyKnowledgeAlgorithmManifest();
  assert.equal(matching.matches, true);
  assert.deepEqual(matching.mismatches, []);

  const driftedClient = new DataLogicEngineClient({
    apiKey: "ukg_test",
    fetch: async () => Response.json({
      success: true,
      data: { ...server, sha256: "0".repeat(64), capability_count: 212 },
    }),
  });
  const drifted = await driftedClient.verifyKnowledgeAlgorithmManifest();
  assert.equal(drifted.matches, false);
  assert.deepEqual(drifted.mismatches, ["sha256", "capability_count"]);
});

test("KA client exposes durable plan, confirmation, history, and evidence routes", async () => {
  const seen = [];
  const run = {
    schema_version: "dle.ka-product-run.v1",
    run_id: "run-19j",
    request_id: "request-19j",
    canonical_id: "KA-004",
    manifest_version: "test",
    status: "planned",
    mode: "production",
    risk_tier: "destructive",
    confirmation_required: true,
    confirmed: false,
    cancellation_requested: false,
    result_size_bytes: null,
    error_code: null,
    error_message: null,
    created_at: "2026-07-25T00:00:00Z",
    updated_at: "2026-07-25T00:00:00Z",
    started_at: null,
    completed_at: null,
    expires_at: "2026-07-26T00:00:00Z",
    status_url: "/api/v1/ka/runs/run-19j",
    execute_url: "/api/v1/ka/runs/run-19j/execute",
    cancel_url: "/api/v1/ka/runs/run-19j/cancel",
    result_url: "/api/v1/ka/runs/run-19j/result",
    trace_url: "/api/v1/ka/runs/run-19j/trace",
    artifacts_url: "/api/v1/ka/runs/run-19j/artifacts",
    effects_url: "/api/v1/ka/runs/run-19j/effects",
  };
  const client = new DataLogicEngineClient({
    apiKey: "ukg_test",
    fetch: async (url, init) => {
      const value = String(url);
      seen.push({ url: value, init });
      if (value.endsWith("/ka/runs/plan")) {
        return Response.json({
          success: true,
          run,
          plan: {
            plan_id: "plan-19j",
            valid: true,
            selected_ids: ["KA-004"],
            execution_order: [["KA-004"]],
            risk: {
              tier: "destructive",
              confirmation_reasons: ["high_or_critical_risk"],
            },
          },
          confirmation_token: "confirm-19j",
        });
      }
      if (value.endsWith("/ka/runs?limit=200")) {
        return Response.json({ success: true, runs: [run] });
      }
      if (value.endsWith("/result")) {
        return Response.json({
          success: true,
          run: { ...run, status: "succeeded" },
          schema_version: "dle.ka-product-result.v1",
          run_id: "run-19j",
          report: {},
        });
      }
      if (value.endsWith("/trace")) {
        return Response.json({ success: true, trace: { run_id: "run-19j" } });
      }
      if (value.endsWith("/artifacts")) {
        return Response.json({ success: true, artifacts: [] });
      }
      if (value.endsWith("/effects")) {
        return Response.json({ success: true, effects: [] });
      }
      if (value.endsWith("/execute")) {
        return Response.json({ success: true, run: { ...run, status: "queued" } });
      }
      if (value.endsWith("/cancel")) {
        return Response.json({ success: true, run: { ...run, status: "cancelled" } });
      }
      return Response.json({ success: true, run });
    },
  });

  const planned = await client.planKnowledgeAlgorithm("KA-004", {
    input: { query: "validate" },
    idempotency_key: "cp19j-typescript-plan",
  });
  const queued = await client.executeKnowledgeAlgorithmPlan(
    planned.run.run_id,
    planned.confirmation_token ?? undefined,
  );
  const listed = await client.knowledgeAlgorithmRuns(999);
  const status = await client.knowledgeAlgorithmRun("run-19j");
  const result = await client.knowledgeAlgorithmRunResult("run-19j");
  const trace = await client.knowledgeAlgorithmRunTrace("run-19j");
  const artifacts = await client.knowledgeAlgorithmRunArtifacts("run-19j");
  const effects = await client.knowledgeAlgorithmRunEffects("run-19j");
  const cancelled = await client.cancelKnowledgeAlgorithmRun("run-19j");

  assert.equal(planned.plan.plan_id, "plan-19j");
  assert.equal(queued.run.status, "queued");
  assert.equal(listed.runs.length, 1);
  assert.equal(status.run.run_id, "run-19j");
  assert.equal(result.run.status, "succeeded");
  assert.equal(trace.trace.run_id, "run-19j");
  assert.deepEqual(artifacts.artifacts, []);
  assert.deepEqual(effects.effects, []);
  assert.equal(cancelled.run.status, "cancelled");
  const planBody = JSON.parse(seen[0].init.body);
  assert.equal(planBody.ka_id, "KA-004");
  assert.equal(planBody.idempotency_key, "cp19j-typescript-plan");
  assert.equal(planBody.input.query, "validate");
});
