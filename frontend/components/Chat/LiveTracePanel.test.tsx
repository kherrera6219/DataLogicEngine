import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LiveTracePanel } from './LiveTracePanel';

const { listMock, getStagesMock } = vi.hoisted(() => ({
  listMock: vi.fn(),
  getStagesMock: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  api: {
    trace: {
      list: listMock,
      getStages: getStagesMock,
    },
  },
  // The component also imports `request` for /trace/live-progress and
  // /trace/ka-execution-feed. Without it the named export is undefined and the
  // component's catch block silently drops to the empty state.
  request: vi.fn().mockResolvedValue(null),
}));

// Mock UI components
vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value }: { value: number }) => <div data-testid="progress" data-value={value} />
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}));

describe('LiveTracePanel', () => {
  beforeEach(() => {
    listMock.mockReset();
    getStagesMock.mockReset();

    listMock.mockResolvedValue([
      {
        run_id: 'run-1',
        status: 'running',
        created_at: '2026-02-08T12:00:00Z',
        input_message: 'How do we satisfy HIPAA controls?',
        scores: {
          confidence: 0.93,
          entropy: 0.08,
          bias_risk: 0.02,
        },
      },
    ]);

    getStagesMock.mockResolvedValue({
      stages: [
        { stage_id: 's1', name: 'TruthGate', status: 'pass', timing: { duration_ms: 120 } },
        { stage_id: 's2', name: 'Persona Analysis', status: 'running', timing: { duration_ms: 340 } },
      ],
    });
  });

  it('should render correct header and run status', async () => {
    render(<LiveTracePanel />);
    expect(screen.getByText('Live Trace')).toBeInTheDocument();
    await screen.findByText('RUNNING');
  });

  it('should render run message and confidence metrics', async () => {
    render(<LiveTracePanel />);
    await screen.findByText('Active Run');
    expect(screen.getByText(/How do we satisfy HIPAA controls\?/i)).toBeInTheDocument();
    expect(screen.getByText('Confidence')).toBeInTheDocument();
    expect(screen.getByText('93.0%')).toBeInTheDocument();
  });

  it('should render step progress', async () => {
    render(<LiveTracePanel />);
    const progress = await screen.findByTestId('progress');
    expect(progress).toBeInTheDocument();
    await waitFor(() => expect(progress).toHaveAttribute('data-value', '50'));
  });
});
