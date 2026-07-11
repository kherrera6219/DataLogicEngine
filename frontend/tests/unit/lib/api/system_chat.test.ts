import { describe, it, expect, vi, beforeEach } from 'vitest';
import { system, sendChat, chat } from '@/lib/api/system_chat';
import * as apiBase from '@/lib/api/client';

vi.mock('@/lib/api/client', () => ({
  request: vi.fn(),
  API_BASE: 'http://localhost:5000/api/v1'
}));

describe('system_chat API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('system.health', () => {
    it('returns health status on success', async () => {
      vi.mocked(apiBase.request).mockResolvedValueOnce({ status: 'ok' });
      const result = await system.health();
      expect(result).toBe('ok');
      expect(apiBase.request).toHaveBeenCalledWith('/health');
    });

    it('returns "Offline" on failure', async () => {
      vi.mocked(apiBase.request).mockRejectedValueOnce(new Error('Fail'));
      const result = await system.health();
      expect(result).toBe('Offline');
    });
  });

  describe('sendChat', () => {
    it('omits provider and model when not supplied so the backend uses its DB config', async () => {
      vi.mocked(apiBase.request).mockResolvedValueOnce({ response: 'hi' });
      const payload = { messages: [{ role: 'user' as const, content: 'hello' }] };
      await sendChat(payload);

      expect(apiBase.request).toHaveBeenCalledWith('/gateway/chat', expect.objectContaining({
        method: 'POST',
      }));

      // provider and model must NOT be in the body when not supplied by the caller.
      // The backend reads LLMProvider.model_id from the database in this case (Sprint 5f).
      const callBody = (vi.mocked(apiBase.request).mock.calls[0][1] as { body: string }).body;
      expect(callBody).not.toContain('"provider"');
      expect(callBody).not.toContain('"model"');
      expect(callBody).toContain('"messages"');
    });

    it('includes provider and model when explicitly supplied by the caller', async () => {
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
