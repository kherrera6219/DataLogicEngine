import { API_BASE, ChatRequest, ChatResponse } from './types';

export const system = {
    health: async () => {
       try {
          const res = await fetch(`/health`);
          return res.ok ? 'Operational' : 'Degraded';
       } catch (e) { return 'Offline'; }
    }
};

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  try {
    const res = await fetch(`${API_BASE}/gateway/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
          messages: payload.messages,
          provider: payload.provider || 'openai',
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
  } catch (err) {
    console.error(err);
    const errorMessage = err instanceof Error ? err.message : "Network error";
    throw new Error(errorMessage);
  }
}

export const chat = {
    sendSimple: async (message: string) => {
       return sendChat({ messages: [{ role: 'user', content: message }] });
    }
};
