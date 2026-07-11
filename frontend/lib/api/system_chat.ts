import { ChatRequest, ChatResponse } from './types';
import { request } from '@/lib/api/client';

export const system = {
    health: () => request<{ status?: string } | string>('/health')
      .then((payload) => typeof payload === 'string' ? payload : payload.status || 'degraded')
      .catch(() => 'Offline')
};

export async function sendChat(payload: ChatRequest): Promise<ChatResponse> {
  const body: Record<string, unknown> = {
    messages: payload.messages,
    run_ukg_pipeline: payload.run_ukg_pipeline,
    mode: payload.mode,
  };
  // Only include provider / model when the caller supplied them so the backend
  // uses the LLMProvider table rather than a hardcoded default.
  if (payload.provider) body['provider'] = payload.provider;
  if (payload.model) body['model'] = payload.model;
  return request<ChatResponse>('/gateway/chat', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export const chat = {
    sendSimple: async (message: string) => {
       return sendChat({ messages: [{ role: 'user', content: message }] });
    }
};
