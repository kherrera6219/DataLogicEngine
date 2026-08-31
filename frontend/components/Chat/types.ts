export interface TraceStep {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  durationMs?: number;
  percentage: number;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface TracePipeline {
  currentStepId: string;
  steps: TraceStep[];
  totalDurationMs: number;
  estimatedTotalMs: number;
  overallProgress: number;
}

export interface PersonaOutput {
  id: string;
  name: string;
  role: string;
  avatar: string; // emoji or url
  weight: number;
  confidence: number;
  contribution: string;
  sources: string[];
}

export interface ValidationMetric {
  name: string;
  score: number;
  status: 'pass' | 'fail' | 'warn';
  details: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  runId?: string;
  traces?: TracePipeline;
  personas?: PersonaOutput[];
  metrics?: ValidationMetric[];
  finalAnswer?: string;
  isEnhanced?: boolean;
  providerUsed?: string;
  modelUsed?: string;
  completion?: import('@/lib/api/types').ProviderCompletion | null;
  governedMode?: import('@/lib/api/types').GovernedMode;
  confidenceDisplay?: import('@/lib/api/types').ConfidenceDisplay | null;
  providerCallBudget?: import('@/lib/api/types').ProviderCallBudget | null;
  auditTrail?: {
    decision_path: string;
    complete_trace_url: string;
    download_url: string;
  };
}

export interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: string;
  messages: ChatMessage[];
}
