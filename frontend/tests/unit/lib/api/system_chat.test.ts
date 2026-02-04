import { describe, it, expect, vi, beforeEach } from 'vitest';
import { system, sendChat, chat } from '@/lib/api/system_chat';
import * as apiBase from '@/lib/api/index';

vi.mock('@/lib/api/index', () => ({
  request: vi.fn(),
  API_BASE: 'http://localhost:5000/api/v1'
}));

describe('system_chat API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('system.health', () => {
    it('returns health status on success', async () => {
      vi.mocked(apiBase.request).mockResolvedValueOnce('OK');
      const result = await system.health();
      expect(result).toBe('OK');
      expect(apiBase.request).toHaveBeenCalledWith('/health');
    });

    it('returns "Offline" on failure', async () => {
      vi.mocked(apiBase.request).mockRejectedValueOnce(new Error('Fail'));
      const result = await system.health();
      expect(result).toBe('Offline');
    });
  });

  describe('sendChat', () => {
    it('sends chat request with defaults', async () => {
      vi.mocked(apiBase.request).mockResolvedValueOnce({ response: 'hi' });
      const payload = { messages: [{ role: 'user' as const, content: 'hello' }] };
      await sendChat(payload);
      
      expect(apiBase.request).toHaveBeenCalledWith('/gateway/chat', expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"provider":"openai"')
      }));
    });

    it('respects provided provider and model', async () => {
      vi.mocked(apiBase.request).mockResolvedValueOnce({ response: 'hi' });
      const payload = { 
        messages: [{ role: 'user' as const, content: 'hello' }],
        provider: 'anthropic',
        model: 'claude-3'
      };
      await sendChat(payload);
      
      expect(apiBase.request).toHaveBeenCalledWith('/gateway/chat', expect.objectContaining({
        body: expect.stringContaining('"provider":"anthropic"')
      }));
      expect(apiBase.request).toHaveBeenCalledWith('/gateway/chat', expect.objectContaining({
        body: expect.stringContaining('"model":"claude-3"')
      }));
    });
  });

  describe('chat.sendSimple', () => {
    it('wraps simple message into chat payload', async () => {
      vi.mocked(apiBase.request).mockResolvedValueOnce({ response: 'hi' });
      await chat.sendSimple('test message');
      expect(apiBase.request).toHaveBeenCalledWith('/gateway/chat', expect.objectContaining({
        body: expect.stringContaining('"content":"test message"')
      }));
    });
  });
});
