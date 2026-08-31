export const API_BASE = "/api/v1";

// --- Interfaces ---

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  messages: Message[];
  request_id?: string;
  run_ukg_pipeline?: boolean;
  mode?: string;
  session_id?: string;
  provider?: string;
  model?: string;
  meta?: Record<string, unknown>;
}

export interface ChatResponse {
  contract_version?: 'governed.v1' | string;
  status?: string;
  completion?: ProviderCompletion | null;
  mode?: GovernedMode;
  confidence_display?: ConfidenceDisplay | null;
  provider_call_budget?: ProviderCallBudget | null;
  response?: string;
  history?: Message[];
  trace_id?: string;
  run_id?: string;
  audit_trail?: AuditTrail;
  trace_summary?: unknown;
  error?: string;
  queued?: boolean;
  queue_item?: unknown;
  provider_used?: string | null;
  model_used?: string;
  confidence_score?: number | null;
  confidence_measurement?: ConfidenceMeasurement | null;
  convergence?: Record<string, unknown> | null;
  evidence_count?: number;
  source_ids?: string[];
  claims?: Array<{
    claim_id: string;
    text: string;
    evidence_ids: string[];
    status: string;
    confidence: number;
  }>;
  citations?: Array<Record<string, unknown>>;
  validators?: Array<Record<string, unknown>>;
  failure?: {
    kind: string;
    code: string;
    message: string;
    stage: string;
    retryable: boolean;
    details?: Record<string, unknown>;
  } | null;
}

export type GovernedMode = 'standard' | 'enhanced' | 'local_review';

export interface ProviderCallBudget {
  max_calls: number;
  calls_used: number;
}

export interface ConfidenceDisplay {
  schema_version?: string;
  status: 'measured' | 'not_measured' | 'validation_failed' | 'insufficient_evidence';
  measurement_status?: string;
  value: number | null;
  formula_version?: string | null;
  reason: string;
  missing_components: string[];
  failed_validator_ids?: string[];
  explanation: string;
}

export type CompletionDisposition =
  | 'complete'
  | 'length_limited'
  | 'safety_blocked'
  | 'provider_incomplete'
  | 'failed';

export interface ProviderCompletion {
  disposition: CompletionDisposition;
  native_reason?: string | null;
  response_id?: string | null;
}

export interface AuditTrail {
  decision_path: string;
  complete_trace_url: string;
  download_url: string;
}

export interface TraceRun {
  run_id: string;
  status: string;
  created_at: string | null;
  completed_at?: string | null;
  input_message?: string | null;
  ka_id?: string | null;
  scores?: {
      confidence?: number | null;
      entropy?: number | null;
      bias_risk?: number | null;
  } | null;
  /** LLM model used for this run (e.g. "gpt-5.6-sol", "gemini-3.7-flash"). */
  model_name?: string | null;
  /** Provider that served this run (e.g. "openai", "google"). */
  provider_used?: string | null;
  data_snapshot?: {
    confidence_measurement?: ConfidenceMeasurement | null;
    confidence_display?: ConfidenceDisplay | null;
    governed_mode?: GovernedMode | null;
    provider_call_budget?: ProviderCallBudget | null;
    convergence?: Record<string, unknown> | null;
    [key: string]: unknown;
  } | null;
}

export interface ConfidenceMeasurement {
  formula_version?: string;
  value?: number | null;
  status?: string;
  components?: Record<string, number | null>;
  weights?: Record<string, number>;
  missing_components?: string[];
  explanation?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
  role: string;
  windows_sid?: string;
  created_at?: string;
}

export interface KAExecution {
  id: number;
  uid: string;
  algorithm_id: number;
  algorithm_name?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  input_params: Record<string, unknown>;
  output_results?: Record<string, unknown>;
  error_message?: string;
}

