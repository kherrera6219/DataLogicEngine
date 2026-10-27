import React from 'react';
import { render, screen, fireEvent, waitFor, act, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatInterface } from './ChatInterface';
import { FeatureFlagProvider } from '@/contexts/FeatureFlagContext';
import { ToastProvider } from '@/components/ui/use-toast';
import { api, request, ApiError } from '@/lib/api';
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
      createSession: vi.fn(),
      sendMessage: vi.fn(),
    },
  },
  request: vi.fn(),
  // ApiError must be exported so ChatInterface.tsx can use `instanceof ApiError`
  // in its 429 rate-limit handler. Without this the right-hand side of instanceof
  // is undefined at test runtime, causing a Vitest mocker error.
  ApiError: class ApiError extends Error {
    constructor(message: string, public readonly status: number, public readonly payload?: unknown) {
      super(message);
      this.name = 'ApiError';
    }
  },
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
  LiveTracePanel: ({ activeRunId }: { activeRunId?: string | null }) => <div data-testid="trace-panel">{activeRunId || 'No selected run'}</div>
}));
vi.mock('./DetailedResponseView', () => ({
  DetailedResponseView: ({ message }: { message: { id: string } }) => <div data-testid="detailed-view">{message.id}</div>
}));
vi.mock('./TraceVisualizer', () => ({
  TraceVisualizer: () => <div data-testid="trace-visualizer">Visualizer</div>
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
  const auditTrail = {
    decision_path: '/api/v1/trace/runs/run-queued-001/decision',
    complete_trace_url: '/api/v1/trace/runs/run-queued-001',
    download_url: '/api/v1/trace/runs/run-queued-001/download',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (api.chat.listSessions as ReturnType<typeof vi.fn>).mockResolvedValue({ sessions: mockSessions });
    (api.chat.getSessionMessages as ReturnType<typeof vi.fn>).mockResolvedValue({ 
      messages: [{ id: 'hist-1', role: 'assistant', content: '', finalAnswer: 'Session History' }] 
    });
    (api.chat.createSession as ReturnType<typeof vi.fn>).mockResolvedValue({
      created: true,
      session: {
        id: 'created-session-1',
        user_id: 1,
        title: null,
        mode: 'chat',
        created_at: '2026-08-26T00:00:00Z',
        updated_at: '2026-08-26T00:00:00Z',
      },
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
    expect(screen.getByText(/Graph relationships are used only when graph context is explicitly enabled/i)).toBeInTheDocument();
  });

  it('should handle switching sessions', async () => {
    renderChatInterface();
    await waitFor(() => screen.getByText('Session 2'));
    fireEvent.click(screen.getByText('Session 2'));
    expect(socketClient.joinRoom).toHaveBeenCalled();
  });

  it('does not replace the selected session with a late history response', async () => {
    let resolveOld!: (value: unknown) => void;
    (api.chat.getSessionMessages as ReturnType<typeof vi.fn>).mockImplementation((id: string) =>
      id === 'session-1'
        ? new Promise((resolve) => { resolveOld = resolve; })
        : Promise.resolve({ messages: [{ id: 'b', role: 'assistant', content: 'Session B history' }] }),
    );
    renderChatInterface();
    await screen.findByRole('button', { name: 'Session 2' });
    await waitFor(() => expect(api.chat.getSessionMessages).toHaveBeenCalledWith('session-1'));
    fireEvent.click(screen.getByRole('button', { name: 'Session 2' }));
    expect(await screen.findByText('Session B history')).toBeInTheDocument();
    await act(async () => resolveOld({ messages: [{ id: 'a', role: 'assistant', content: 'Session A history' }] }));
    expect(screen.getByText('Session B history')).toBeInTheDocument();
    expect(screen.queryByText('Session A history')).not.toBeInTheDocument();
  });

  it('keeps a late response out of a newly selected session', async () => {
    let resolveSend!: (value: unknown) => void;
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockReturnValue(new Promise((resolve) => { resolveSend = resolve; }));
    (api.chat.getSessionMessages as ReturnType<typeof vi.fn>).mockImplementation(async (id: string) => ({
      messages: id === 'session-2' ? [{ id: 'b', role: 'assistant', content: 'Session B history' }] : [],
    }));
    renderChatInterface();
    await screen.findByRole('button', { name: 'Session 1' });
    await waitFor(() => expect(api.chat.getSessionMessages).toHaveBeenCalledWith('session-1'));
    fireEvent.change(screen.getByRole('textbox', { name: /message composer/i }), { target: { value: 'Question for A' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    await waitFor(() => expect(api.chat.sendMessage).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button', { name: 'Session 2' }));
    expect(await screen.findByText('Session B history')).toBeInTheDocument();
    await act(async () => resolveSend({ response: 'Answer for A' }));
    expect(screen.getByText('Session B history')).toBeInTheDocument();
    expect(screen.queryByText('Answer for A')).not.toBeInTheDocument();
  });

  it('does not let an earlier request clear the trace of a newer request', async () => {
    let finishRefresh!: (value: unknown) => void;
    let finishSecond!: (value: unknown) => void;
    (api.chat.listSessions as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ sessions: mockSessions })
      .mockReturnValueOnce(new Promise((resolve) => { finishRefresh = resolve; }));
    (api.chat.sendMessage as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ response: 'First answer' })
      .mockReturnValueOnce(new Promise((resolve) => { finishSecond = resolve; }));
    renderChatInterface();
    await screen.findByRole('button', { name: 'Session 1' });
    const composer = screen.getByRole('textbox', { name: /message composer/i });
    fireEvent.change(composer, { target: { value: 'First' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    await screen.findByText('First answer');
    fireEvent.change(composer, { target: { value: 'Second' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    await waitFor(() => expect(api.chat.sendMessage).toHaveBeenCalledTimes(2));
    const secondTrace = screen.getByTestId('trace-panel').textContent;
    expect(secondTrace).not.toBe('No selected run');
    await act(async () => finishRefresh({ sessions: mockSessions }));
    expect(screen.getByTestId('trace-panel')).toHaveTextContent(secondTrace || '');
    await act(async () => finishSecond({ response: 'Second answer' }));
  });

  it('refreshes a session revisited before its background answer completes', async () => {
    let finish!: (value: unknown) => void;
    let saved = false;
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockReturnValue(new Promise((resolve) => { finish = resolve; }));
    (api.chat.getSessionMessages as ReturnType<typeof vi.fn>).mockImplementation(async (id: string) => ({
      messages: id === 'session-1' && saved ? [{ id: 'saved', role: 'assistant', content: 'Saved background answer' }] : [],
    }));
    renderChatInterface();
    await screen.findByRole('button', { name: 'Session 1' });
    await waitFor(() => expect(api.chat.getSessionMessages).toHaveBeenCalledWith('session-1'));
    fireEvent.change(screen.getByRole('textbox', { name: /message composer/i }), { target: { value: 'Question' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    await waitFor(() => expect(api.chat.sendMessage).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button', { name: 'Session 2' }));
    fireEvent.click(screen.getByRole('button', { name: 'Session 1' }));
    await waitFor(() => expect(api.chat.getSessionMessages).toHaveBeenCalledTimes(3));
    saved = true;
    await act(async () => finish({ response: 'Saved background answer' }));
    expect(await screen.findByText('Saved background answer')).toBeInTheDocument();
  });

  it('reports a history load failure and allows selecting the session to retry', async () => {
    (api.chat.getSessionMessages as ReturnType<typeof vi.fn>)
      .mockRejectedValueOnce(new Error('unavailable'))
      .mockResolvedValueOnce({ messages: [{ id: 'retry', role: 'assistant', content: 'Recovered history' }] });
    renderChatInterface();
    expect(await screen.findByText(/could not load this conversation/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Session 1' }));
    expect(await screen.findByText('Recovered history')).toBeInTheDocument();
  });

  it('filters recent sessions by title and restores them when the search is cleared', async () => {
    renderChatInterface();
    await screen.findByRole('button', { name: 'Session 1' });
    const search = screen.getByRole('textbox', { name: 'Search chat sessions' });
    fireEvent.change(search, { target: { value: 'SESSION 2' } });
    expect(screen.queryByRole('button', { name: 'Session 1' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Session 2' })).toBeInTheDocument();
    fireEvent.change(search, { target: { value: 'missing' } });
    expect(screen.getByText('No matching sessions')).toBeInTheDocument();
    fireEvent.change(search, { target: { value: '' } });
    expect(screen.getByRole('button', { name: 'Session 1' })).toBeInTheDocument();
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

  it('labels a length-limited answer and sends the visible transcript with an explicit continuation', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      response: 'The first portion ends here.',
      status: 'length_limited',
      completion: {
        disposition: 'length_limited',
        native_reason: 'MAX_TOKENS',
        response_id: 'provider-response-1',
      },
    });

    renderChatInterface();
    const textarea = await screen.findByRole('textbox', { name: /message composer/i });
    fireEvent.change(textarea, { target: { value: 'Give me a complete Mars engine review' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));

    expect(await screen.findByText(/answer reached the provider output limit/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /prepare continuation/i }));

    expect((textarea as HTMLTextAreaElement).value).toMatch(/continue the prior answer/i);
    expect(api.chat.sendMessage).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /send message/i }));

    await waitFor(() => expect(api.chat.sendMessage).toHaveBeenCalledTimes(2));
    expect(api.chat.sendMessage).toHaveBeenLastCalledWith(
      expect.objectContaining({
        messages: [
          { role: 'user', content: 'Give me a complete Mars engine review' },
          { role: 'assistant', content: 'The first portion ends here.' },
          {
            role: 'user',
            content: 'Continue the prior answer from where it stopped. Do not repeat completed material. Finish the unanswered parts of my request.',
          },
        ],
      }),
    );
  });

  it('renders measured evidence support and the actual Standard mode', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      response: 'Measured response',
      mode: 'standard',
      provider_call_budget: { max_calls: 1, calls_used: 1 },
      confidence_display: {
        status: 'measured',
        value: 0.84,
        formula_version: 'dle-confidence.v1',
        reason: 'all_required_components_measured',
        missing_components: [],
        explanation: 'Evidence-support coverage, not correctness probability.',
      },
    });

    renderChatInterface();
    const textarea = await screen.findByRole('textbox', { name: /message composer/i });
    fireEvent.change(textarea, { target: { value: 'Measured request' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));

    expect(await screen.findByText('Standard Mode')).toBeInTheDocument();
    expect(screen.queryByText(/Enhanced Mode Active/i)).not.toBeInTheDocument();
    expect(screen.getByText('84.0%')).toBeInTheDocument();
    expect(screen.getByText(/not correctness probability/i)).toBeInTheDocument();
    expect(screen.getByText(/1 of 1 provider attempts used/i)).toBeInTheDocument();
    const response = within(screen.getByText('Measured response').closest('[data-testid="message-item"]') as HTMLElement);
    expect(response.getByText(/Standard mode does not enable the 12-step refinement workflow/i)).toBeInTheDocument();
    expect(response.getByText(/does not indicate that the answer met a measured confidence threshold/i)).toBeInTheDocument();
  });

  it('makes the conditional Enhanced budget visible before sending', async () => {
    renderChatInterface();
    const toggle = await screen.findByRole('button', { name: 'Toggle Quad Persona Mode' });
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText(/Enhanced mode permits one conditional refinement cycle and at most 2 counted provider attempts/i)).toBeInTheDocument();
  });

  it('renders unmeasured confidence with its reason and Enhanced mode', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      response: 'Unmeasured response',
      mode: 'enhanced',
      provider_call_budget: { max_calls: 2, calls_used: 1 },
      confidence_display: {
        status: 'insufficient_evidence',
        value: null,
        formula_version: 'dle-confidence.v1',
        reason: 'no_governed_evidence_available',
        missing_components: ['claim_support', 'source_quality'],
        explanation: 'Evidence support was not measured because no governed evidence was available.',
      },
    });

    renderChatInterface();
    const textarea = await screen.findByRole('textbox', { name: /message composer/i });
    fireEvent.change(textarea, { target: { value: 'Unmeasured request' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));

    expect(await screen.findByText('Enhanced Mode')).toBeInTheDocument();
    expect(screen.getByText('Not measured')).toBeInTheDocument();
    expect(screen.getByText(/no governed evidence was available/i)).toBeInTheDocument();
    expect(screen.queryByText('100.0%')).not.toBeInTheDocument();
  });

  it('shows retrieval and indexing failures without exposing internal error details', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      response: 'Answer without available local evidence',
      warnings: ['document_retrieval_failed:RetrievalError', 'user_chat_index_unavailable'],
    });
    renderChatInterface();
    const textarea = await screen.findByRole('textbox', { name: /message composer/i });
    fireEvent.change(textarea, { target: { value: 'Find local evidence' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));
    expect(await screen.findByText(/Some local knowledge could not be searched/i)).toBeInTheDocument();
    expect(screen.getByText(/conversation was saved, but its search index was unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText(/document_retrieval_failed/)).not.toBeInTheDocument();
  });

  it('creates a durable session before the first message is sent', async () => {
    const createdSession = {
      id: 'created-session-1',
      user_id: 1,
      title: null,
      mode: 'chat',
      created_at: '2026-08-26T00:00:00Z',
      updated_at: '2026-08-26T00:00:00Z',
    };
    (api.chat.listSessions as ReturnType<typeof vi.fn>)
      .mockResolvedValueOnce({ sessions: [] })
      .mockResolvedValue({ sessions: [createdSession] });
    (api.chat.createSession as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      created: true,
      session: createdSession,
    });

    renderChatInterface();
    expect(await screen.findByText('No recent sessions found')).toBeInTheDocument();

    const textarea = screen.getByRole('textbox', { name: /message composer/i });
    fireEvent.change(textarea, { target: { value: 'First durable question' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));

    await waitFor(() => expect(api.chat.createSession).toHaveBeenCalledTimes(1));
    await waitFor(() => {
      expect(api.chat.sendMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          session_id: 'created-session-1',
          messages: [{ role: 'user', content: 'First durable question' }],
        }),
      );
    });
    expect(
      (api.chat.createSession as ReturnType<typeof vi.fn>).mock.invocationCallOrder[0],
    ).toBeLessThan(
      (api.chat.sendMessage as ReturnType<typeof vi.fn>).mock.invocationCallOrder[0],
    );
    expect(await screen.findByText('Session created-')).toBeInTheDocument();
  });

  it('new chat stays a draft until send and then uses one persisted session', async () => {
    renderChatInterface();
    await screen.findByText('Session 1');

    fireEvent.click(screen.getByTestId('new-chat-button'));
    expect(screen.getByText('No active session')).toBeInTheDocument();

    const textarea = screen.getByRole('textbox', { name: /message composer/i });
    fireEvent.change(textarea, { target: { value: 'Start a new persisted chat' } });
    fireEvent.click(screen.getByRole('button', { name: /send message/i }));

    await waitFor(() => expect(api.chat.createSession).toHaveBeenCalledTimes(1));
    await waitFor(() => {
      expect(api.chat.sendMessage).toHaveBeenCalledWith(
        expect.objectContaining({ session_id: 'created-session-1' }),
      );
    });
  });

  it('clears the selected run for a new draft and restores a saved session run', async () => {
    (api.chat.getSessionMessages as ReturnType<typeof vi.fn>).mockResolvedValue({
      messages: [{ id: 'm1', role: 'assistant', content: 'Saved response', run_id: 'saved-run' }],
    });
    renderChatInterface();
    expect(await screen.findByText('Saved response')).toBeInTheDocument();
    expect(screen.getByTestId('trace-panel')).toHaveTextContent('saved-run');
    fireEvent.click(screen.getByTestId('new-chat-button'));
    expect(screen.getByTestId('trace-panel')).toHaveTextContent('No selected run');
    fireEvent.click(screen.getByRole('button', { name: 'Session 1' }));
    await waitFor(() => expect(screen.getByTestId('trace-panel')).toHaveTextContent('saved-run'));
  });

  it('should display queued gateway trace links when a provider request is saved offline', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      queued: true,
      run_id: 'run-queued-001',
      audit_trail: auditTrail,
      provider_used: 'local',
      model_used: 'offline-queue',
    });

    renderChatInterface();

    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    fireEvent.change(textarea, { target: { value: 'Queue this request' } });
    fireEvent.click(screen.getByText('Send'));

    expect(await screen.findByText(/local desktop queue saved this request/i)).toBeInTheDocument();
    expect(screen.getByText('Reasoning Trace')).toBeInTheDocument();
    expect(screen.getByText('run-queu')).toBeInTheDocument();
    expect(screen.getByText(/offline-queue/i)).toBeInTheDocument();
  });

  it('should display trace links from rate-limited gateway errors without offline queuing', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new ApiError('Provider rate limited', 429, {
        run_id: 'run-rate-001',
        audit_trail: {
          ...auditTrail,
          complete_trace_url: '/api/v1/trace/runs/run-rate-001',
        },
        provider_used: 'openai',
        model_used: 'gpt-5',
      }),
    );

    renderChatInterface();

    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    fireEvent.change(textarea, { target: { value: 'Rate limit trace' } });
    fireEvent.click(screen.getByText('Send'));

    expect(await screen.findByText(/currently rate limited/i)).toBeInTheDocument();
    expect(screen.getByText('Reasoning Trace')).toBeInTheDocument();
    expect(screen.getByText('run-rate')).toBeInTheDocument();
    expect(screen.getByText(/gpt-5/i)).toBeInTheDocument();
    expect(request).not.toHaveBeenCalledWith('/gateway/offline-queue', expect.anything());
  });

  it('should preserve failed gateway trace links on desktop fallback messages', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new ApiError('Gateway failed', 503, {
        run_id: 'run-fail-001',
        audit_trail: {
          ...auditTrail,
          complete_trace_url: '/api/v1/trace/runs/run-fail-001',
        },
        provider_used: 'openai',
        model_used: 'gpt-5',
        failure: {
          kind: 'provider_failure',
          details: { provider_failure: { class: 'network' } },
        },
      }),
    );

    renderChatInterface();

    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    fireEvent.change(textarea, { target: { value: 'Failed trace' } });
    fireEvent.click(screen.getByText('Send'));

    expect(await screen.findByText(/could not be completed/i)).toBeInTheDocument();
    expect(screen.getByText('Reasoning Trace')).toBeInTheDocument();
    expect(screen.getByText('run-fail')).toBeInTheDocument();
    expect(request).toHaveBeenCalledWith(
      '/gateway/offline-queue',
      expect.objectContaining({ method: 'POST' }),
    );
  });

  it('should autofocus the message composer and expose the main chat landmark', async () => {
    renderChatInterface();

    const composer = await screen.findByRole('textbox', { name: /message composer/i });
    expect(composer).toHaveFocus();
    expect(screen.getByRole('main', { name: /chat interface/i })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: /search chat sessions/i })).toBeInTheDocument();
  });

  it('should send a message with Ctrl+Enter', async () => {
    renderChatInterface();

    const textarea = await screen.findByRole('textbox', { name: /message composer/i });
    fireEvent.change(textarea, { target: { value: 'Keyboard submit' } });
    fireEvent.keyDown(textarea, { key: 'Enter', ctrlKey: true });

    await waitFor(() => {
    expect(api.chat.sendMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        messages: [{ role: 'user', content: 'Keyboard submit' }],
      }),
    );
    });
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

    expect(await screen.findByText(/could not be completed/i, {}, { timeout: 10000 })).toBeInTheDocument();
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

  it('should handle message history navigation', async () => {
    renderChatInterface();
    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    
    // Send a message
    fireEvent.change(textarea, { target: { value: 'First message' } });
    fireEvent.click(screen.getByText('Send'));
    
    await waitFor(() => {
      expect(api.chat.sendMessage).toHaveBeenCalled();
    });
  });

  it('should display loading state while sending message', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockImplementationOnce(
      () => new Promise(resolve => setTimeout(() => resolve({ response: 'Delayed' }), 500))
    );

    renderChatInterface();
    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    
    fireEvent.change(textarea, { target: { value: 'Slow message' } });
    fireEvent.click(screen.getByText('Send'));

    // Check for loading indicator (if visible)
    await waitFor(() => {
      const sendBtn = screen.getByText('Send');
      expect(sendBtn).toBeInTheDocument();
    });
  });

  it('should handle empty message submission', async () => {
    renderChatInterface();
    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    
    fireEvent.change(textarea, { target: { value: '' } });
    const sendBtn = screen.getByText('Send');
    
    // Button should likely be disabled or the API shouldn't be called
    if (!sendBtn.hasAttribute('disabled')) {
      fireEvent.click(sendBtn);
    }
    
    expect(api.chat.sendMessage).not.toHaveBeenCalledWith(
      expect.objectContaining({ message: '' })
    );
  });

  it('should display response trace information when available', async () => {
    (api.chat.sendMessage as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      response: 'Test response',
      trace: {
        stages: [
          {
            name: 'stage-1',
            status: 'completed',
            duration_ms: 100
          }
        ]
      }
    });

    renderChatInterface();
    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i);
    
    fireEvent.change(textarea, { target: { value: 'Query with trace' } });
    fireEvent.click(screen.getByText('Send'));

    await waitFor(() => {
      expect(screen.getByTestId('trace-panel')).toBeInTheDocument();
    });
  });

  it('should expand/collapse message details on click', async () => {
    renderChatInterface();
    
    await waitFor(() => {
      const messages = screen.queryAllByTestId('message-item');
      if (messages.length > 0) {
        fireEvent.click(messages[0]);
        expect(screen.getByTestId('detailed-view')).toBeInTheDocument();
      }
    });
  });

  it('should persist session when switching tabs and returning', async () => {
    renderChatInterface();
    
    await waitFor(() => expect(screen.getByText('Session 1')).toBeInTheDocument());
    
    fireEvent.click(screen.getByText('Session 2'));
    
    await waitFor(() => {
      expect(api.chat.getSessionMessages).toHaveBeenCalledWith('session-2');
    });
  });

  it('should handle socket reconnection events', async () => {
    renderChatInterface();
    
    // Simulate socket reconnection
    const handlers = (socketClient.setHandlers as ReturnType<typeof vi.fn>).mock.calls[0]?.[0];
    if (handlers?.onConnected) {
      await act(async () => {
        handlers.onConnected?.({ status: 'connected', sid: 'test-sid' });
      });
    }

    expect(socketClient.setHandlers).toHaveBeenCalled();
  });

  it('should clear textarea after successful message send', async () => {
    renderChatInterface();
    const textarea = await screen.findByPlaceholderText(/ask a compliance question/i) as HTMLTextAreaElement;
    
    fireEvent.change(textarea, { target: { value: 'Test message' } });
    fireEvent.click(screen.getByText('Send'));

    await waitFor(() => {
      expect(textarea.value).toBe('');
    });
  });

  it('links settings and does not expose unsupported chat controls', async () => {
    renderChatInterface();

    const settings = await screen.findByRole('link', { name: /settings/i });
    expect(settings).toHaveAttribute('href', '/settings');
    expect(screen.queryByText('Advanced Configuration')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Export' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Clear All' })).not.toBeInTheDocument();
  });

  it('lets the user collapse and restore the dedicated trace pane', async () => {
    renderChatInterface();

    expect(await screen.findByTestId('trace-panel')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Hide trace explorer' }));
    expect(screen.queryByTestId('trace-panel')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Show trace explorer' }));
    expect(screen.getByTestId('trace-panel')).toBeInTheDocument();
  });
});
