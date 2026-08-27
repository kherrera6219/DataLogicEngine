import { request } from '@/lib/api/client';
import { ChatRequest, ChatResponse, ProviderCompletion } from './types';

export interface ChatSession {
  id: string;
  user_id: number;
  title: string | null;
  mode?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateChatSessionRequest {
  session_id: string;
  mode: 'chat' | 'quad';
}

export interface CreateChatSessionResponse {
  session: ChatSession;
  created: boolean;
}

export interface ApiChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  is_enhanced?: boolean;
  run_id?: string;
  completion?: ProviderCompletion | null;
}

export const chat = {
  /**
   * List all chat sessions for the current user
   */
  listSessions: async () => {
    return request<{ sessions: ChatSession[] }>('/gateway/sessions');
  },

  /**
   * Get messages for a specific session
   */
  getSessionMessages: async (sessionId: string) => {
    return request<{ messages: ApiChatMessage[] }>(`/gateway/sessions/${sessionId}/messages`);
  },

  /**
   * Create or idempotently resolve a principal-owned desktop chat session.
   */
  createSession: async (payload: CreateChatSessionRequest) => {
    return request<CreateChatSessionResponse>('/gateway/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Send a message to the gateway
   */
  sendMessage: async (payload: ChatRequest): Promise<ChatResponse> => {
    return request<ChatResponse>('/gateway/chat', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  /**
   * Get gateway health status
   */
  getHealth: async () => {
    return request<{ active_providers: number, message: string }>('/gateway/health');
  }
};
