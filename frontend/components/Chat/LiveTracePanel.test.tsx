import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LiveTracePanel } from './LiveTracePanel';

const { listMock, getStagesMock, requestMock } = vi.hoisted(() => ({
  listMock: vi.fn(),
  getStagesMock: vi.fn(),
  requestMock: vi.fn(),
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
  request: requestMock,
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
    requestMock.mockReset();
    requestMock.mockResolvedValue(null);

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

  it('renders KA execution feed when no trace run exists', async () => {
    listMock.mockResolvedValueOnce([]);
    requestMock.mockImplementation((path: string) => {
      if (path.startsWith('/trace/ka-execution-feed')) {
        return Promise.resolve({
          items: [
            {
              id: 7,
              uid: 'exec-7',
              ka_id: 'KA-042',
              status: 'completed',
              execution_time_ms: 87,
              started_at: '2026-07-04T08:15:00Z',
              completed_at: '2026-07-04T08:15:01Z',
            },
          ],
          limit: 20,
          updated_at: '2026-07-04T08:16:00Z',
        });
      }
      return Promise.resolve(null);
    });

    render(<LiveTracePanel />);

    expect(await screen.findByText(/No trace runs found yet/i)).toBeInTheDocument();
    expect(await screen.findByText('KA Execution Feed')).toBeInTheDocument();
    expect(screen.getByText('KA-042')).toBeInTheDocument();
    expect(screen.getByText('completed (87ms)')).toBeInTheDocument();
    expect(getStagesMock).not.toHaveBeenCalled();
  });
});
