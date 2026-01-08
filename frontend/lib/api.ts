export const API_BASE = "/api/v1";

// Interfaces
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatResponse {
  response: string;
  history?: ChatMessage[];
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
}

export interface TraceDetail extends TraceRun {
  stages?: any[];
  evidence?: any[];
  metrics?: any;
}

// Client
export const api = {
  chat: {
    send: async (message: string, provider: string = 'openai', model: string = 'gpt-4') => {
      try {
        const res = await fetch(`${API_BASE}/gateway/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, provider, model })
        });
        if (!res.ok) throw new Error("Chat failed");
        return await res.json() as ChatResponse;
      } catch (err) {
        console.error(err);
        return { response: "Error connecting to server.", error: String(err) };
      }
    }
  },
  
  trace: {
    list: async (limit: number = 10) => {
       try {
         const res = await fetch(`${API_BASE}/trace/runs?limit=${limit}`);
         if (!res.ok) return []; // Fallback empty
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
           const res = await fetch(`/health`);
           return res.ok ? 'Operational' : 'Degraded';
        } catch (e) { return 'Offline'; }
     }
  }
};
