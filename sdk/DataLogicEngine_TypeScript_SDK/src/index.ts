import type {
  KAExecutionEnvelope,
  KAExecutionRequest,
  KAListResponse,
  KAProductPlanEnvelope,
  KAProductPlanRequest,
  KAProductResultEnvelope,
  KAProductRunEnvelope,
  KAProductRunListEnvelope,
} from "./ka-types.js";
import {
  KA_RUNTIME_MANIFEST,
  KA_RUNTIME_MANIFEST_SHA256,
} from "./ka-manifest.generated.js";

export { KA_RUNTIME_MANIFEST, KA_RUNTIME_MANIFEST_SHA256 };
export type * from "./ka-types.js";

export const GATEWAY_CONTRACT_VERSION = "dle-gateway.v1" as const;

export type GatewayMessage = {
  role: "user" | "assistant" | "system";
  content: string | Array<Record<string, unknown>>;
};

export type VirtualModel =
  | "dle-standard"
  | "dle-enhanced"
  | "dle-local-review";

export type GatewayChatOptions = {
  virtualModel?: VirtualModel;
  requestId?: string;
  idempotencyKey?: string;
  sessionId?: string;
  constraints?: Record<string, unknown>;
  maxTokens?: number;
  meta?: Record<string, unknown>;
  signal?: AbortSignal;
};

export type GatewayResult = {
  request_id: string;
  response: string;
  run_id: string | null;
  provider_used: string | null;
  model_used: string | null;
  virtual_model: VirtualModel;
  gateway_contract_version: typeof GATEWAY_CONTRACT_VERSION;
  contract_version: string;
  status: string;
  usage: Record<string, unknown>;
  confidence_score: number | null;
  citations: Array<Record<string, unknown>>;
  [key: string]: unknown;
};

export type GatewayCapabilities = {
  contract_version: typeof GATEWAY_CONTRACT_VERSION;
  profile: "desktop_loopback" | "same_host_gateway";
  virtual_models: Record<string, Record<string, unknown>>;
  scopes: string[];
  provider_credentials_exposed: false;
};

export type KAManifestIntegrity = {
  manifest_version: string | null;
  sha256: string | null;
  source: string | null;
  capability_count: number | null;
};

export type KAManifestParity = {
  matches: boolean;
  mismatches: Array<"manifest_version" | "sha256" | "capability_count">;
  server: KAManifestIntegrity;
  client: {
    manifest_version: string;
    sha256: string;
    capability_count: number;
  };
};

export type GatewayJob = {
  job_id: string;
  request_id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancelled" | "expired";
  virtual_model: VirtualModel;
  run_id: string | null;
  response_status: number | null;
  error_code: string | null;
  error_message: string | null;
  result_storage: "postgresql_ciphertext" | "minio_ciphertext";
  result_size_bytes: number | null;
  gateway_contract_version: typeof GATEWAY_CONTRACT_VERSION;
  status_url: string;
  result_url: string;
  cancel_url: string;
  [key: string]: unknown;
};

export class DataLogicEngineError extends Error {
  readonly status: number;
  readonly code: string | undefined;
  readonly details: unknown;
  readonly retryAfterSeconds: number | undefined;

  constructor(
    message: string,
    options: {
      status: number;
      code?: string;
      details?: unknown;
      retryAfterSeconds?: number;
    },
  ) {
    super(message);
    this.name = "DataLogicEngineError";
    this.status = options.status;
    this.code = options.code;
    this.details = options.details;
    this.retryAfterSeconds = options.retryAfterSeconds;
  }
}

export type DataLogicEngineClientOptions = {
  baseUrl?: string;
  apiKey: string;
  fetch?: typeof globalThis.fetch;
  maxAttempts?: number;
  retryDelayMs?: number;
};

function requiredId(value: string | undefined): string {
  return value ?? globalThis.crypto.randomUUID();
}

function responseMessage(body: unknown): { message: string; code?: string } {
  if (!body || typeof body !== "object") return { message: "Gateway request failed" };
  const record = body as Record<string, unknown>;
  const rawError = record.error;
  if (rawError && typeof rawError === "object") {
    const error = rawError as Record<string, unknown>;
    const code = String(error.code ?? record.code ?? "");
    return {
      message: String(error.message ?? error.code ?? "Gateway request failed"),
      ...(code ? { code } : {}),
    };
  }
  const code = String(record.code ?? "");
  return {
    message: String(record.message ?? rawError ?? "Gateway request failed"),
    ...(code ? { code } : {}),
  };
}

