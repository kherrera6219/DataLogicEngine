import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { chat } from '@/lib/api/chat';
import { request } from '@/lib/api/index';

// Mock the request function
vi.mock('./index', () => ({
  request: vi.fn(),
  chat: {
    ...vi.importActual('./chat'),
    listSessions: vi.fn(),
    getSessionMessages: vi.fn(),
    sendMessage: vi.fn(),
    getHealth: vi.fn()
  }
}));

// We need to test the real implementation, so we should unmock chat if we want to test it calling request.
// However, if the module exports an object 'chat', we can just test 'chat' methods if they are not mocked.
// But the mock above mocks 'chat' too.
// Let's rely on standard testing: import real chat, mock dependencies (request).

vi.unmock('./chat');

describe('Chat API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('listSessions should call correct endpoint', async () => {
    (request as Mock).mockResolvedValue({ sessions: [] });
    await chat.listSessions();
    expect(request).toHaveBeenCalledWith('/gateway/sessions');
  });

  it('getSessionMessages should call correct endpoint', async () => {
    (request as Mock).mockResolvedValue({ messages: [] });
    await chat.getSessionMessages('123');
    expect(request).toHaveBeenCalledWith('/gateway/sessions/123/messages');
  });

  it('sendMessage should post payload', async () => {
    const payload = { 
        messages: [{ role: 'user' as const, content: 'hello' }], 
        session_id: '123' 
    };
    (request as Mock).mockResolvedValue({ response: 'hi' });
    await chat.sendMessage(payload);
    expect(request).toHaveBeenCalledWith('/gateway/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  });

  it('getHealth should call health endpoint', async () => {
    (request as Mock).mockResolvedValue({ status: 'ok' });
    await chat.getHealth();
    expect(request).toHaveBeenCalledWith('/gateway/health');
  });
});
