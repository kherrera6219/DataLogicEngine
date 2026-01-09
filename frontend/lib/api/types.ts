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

export interface TraceDetail extends TraceRun {
  stages?: any[];
  evidence?: any[];
  metrics?: any;
}

export interface PillarLevel {
  uid: string;
  pillar_id: number;
  name: string;
  description?: string;
  sublevels?: any;
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