export class DataLogicEngineClient {
  readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly fetchImpl: typeof globalThis.fetch;
  private readonly maxAttempts: number;
  private readonly retryDelayMs: number;

  constructor(options: DataLogicEngineClientOptions) {
    if (!options.apiKey?.trim()) throw new TypeError("apiKey is required");
    this.baseUrl = (options.baseUrl ?? "http://127.0.0.1:5000/api/v1").replace(/\/$/, "");
    this.apiKey = options.apiKey;
    this.fetchImpl = options.fetch ?? globalThis.fetch.bind(globalThis);
    this.maxAttempts = Math.max(1, Math.min(5, options.maxAttempts ?? 3));
    this.retryDelayMs = Math.max(0, options.retryDelayMs ?? 250);
  }

  private headers(accept = "application/json"): HeadersInit {
    return {
      Accept: accept,
      Authorization: `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
      "User-Agent": "datalogicengine-typescript/0.1.0",
      "X-API-Version": GATEWAY_CONTRACT_VERSION,
    };
  }

  private async raiseForError(response: Response): Promise<never> {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = await response.text();
    }
    const normalized = responseMessage(body);
    const retryAfter = Number(response.headers.get("Retry-After"));
    throw new DataLogicEngineError(normalized.message, {
      status: response.status,
      ...(normalized.code ? { code: normalized.code } : {}),
      details: body,
      ...(Number.isFinite(retryAfter) ? { retryAfterSeconds: retryAfter } : {}),
    });
  }

  private async request(
    method: "GET" | "POST",
    path: string,
    body?: Record<string, unknown>,
    signal?: AbortSignal,
  ): Promise<Record<string, unknown>> {
    const isRetrySafe = method === "GET" || Boolean(body?.idempotency_key);
    const attempts = isRetrySafe ? this.maxAttempts : 1;
    let lastError: unknown;
    for (let attempt = 1; attempt <= attempts; attempt += 1) {
      try {
        const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
          method,
          headers: this.headers(),
          ...(body ? { body: JSON.stringify(body) } : {}),
          ...(signal ? { signal } : {}),
        });
        if (!response.ok) await this.raiseForError(response);
        return (await response.json()) as Record<string, unknown>;
      } catch (error) {
        if (error instanceof DataLogicEngineError || signal?.aborted) throw error;
        lastError = error;
        if (attempt < attempts) {
          await new Promise((resolve) => setTimeout(resolve, this.retryDelayMs * attempt));
        }
      }
    }
    throw new DataLogicEngineError("Gateway transport failed", {
      status: 0,
      details: lastError,
    });
  }

  private chatBody(messages: GatewayMessage[], options: GatewayChatOptions): Record<string, unknown> {
    if (messages.length === 0) throw new TypeError("messages are required");
    return {
      messages,
      virtual_model: options.virtualModel ?? "dle-standard",
      request_id: requiredId(options.requestId),
      idempotency_key: requiredId(options.idempotencyKey),
      ...(options.sessionId ? { session_id: options.sessionId } : {}),
      constraints: options.constraints ?? {},
      ...(options.maxTokens ? { max_tokens: options.maxTokens } : {}),
      meta: options.meta ?? {},
    };
  }

  async chat(messages: GatewayMessage[], options: GatewayChatOptions = {}): Promise<GatewayResult> {
    const payload = await this.request("POST", "/gateway/chat", this.chatBody(messages, options), options.signal);
    const data = (payload.data ?? payload) as GatewayResult;
    if (data.gateway_contract_version !== GATEWAY_CONTRACT_VERSION) {
      throw new DataLogicEngineError("Unsupported gateway contract version", {
        status: 0,
        details: data.gateway_contract_version,
      });
    }
    return data;
  }

  async capabilities(signal?: AbortSignal): Promise<GatewayCapabilities> {
    return (await this.request("GET", "/gateway/capabilities", undefined, signal)) as GatewayCapabilities;
  }

  async knowledgeAlgorithms(signal?: AbortSignal): Promise<KAListResponse> {
    return await this.request(
      "GET",
      "/ka/algorithms?per_page=300",
      undefined,
      signal,
    ) as KAListResponse;
  }

  async knowledgeAlgorithmManifest(
    signal?: AbortSignal,
  ): Promise<KAManifestIntegrity> {
    const payload = await this.request("GET", "/ka/manifest", undefined, signal);
    return (payload.data ?? payload) as KAManifestIntegrity;
  }

  async verifyKnowledgeAlgorithmManifest(
    signal?: AbortSignal,
  ): Promise<KAManifestParity> {
    const server = await this.knowledgeAlgorithmManifest(signal);
    const client = {
      manifest_version: KA_RUNTIME_MANIFEST.manifest_version,
      sha256: KA_RUNTIME_MANIFEST_SHA256,
      capability_count: KA_RUNTIME_MANIFEST.capability_count,
    };
    const mismatches: KAManifestParity["mismatches"] = [];
    if (server.manifest_version !== client.manifest_version) {
      mismatches.push("manifest_version");
    }
    if (server.sha256 !== client.sha256) mismatches.push("sha256");
    if (server.capability_count !== client.capability_count) {
      mismatches.push("capability_count");
    }
    return {
      matches: mismatches.length === 0,
      mismatches,
      server,
      client,
    };
  }

  async knowledgeAlgorithm(
    kaId: string,
    signal?: AbortSignal,
  ): Promise<Record<string, unknown>> {
    return this.request(
      "GET",
      `/ka/algorithms/${encodeURIComponent(kaId)}`,
      undefined,
      signal,
    );
  }

  async executeKnowledgeAlgorithm(
    kaId: string,
    execution: KAExecutionRequest,
    signal?: AbortSignal,
  ): Promise<KAExecutionEnvelope> {
    return await this.request(
      "POST",
      `/ka/algorithms/${encodeURIComponent(kaId)}/execute`,
      execution as unknown as Record<string, unknown>,
      signal,
    ) as KAExecutionEnvelope;
  }

  async planKnowledgeAlgorithm(
    kaId: string,
    plan: KAProductPlanRequest,
    signal?: AbortSignal,
  ): Promise<KAProductPlanEnvelope> {
    return await this.request(
      "POST",
      "/ka/runs/plan",
      {
        ka_id: kaId,
        input: plan.input,
        mode: plan.mode ?? "production",
        idempotency_key: requiredId(plan.idempotency_key),
        metadata: plan.metadata ?? {},
        budget: plan.budget ?? {},
        ...(plan.request_id ? { request_id: plan.request_id } : {}),
        ...(plan.session_id ? { session_id: plan.session_id } : {}),
        ...(plan.tier ? { tier: plan.tier } : {}),
        ...(plan.layer ? { layer: plan.layer } : {}),
        ...(plan.persona ? { persona: plan.persona } : {}),
      },
      signal,
    ) as KAProductPlanEnvelope;
  }

  async knowledgeAlgorithmRuns(
    limit = 50,
    signal?: AbortSignal,
  ): Promise<KAProductRunListEnvelope> {
    const bounded = Math.max(1, Math.min(200, Math.trunc(limit)));
    return await this.request(
      "GET",
      `/ka/runs?limit=${bounded}`,
      undefined,
      signal,
    ) as KAProductRunListEnvelope;
  }

  async knowledgeAlgorithmRun(
    runId: string,
    signal?: AbortSignal,
  ): Promise<KAProductRunEnvelope> {
    return await this.request(
      "GET",
      `/ka/runs/${encodeURIComponent(runId)}`,
      undefined,
      signal,
    ) as KAProductRunEnvelope;
  }

  async executeKnowledgeAlgorithmPlan(
    runId: string,
    confirmationToken?: string,
    signal?: AbortSignal,
  ): Promise<KAProductRunEnvelope> {
    return await this.request(
      "POST",
      `/ka/runs/${encodeURIComponent(runId)}/execute`,
      confirmationToken
        ? { confirmation_token: confirmationToken }
        : {},
      signal,
    ) as KAProductRunEnvelope;
  }

  async cancelKnowledgeAlgorithmRun(
    runId: string,
    signal?: AbortSignal,
  ): Promise<KAProductRunEnvelope> {
    return await this.request(
      "POST",
      `/ka/runs/${encodeURIComponent(runId)}/cancel`,
      {},
      signal,
    ) as KAProductRunEnvelope;
  }

  async knowledgeAlgorithmRunResult(
    runId: string,
    signal?: AbortSignal,
  ): Promise<KAProductResultEnvelope> {
    return await this.request(
      "GET",
      `/ka/runs/${encodeURIComponent(runId)}/result`,
      undefined,
      signal,
    ) as KAProductResultEnvelope;
  }

  async knowledgeAlgorithmRunTrace(
    runId: string,
    signal?: AbortSignal,
  ): Promise<Record<string, unknown>> {
    return this.request(
      "GET",
      `/ka/runs/${encodeURIComponent(runId)}/trace`,
      undefined,
      signal,
    );
  }

  async knowledgeAlgorithmRunArtifacts(
    runId: string,
    signal?: AbortSignal,
  ): Promise<Record<string, unknown>> {
    return this.request(
      "GET",
      `/ka/runs/${encodeURIComponent(runId)}/artifacts`,
      undefined,
      signal,
    );
  }

  async knowledgeAlgorithmRunEffects(
    runId: string,
    signal?: AbortSignal,
  ): Promise<Record<string, unknown>> {
    return this.request(
      "GET",
      `/ka/runs/${encodeURIComponent(runId)}/effects`,
      undefined,
      signal,
    );
  }

  async cancel(requestId: string, signal?: AbortSignal): Promise<Record<string, unknown>> {
    return this.request("POST", `/gateway/requests/${encodeURIComponent(requestId)}/cancel`, undefined, signal);
  }

  async createRun(
    messages: GatewayMessage[],
    options: GatewayChatOptions = {},
  ): Promise<GatewayJob> {
    return await this.request(
      "POST",
      "/gateway/runs",
      this.chatBody(messages, options),
      options.signal,
    ) as GatewayJob;
  }

  async runs(limit = 50, signal?: AbortSignal): Promise<GatewayJob[]> {
    const bounded = Math.max(1, Math.min(200, Math.trunc(limit)));
    const payload = await this.request("GET", `/gateway/runs?limit=${bounded}`, undefined, signal);
    return (payload.jobs ?? []) as GatewayJob[];
  }

  async run(jobId: string, signal?: AbortSignal): Promise<GatewayJob> {
    return await this.request(
      "GET",
      `/gateway/runs/${encodeURIComponent(jobId)}`,
      undefined,
      signal,
    ) as GatewayJob;
  }

  async runResult(jobId: string, signal?: AbortSignal): Promise<Record<string, unknown>> {
    return this.request(
      "GET",
      `/gateway/runs/${encodeURIComponent(jobId)}/result`,
      undefined,
      signal,
    );
  }

  async cancelRun(jobId: string, signal?: AbortSignal): Promise<GatewayJob> {
    return await this.request(
      "POST",
      `/gateway/runs/${encodeURIComponent(jobId)}/cancel`,
      undefined,
      signal,
    ) as GatewayJob;
  }

  async trace(runId: string, signal?: AbortSignal): Promise<Record<string, unknown>> {
    return this.request(
      "GET",
      `/gateway/traces/${encodeURIComponent(runId)}`,
      undefined,
      signal,
    );
  }

  async *stream(
    messages: GatewayMessage[],
    options: Omit<GatewayChatOptions, "idempotencyKey"> = {},
  ): AsyncGenerator<Record<string, unknown>> {
    const body = this.chatBody(messages, options);
    delete body.idempotency_key;
    const response = await this.fetchImpl(`${this.baseUrl}/gateway/chat/stream`, {
      method: "POST",
      headers: this.headers("text/event-stream"),
      body: JSON.stringify(body),
      ...(options.signal ? { signal: options.signal } : {}),
    });
    if (!response.ok) await this.raiseForError(response);
    if (!response.body) throw new DataLogicEngineError("Gateway stream has no body", { status: 0 });

    const decoder = new TextDecoder();
    let buffer = "";
    for await (const chunk of response.body) {
      buffer += decoder.decode(chunk, { stream: true }).replace(/\r\n/g, "\n");
      let boundary = buffer.indexOf("\n\n");
      while (boundary >= 0) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const data = block
          .split("\n")
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trim())
          .join("\n");
        if (data) yield JSON.parse(data) as Record<string, unknown>;
        boundary = buffer.indexOf("\n\n");
      }
    }
  }
}