export interface KAExecutionFeedItem {
  id: number;
  uid: string | null;
  ka_id: string | null;
  status: string | null;
  execution_time_ms: number | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface KAExecutionFeed {
  items: KAExecutionFeedItem[];
  limit: number;
  updated_at: string;
}

export interface ToolExecutionHistoryItem {
  id: string;
  ka_id: string;
  ka_name: string;
  risk_tier: 'read_only' | 'write' | 'destructive' | string;
  status: 'success' | 'failure' | 'blocked' | string;
  triggered_by: string;
  run_id: string | null;
  duration_ms: number | null;
  created_at: string | null;
  error: string | null;
}

export interface ToolExecutionHistoryResponse {
  success?: boolean;
  executions?: ToolExecutionHistoryItem[];
  error?: string;
}

export type KAProductRunStatus =
  | 'planned'
  | 'queued'
  | 'running'
  | 'succeeded'
  | 'partial'
  | 'blocked'
  | 'failed'
  | 'cancelled'
  | 'timed_out'
  | 'dry_run'
  | 'expired';

export interface KAProductRun {
  schema_version: 'dle.ka-product-run.v1';
  run_id: string;
  request_id: string;
  canonical_id: string;
  manifest_version: string;
  status: KAProductRunStatus;
  mode: 'production' | 'evaluation' | 'dry_run';
  risk_tier: 'read_only' | 'write' | 'destructive';
  confirmation_required: boolean;
  confirmed: boolean;
  cancellation_requested: boolean;
  result_size_bytes: number | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  expires_at: string;
  status_url: string;
  execute_url: string;
  cancel_url: string;
  result_url: string;
  trace_url: string;
  artifacts_url: string;
  effects_url: string;
}

export interface KAProductPlanEnvelope {
  success: boolean;
  run: KAProductRun;
  plan: {
    plan_id: string;
    manifest_version: string;
    valid: boolean;
    validation_errors: string[];
    selected_ids: string[];
    execution_order: string[][];
    selected_count: number;
    dependency_count: number;
    effect_proposal_count: number;
    estimated_critical_path_ms: number;
    risk: {
      tier: 'read_only' | 'write' | 'destructive';
      risk_classes: string[];
      effect_oriented_ids: string[];
      effect_ports: string[];
      confirmation_reasons: string[];
    };
    entries: Record<string, Record<string, unknown>>;
  };
  confirmation_token: string | null;
}

export interface KAProductRunEnvelope {
  success: boolean;
  run: KAProductRun;
  plan?: KAProductPlanEnvelope['plan'];
}

export interface KAProductRunListEnvelope {
  success: boolean;
  runs: KAProductRun[];
}

export interface TraceDetail extends TraceRun {
  stages?: KAExecution[];
  evidence?: Record<string, unknown>[];
  metrics?: Record<string, number>;
}

export interface TraceEvidenceSource {
  evidence_id: string;
  run_id: string;
  source_id?: string | null;
  source_type?: string | null;
  title?: string | null;
  evidence_tier?: 'GOLD' | 'SILVER' | 'BRONZE' | 'UNVERIFIED';
  credibility_score?: number | null;
  claims_supported?: string[];
  layer_retrieved?: string | null;
  ka_that_invoked?: string | null;
  source?: Record<string, unknown>;
  locator?: Record<string, unknown> | null;
  snippet?: string | null;
}

export interface TraceKAInvocation {
  invocation_id: string;
  run_id: string;
  stage_id?: string | null;
  ka_id: string;
  ka_name?: string | null;
  status: string;
  timing?: { duration_ms?: number | null };
  inputs?: Record<string, unknown> | null;
  outputs?: Record<string, unknown> | null;
}

export interface TraceBundle {
  run_id: string;
  status: string;
  run: TraceRun;
  frost_layers: TraceStage[];
  stages: TraceStage[];
  evidence_sources: TraceEvidenceSource[];
  evidence: TraceEvidenceSource[];
  claims: Record<string, unknown>[];
  citations?: Record<string, unknown>[];
  validators?: Record<string, unknown>[];
  quality_decisions?: Record<string, unknown>[];
  persona_positions: TracePersona[];
  personas: TracePersona[];
  ka_invocations: TraceKAInvocation[];
  kas: TraceKAInvocation[];
  coordinate: TraceAxisVector | null;
  axes: TraceAxisVector | null;
  policy_decisions: Record<string, unknown>[];
  memory_events: Record<string, unknown>[];
  metrics: {
    total_duration_ms?: number | null;
    total_tokens_in?: number | null;
    total_tokens_out?: number | null;
    total_retrievals?: number | null;
    stage_count?: number | null;
    confidence?: number | null;
    entropy?: number | null;
  };
  export_url: string;
}

export interface PillarLevel {
  uid: string;
  pillar_id: string; // Changed from number to match backend PL01 string
  name: string;
  description?: string;
  sublevels?: PillarLevel[];
}

export interface SimulationSession {
  session_id: string;
  name?: string | null;
  status: "draft" | "queued" | "running" | "paused" | "materialization_pending" | "completed" | "failed" | "cancelled" | "timeout";
  progress?: number;
  created_at: string;
  current_step: number;
  total_steps?: number | null;
  user_id: number;
  parameters?: Record<string, unknown> | null;
  results?: {
    status?: string;
    final_conclusion?: string;
    confidence_score?: number | null;
    validation?: { status?: string; reason?: string };
    budget?: SimulationBudget;
    artifacts?: Array<{ type: string; state: string }>;
  } | null;
  plan?: SimulationPlan;
  budget?: SimulationBudget;
  scenario_revision?: string | null;
  provider_call_count?: number;
  artifact_state?: string;
  last_error_code?: string | null;
  last_error_message?: string | null;
}

export interface SimulationPlan {
  contract_version: string;
  engine: string;
  engine_version: string;
  depth: "quick" | "standard" | "deep";
  debate_turns: number;
  participants: string[];
  max_provider_calls: number;
  max_tokens_per_call: number;
  max_output_tokens: number;
}

export interface SimulationBudget {
  max_provider_calls: number;
  max_total_tokens: number;
  max_output_tokens?: number;
  max_tool_calls?: number;
  max_cost_usd?: number | null;
  estimated_cost_usd?: number | null;
  pricing_status?: string;
  provider_status?: string;
  admissible?: boolean;
  blocking_code?: string | null;
  provider_calls_used?: number;
  tokens_in?: number;
  tokens_out?: number;
}

export interface SimulationPreflight {
  scenario: Record<string, unknown>;
  scenario_revision: string;
  plan: SimulationPlan;
  budget: SimulationBudget;
}

export interface SimulationEvent {
  sequence: number;
  event_type: string;
  status: string;
  step_key?: string | null;
  current_step?: number | null;
  total_steps?: number | null;
  details: Record<string, unknown>;
  created_at: string;
}

export type KnowledgePillar = PillarLevel;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type KnowledgeStats = any[];
// Advanced Tracing Interfaces

export interface TracePersona {
  persona_id: string;
  run_id: string;
  persona_type: 'analyst' | 'expert' | 'critic' | 'synthesizer' | 'custom' | 'knowledge' | 'sector' | 'regulatory' | 'compliance';
  persona_name?: string | null;
  status: string;
  draft?: {
    text?: string | null;
    confidence?: number | null;
  };
  confidence?: number | null; // Top level confidence
  initial_position?: string | null;
  critique_of_others?: string | null;
  final_position?: string | null;
  synthesis_weight?: number | null;
  flagged_conflicts?: string[];
}

export interface TraceAxisVector {
  vector_id: string;
  run_id: string;
  axes: Record<string, {
    name?: string | null;
    selected?: boolean | null;
    candidates?: string[];
  }> | null;
  coordinate_hash?: string;
}

export interface TraceStage {
  stage_id: string;
  run_id: string;
  name: string;
  stage_type: 'layer' | 'step';
  layer_index?: number | null;
  step_index?: number | null;
  status: string;
  start_time?: string | null;
  end_time?: string | null;
  duration_ms?: number | null;
  inputs?: Record<string, unknown>;
  outputs?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
  algorithm_name?: string; // Legacy support if needed
  started_at?: string | null;     // Legacy support
}

export interface TraceRefinementStep {
  step: number;
  step_id: string;
  name: string;
  status: string;
  reason?: string | null;
  candidate_ka_ids?: string[];
  selected_ka_ids?: string[];
  executed_ka_ids?: string[];
  reused_ka_ids?: string[];
  findings?: Record<string, unknown>[];
  constraints?: string[];
  effects?: Record<string, unknown>[];
}

export interface TraceRefinementReceipt {
  schema_version: 'dle.canonical-refinement-result.v1';
  registry_version: string;
  status: string;
  steps: TraceRefinementStep[];
  step_count: number;
  step_status_counts?: Record<string, number>;
  rewrite_authorized: boolean;
  rewrite_constraints?: string[];
  provider_subcalls_used?: number;
  max_provider_rewrites?: number;
  blocked_by_step?: string | null;
}

export interface IngestionRejectedFile {
  path: string;
  reason: string;
}

export interface IngestionChunk {
  node_uid: string;
  node_id: string;
  source_path: string;
  chunk_index: number;
  chunk_count: number;
  content_hash: string;
  chunk_hash: string;
  indexed: boolean;
}

export interface IngestionResult {
  ingestion_id: string;
  source: string;
  files_scanned: number;
  files_ingested: number;
  files_rejected: number;
  chunks_created: number;
  chunks_indexed: number;
  rejected_files: IngestionRejectedFile[];
  chunks: IngestionChunk[];
  manifest_path?: string | null;
  status?: string;
  checkpoint?: string;
  materializations_pending?: number;
  files?: IngestionFileState[];
}

export interface IngestionFileState {
  relative_path: string;
  status: string;
  source_revision?: string | null;
  detected_type?: string | null;
  parser_result?: { status?: string; detected_type?: string } | null;
  defense_result?: {
    policy_version?: string;
    disposition?: string;
    safe_for_retrieval?: boolean;
    categories?: string[];
  } | null;
  object_status?: string | null;
  normalized_object_status?: string | null;
  embedding_revision?: string | null;
  vector_status?: string | null;
  graph_status?: string | null;
  last_retrieved_at?: string | null;
  last_retrieval_trace_id?: string | null;
  error_code?: string | null;
}

export interface IngestionSupportedTypes {
  extensions: string[];
  default_chunk_size: number;
  default_max_file_bytes: number;
  default_max_total_bytes: number;
  default_max_files: number;
  default_max_pages: number;
  default_max_archive_entries: number;
  default_max_decompressed_bytes: number;
  default_max_archive_depth: number;
  default_parser_timeout_seconds: number;
}

export interface AnalyticsOverview {
  api_requests_24h: number;
  kg_nodes: number;
  kg_edges: number;
  kg_size_display: string;
  validation_status: string;
  average_validation_confidence: string;
  validation_run_count?: number;
  failed_validation_runs?: number;
  timestamp: string;
}

export interface McpStats {
  timestamp?: string;
  time_series: { time: string; requests: number; responses: number; errors: number }[];
  top_tools: { name: string; calls: number; percent: number }[];
  server_health: { name: string; status: string; latency: number }[];
  error_stats: { name: string; value: number; color?: string; colorCode?: string }[];
}

export interface Activity {
  type: string;
  title: string;
  time: string;
  id?: string;
  color?: string;
}

export interface GraphNode {
  id: string;
  uid?: string;
  name: string;
  label?: string;
  node_type?: string;
  pillar?: string;
  group?: number;
  val?: number;
  details?: Record<string, string>;
  attributes?: Record<string, unknown>;
}

export interface GraphEdge {
  id?: string;
  uid?: string;
  source: string;
  target: string;
  type?: string;
  edge_type?: string;
  weight?: number;
  attributes?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}
