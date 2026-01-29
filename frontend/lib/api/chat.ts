import { request } from './index';
import { ChatMessage, ChatRequest, ChatResponse } from './types';

export interface ChatSession {
  id: string;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
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
    return request<{ messages: any[] }>(`/gateway/sessions/${sessionId}/messages`);
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
