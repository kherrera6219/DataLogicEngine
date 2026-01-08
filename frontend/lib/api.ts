export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatResponse {
  response: string;
  run_id: string;
  provider_used: string;
  model_used: string;
  confidence_score?: number;
  trace_summary?: any;
  coordinates?: any;
  claims?: any[];
  evidence_count?: number;
}

export interface ChatRequest {
  messages: Message[];
  provider?: string;
  model?: string;
  mode?: 'chat' | 'trace' | 'explain';
  run_ukg_pipeline?: boolean;
}

export async function sendChat(data: ChatRequest): Promise<ChatResponse> {
  const res = await fetch('/api/v1/gateway/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // 'X-API-Key': 'key' // TODO: Add auth state
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `Request failed with status ${res.status}`);
  }

  return res.json();
}

export async function getProviders() {
  const res = await fetch('/api/v1/gateway/providers');
  if (!res.ok) throw new Error('Failed to fetch providers');
  return res.json();
}
