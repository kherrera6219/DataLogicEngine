import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatInterface } from './ChatInterface';
import { FeatureFlagProvider } from '@/contexts/FeatureFlagContext';
import { ToastProvider } from '@/components/ui/use-toast';
import { api, request } from '@/lib/api';
import { socketClient } from '@/lib/socket';

// Mock dependencies
vi.mock('uuid', () => ({
  v4: () => 'test-session-uuid'
}));

vi.mock('@/lib/api', () => ({
  api: {
    chat: {
      listSessions: vi.fn(),
      getSessionMessages: vi.fn(),
      sendMessage: vi.fn(),
    },
  },
  request: vi.fn(),
}));

vi.mock('@/lib/socket', () => {
  const mSocket = {
    on: vi.fn(),
    emit: vi.fn(),
    off: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    connected: true,
    joinRoom: vi.fn(),
    leaveRoom: vi.fn(),
    setHandlers: vi.fn(),
  };
  return {
    socketClient: mSocket,
    useSocket: vi.fn((handlers) => {
      if (handlers) mSocket.setHandlers(handlers);
      return mSocket;
    }),
  };
});

// Mock child components
vi.mock('@/components/ui/scroll-area', () => ({
  ScrollArea: ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={className} data-testid="scroll-area">{children}</div>
  )
}));

vi.mock('./LiveTracePanel', () => ({
  LiveTracePanel: () => <div data-testid="trace-panel">Trace</div>
}));
vi.mock('./DetailedResponseView', () => ({
  DetailedResponseView: ({ message }: { message: { id: string } }) => <div data-testid="detailed-view">{message.id}</div>
}));
vi.mock('./TraceVisualizer', () => ({
  TraceVisualizer: () => <div data-testid="trace-visualizer">Visualizer</div>
}));
vi.mock('./AdvancedControls', () => ({
  AdvancedControls: () => <div data-testid="advanced-controls">Controls</div>
}));

describe('ChatInterface', () => {
  const renderChatInterface = () =>
    render(
      <FeatureFlagProvider>
        <ToastProvider>
          <ChatInterface />
        </ToastProvider>
      </FeatureFlagProvider>,
    );

  const mockSessions = [
    { id: 'session-1', title: 'Session 1' },
    { id: 'session-2', title: 'Session 2' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (api.chat.listSessions as ReturnType<typeof vi.fn>).mockResolvedValue({ sessions: mockSessions });
    (api.chat.getSessionMessages as ReturnType<typeof vi.fn>).mockResolvedValue({ 
      messages: [{ id: 'hist-1', role: 'assistant', content: '', finalAnswer: 'Session History' }] 
    });
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValue({ 
      response: 'Core Response',
      trace_summary: { steps: [] }
    });
    (request as ReturnType<typeof vi.fn>).mockResolvedValue({ message: 'Success' });
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  it('should load sessions and initial messages on mount', async () => {
    renderChatInterface();
    await waitFor(() => expect(screen.getByText('Session 1')).toBeInTheDocument());
  });

  it('should handle switching sessions', async () => {
    renderChatInterface();
    await waitFor(() => screen.getByText('Session 2'));
    fireEvent.click(screen.getByText('Session 2'));
    expect(socketClient.joinRoom).toHaveBeenCalled();
  });

  it('should handle sending a message and displaying direct response', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValue({ 
      response: 'Core Response',
      trace_summary: { steps: [] }
    });

    renderChatInterface();
    
    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    fireEvent.change(textarea, { target: { value: 'Test query' } });
    
    const sendBtn = screen.getByText('Send');
    fireEvent.click(sendBtn);
    
    await waitFor(() => expect(screen.getByText('Core Response')).toBeInTheDocument());
  });

  it('should handle API errors gracefully', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network Failure'));

    renderChatInterface();
    
    await screen.findByTestId('main-chat-area', {}, { timeout: 8000 });
    
    await waitFor(() => {
      const msgs = screen.queryAllByTestId('message-item');
      expect(msgs.length).toBeGreaterThan(0);
    }, { timeout: 8000 });
    
    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    await act(async () => {
      fireEvent.change(textarea, { target: { value: 'Failure test' } });
    });
    
    await waitFor(() => expect(sendButton).not.toBeDisabled());
    
    await act(async () => {
      fireEvent.click(sendButton);
    });

    expect(await screen.findByText(/I encountered an error/i, {}, { timeout: 10000 })).toBeInTheDocument();
  }, 30000);

  it('should handle file upload successfully', async () => {
    renderChatInterface();
    const file = new File(['test'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText(/upload file/i);
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText(/File processed successfully/i)).toBeInTheDocument();
    });
  });

  it('should clear messages on new chat', async () => {
    renderChatInterface();
    const newChatBtn = screen.getByText(/new chat/i);
    fireEvent.click(newChatBtn);
    expect(screen.queryByTestId('message-bubble')).not.toBeInTheDocument();
  });
});
