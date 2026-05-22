import { ChatRequest, ChatResponse } from './types';
import { request } from '@/lib/api/client';

export const system = {
    health: () => request<string>('/health').catch(() => 'Offline')
};

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/gateway/chat', {
    method: 'POST',
    body: JSON.stringify({
        messages: payload.messages,
        provider: payload.provider || 'openai',
        model: payload.model || 'gpt-5.5',
        run_ukg_pipeline: payload.run_ukg_pipeline,
        mode: payload.mode
    })
  });
}

export const chat = {
    sendSimple: async (message: string) => {
       return sendChat({ messages: [{ role: 'user', content: message }] });
    }
};
