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
  provider?: string;
  model?: string;
}

export interface ChatResponse {
  response: string;
  history?: Message[];
  trace_id?: string;
  error?: string;
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
