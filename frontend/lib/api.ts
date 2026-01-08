// Toast removed as sonner is not installed. Add later if needed.
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

export interface TraceDetail extends TraceRun {
  stages?: any[];
  evidence?: any[];
  metrics?: any;
}

// --- Unified Client ---

export const api = {
  chat: {
    // New simplified method
    sendSimple: async (message: string) => {
       return sendChat({ messages: [{ role: 'user', content: message }] });
    }
  },
  
  trace: {
    list: async (limit: number = 10) => {
       try {
         const res = await fetch(`${API_BASE}/trace/runs?limit=${limit}`);
         if (!res.ok) return [];
         const data = await res.json();
         return data.runs as TraceRun[];
       } catch (err) {
         console.error("Failed to fetch traces", err);
         return [];
       }
    },
    get: async (id: string) => {
       try {
         const res = await fetch(`${API_BASE}/trace/runs/${id}`);
         if (!res.ok) return null;
         return await res.json() as TraceDetail;
       } catch (err) {
          return null;
       }
    }
  },

  system: {
     health: async () => {
        try {
           const res = await fetch(`/health`);  // Gateway health endpoint
           return res.ok ? 'Operational' : 'Degraded';
        } catch (e) { return 'Offline'; }
     }
  }
};

// --- Legacy / Standalone Exports for ChatInterface ---

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  try {
    const res = await fetch(`${API_BASE}/gateway/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
          messages: payload.messages,
          provider: payload.provider || 'openai', // Defaults
          model: payload.model || 'gpt-4',
          run_ukg_pipeline: payload.run_ukg_pipeline,
          mode: payload.mode
      })
    });
    
    if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Chat failed: ${res.status} ${errText}`);
    }
    return await res.json() as ChatResponse;
  } catch (err: any) {
    console.error(err);
    throw new Error(err.message || "Network error");
  }
}

export async function getProviders() {
    try {
        const res = await fetch(`${API_BASE}/gateway/providers`);
        return await res.json();
    } catch (e) { return []; }
}
