export const API_BASE = "/api/v1";

// --- Interfaces ---

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  messages: Message[];
  run_ukg_pipeline?: boolean;
  mode?: string;
  session_id?: string;
  provider?: string;
  model?: string;
}

export interface ChatResponse {
  response: string;
  history?: Message[];
  trace_id?: string;
  trace_summary?: unknown;
  error?: string;
  provider_used?: string;
  model_used?: string;
}

export interface TraceRun {
  run_id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  input_message?: string;
  ka_id?: string;
  scores?: {
      confidence: number;
      entropy: number;
      bias_risk: number;
  };
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

export interface TraceDetail extends TraceRun {
  stages?: KAExecution[];
  evidence?: Record<string, unknown>[];
  metrics?: Record<string, number>;
}

export interface PillarLevel {
  uid: string;
  pillar_id: string; // Changed from number to match backend PL01 string
  name: string;
  description?: string;
  sublevels?: PillarLevel[];
}

export interface SimulationSession {
  uid: string;
  name: string;
  status: "active" | "completed" | "failed";
  progress?: number;
  created_at: string;
  current_step: number;
  user_id: string;
}

export type KnowledgePillar = PillarLevel;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type KnowledgeStats = any[];
// Advanced Tracing Interfaces

export interface TracePersona {
  persona_id: string;
  run_id: string;
  persona_type: 'analyst' | 'expert' | 'critic' | 'synthesizer' | 'custom' | 'knowledge' | 'sector' | 'regulatory' | 'compliance';
  persona_name?: string;
  status: string;
  draft?: {
    text?: string;
    confidence?: number;
  };
  confidence?: number; // Top level confidence
}

export interface TraceAxisVector {
  vector_id: string;
  run_id: string;
  axes: Record<string, {
    name: string;
    selected: boolean;
    candidates?: string[];
  }>;
  coordinate_hash?: string;
}

export interface TraceStage {
  stage_id: string;
  run_id: string;
  name: string;
  stage_type: 'layer' | 'step';
  layer_index?: number;
  step_index?: number;
  status: string;
  start_time?: string;
  end_time?: string;
  duration_ms?: number;
  inputs?: Record<string, unknown>;
  outputs?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
  algorithm_name?: string; // Legacy support if needed
  started_at?: string;     // Legacy support
}
export interface AnalyticsOverview {
  api_requests_24h: number;
  kg_nodes: number;
  kg_edges: number;
  kg_size_display: string;
  compliance_status: string;
  compliance_score: string;
  timestamp: string;
}

export interface McpStats {
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
