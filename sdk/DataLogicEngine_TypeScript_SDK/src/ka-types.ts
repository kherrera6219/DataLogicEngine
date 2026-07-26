export type KAExecutionMode = "production" | "evaluation" | "dry_run";

export type KAExecutionState =
  | "pending"
  | "admitted"
  | "running"
  | "succeeded"
  | "failed"
  | "blocked"
  | "cancelled"
  | "timed_out"
  | "unavailable";

export type KARuntimeEntrypoint = {
  adapter: "module_run" | "class_execute";
  module: string;
  callable: string;
  class_name?: string;
};

export type KARuntimeDefinition = {
  canonical_id: string;
  name: string;
  purpose: string | null;
  version: string;
  identity_class: string;
  aliases: { scoped: string[]; unscoped: [] };
  implementation: {
    status: string;
    source: string | null;
    entrypoint: KARuntimeEntrypoint | null;
  };
  contract: {
    version: "dle.ka-execution.v1";
    status: string;
    inputs: string[];
    outputs: string[];
    categories: string[];
    layers: string[];
    personas: string[];
    subsystems: string[];
    dependencies: string[];
    dependency_result_contract: "dle.ka-execution-result.v1#output";
    dependency_input_field: "dependency_results";
    triggers: string[];
    risk_classes: string[];
    effect_class: string;
    reads_memory: boolean;
    writes_memory: boolean;
    produces_artifacts: boolean;
    audit_events: boolean;
    limitations: string;
    guarantee: string;
    performance_budget_ms: number;
  };
  admission: {
    production_enabled: boolean;
    classification: string;
    deterministic: boolean | null;
    direct_execution: string;
  };
  integration: {
    authority_version: string;
    primary_owner: string;
    consumer_paths: string[];
    selector_policy: string;
    required_or_optional: string;
    stage: string;
    effect_port: string | null;
    effect_transaction: string;
    qualification: Record<string, string>;
  };
  migration_notes: string;
};

export type KARuntimeManifestCatalog = {
  schema_version: "dle.ka-runtime-manifest.v1";
  manifest_version: string;
  status: string;
  authority: Record<string, unknown>;
  capability_count: number;
  alias_index: Record<string, string>;
  entries: Record<string, KARuntimeDefinition>;
};

export type KAExecutionContext = {
  request_id?: string;
  run_id?: string;
  trace_id?: string;
  idempotency_key?: string;
  deadline_at?: string;
  cancellation_requested?: boolean;
  scopes?: string[];
  policy?: Record<string, unknown>;
  capabilities?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
};

export type KAExecutionRequest = {
  input: Record<string, unknown>;
  mode?: KAExecutionMode;
  context?: KAExecutionContext;
  budget?: {
    timeout_ms?: number;
    max_artifacts?: number;
    max_effects?: number;
    max_output_bytes?: number;
  };
};

export type KAExecutionResult = {
  schema_version: "dle.ka-execution-result.v1";
  success: boolean;
  state: KAExecutionState;
  canonical_id: string;
  requested_id: string;
  manifest_version: string;
  request_id: string;
  run_id: string;
  trace_id: string;
  output: Record<string, unknown>;
  artifacts: Array<Record<string, unknown>>;
  effects: Array<Record<string, unknown>>;
  error: { code: string; message: string } | null;
  duration_ms: number;
  implementation_adapter: string | null;
};

export type KAListResponse = {
  algorithms: Array<Record<string, unknown>>;
  total_count: number;
};

export type KAExecutionEnvelope = {
  success: boolean;
  result: {
    algorithm_id: string;
    executed_at: string;
    status: "completed" | "failed";
    output: Record<string, unknown>;
    log: string;
    execution_time_ms: number;
    canonical_result?: KAExecutionResult;
  };
};
