import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MessageBubble } from './MessageBubble';
import { Message } from '@/lib/api';

// Mock copy button since it might have browser deps
vi.mock('@/components/ui/copy-button', () => ({
  CopyButton: () => <button>Copy</button>
}));

vi.mock('@/hooks/useTraceStream', () => ({
  useTraceStream: () => ({ layers: [], connected: false, error: null })
}));

vi.mock('@/lib/api', () => ({
  api: {
    trace: {
      getBundle: vi.fn().mockResolvedValue({
        run_id: 'run-1',
        status: 'completed',
        metrics: { confidence: 0.91, stage_count: 1 },
        frost_layers: [{ stage_id: 'stage-1', name: 'L1 Context', status: 'completed', layer_index: 1 }],
        stages: [],
        personas: [{ persona_id: 'persona-1' }],
        evidence_sources: [{ evidence_id: 'ev-1' }],
        export_url: '/api/v1/trace/runs/run-1/export',
      }),
      export: vi.fn().mockResolvedValue('{}')
    }
  }
}));

describe('MessageBubble', () => {
  it('should render user message correctly', () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'Hello AI',
      timestamp: new Date().toISOString()
    };
    render(<MessageBubble message={message as Message} />);
    expect(screen.getByText('Hello AI')).toBeInTheDocument();
    // User avatar check (indirectly via class or icon existence, difficult to test exact icon without more mocks, but text content is sufficient for now)
  });

  it('should render assistant message correctly', () => {
    const message = {
      id: '2',
      role: 'assistant' as const,
      content: 'Hello Human',
      timestamp: new Date().toISOString()
    };
    render(<MessageBubble message={message as Message} />);
    expect(screen.getByText('Hello Human')).toBeInTheDocument();
  });

  it('should show thinking state', () => {
    const message = {
      id: '3',
      role: 'assistant' as const,
      content: 'Thinking...',
      timestamp: new Date().toISOString()
    };
    render(<MessageBubble message={message as Message} isThinking={true} />);
    expect(screen.getByText('Reasoning Logic active')).toBeInTheDocument();
  });

  it('should render an expandable trace panel for assistant messages with a run id', async () => {
    const message = {
      id: '4',
      role: 'assistant' as const,
      content: 'Traceable response',
      timestamp: new Date().toISOString(),
      runId: 'run-1',
      auditTrail: {
        decision_path: '/api/v1/trace/runs/run-1',
        complete_trace_url: '/api/v1/trace/runs/run-1/bundle',
        download_url: '/api/v1/trace/runs/run-1/export',
      },
    };

    render(<MessageBubble message={message as Message} />);
    expect(screen.getByText('Reasoning Trace')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Reasoning Trace'));

    await waitFor(() => {
      expect(screen.getByText('91.0%')).toBeInTheDocument();
      expect(screen.getByText('L1 L1 Context')).toBeInTheDocument();
    });
  });
});
