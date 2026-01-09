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
  progress?: number; // Calculated on frontend or added to backend model
  created_at: string;
  current_step: number;
  user_id: string;
}

// --- Unified Client ---

export const api = {
  chat: {
    sendSimple: async (message: string) => {
       return sendChat({ messages: [{ role: 'user', content: message }] });
    }
  },
  
  auth: {
      check: async () => {
          try {
              const res = await fetch(`${API_BASE}/auth/check`);
              return await res.json();
          } catch(e) { return null; }
      },
      login: async (credentials: any) => {
          const res = await fetch(`${API_BASE}/auth/login`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(credentials)
          });
          return await res.json();
      },
      logout: async () => {
          await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
      }
  },

  trace: {
    list: async (limit: number = 10) => {
       try {
         const res = await fetch(`${API_BASE}/trace/runs?limit=${limit}`);
         if (!res.ok) return [];
         const data = await res.json();
         // Handle both envelope { success: true, data: [...] } and direct array [...]
         if (data.success && Array.isArray(data.data)) return data.data;
         return Array.isArray(data) ? data : (data.runs || []);
       } catch (err) {
         console.error("Failed to fetch traces", err);
         return [];
       }
    },
    get: async (id: string) => {
       try {
         const res = await fetch(`${API_BASE}/trace/runs/${id}`);
         if (!res.ok) return null;
         const data = await res.json();
         return data.success ? data.data : data; 
       } catch (err) {
          return null;
       }
    }
  },
  
  knowledge: {
      pillars: async () => {
          try {
              const res = await fetch(`${API_BASE}/pillar-levels`); // Using pillar-levels as proxy for top-level
              if (!res.ok) return [];
              const data = await res.json();
              return (data.success ? data.data : data) as PillarLevel[];
          } catch(e) { return []; }
      },
      stats: async () => {
          // Placeholder for real stats endpoint, currently just counting pillars
          try {
             const res = await fetch(`${API_BASE}/pillar-levels`);
             return (await res.json()).data?.length || 0;
          } catch(e) { return 0; }
      }
  },

  simulation: {
      list: async () => {
          try {
            const res = await fetch(`${API_BASE}/simulations`);
            if (!res.ok) return [];
            const data = await res.json();
            return (data.success ? data.data : data) as SimulationSession[];
          } catch (e) { return []; }
      },
      create: async (name: string, parameters: any = {}) => {
          const res = await fetch(`${API_BASE}/simulations`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ name, parameters })
          });
          if (!res.ok) throw new Error("Failed to create simulation");
          const data = await res.json();
          return data.success ? data.data : data;
      },
      step: async (uid: string) => {
          const res = await fetch(`${API_BASE}/simulations/${uid}/step`, { method: 'POST' });
          return res.json();
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
