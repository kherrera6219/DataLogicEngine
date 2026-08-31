import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

vi.mock('@/hooks/useTraceStream', () => ({
  useTraceStream: () => ({ layers: [], connected: false, error: null }),
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
    Object.defineProperty(window, 'electronAPI', { configurable: true, value: undefined });

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
    expect(screen.getByText('Evidence support')).toBeInTheDocument();
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

  it('renders reasoning, persona, score, stage-status, and fallback formatting branches', async () => {
    listMock.mockResolvedValueOnce([
      {
        run_id: 'completed-run',
        status: 'completed',
        scores: { confidence: 87, entropy: Number.NaN },
      },
    ]);
    getStagesMock.mockResolvedValueOnce({
      stages: [
        { stage_id: 'pass', name: 'Passed', status: 'completed', timing: { duration_ms: 1 } },
        { stage_id: 'warn', name: 'Warning', status: 'warn' },
        { stage_id: 'fail', name: 'Failure', status: 'semantic_failure', timing: {} },
        { stage_id: 'unknown', name: 'Unknown' },
      ],
    });
    requestMock.mockImplementation((path: string) => {
      if (path === '/trace/live-progress') {
        return Promise.resolve({
          active_run_id: 'completed-run',
          status: 'completed',
          current_layer: null,
          layer_name: null,
          kas_running: [
            { ka_id: 'KA-001', ka_name: 'Named KA', status: 'running' },
            { ka_id: 'KA-002', status: 'blocked' },
          ],
          confidence_so_far: null,
          persona_confidences: [
            { persona: 'knowledge', confidence: -1 },
            { persona: 'sector', confidence: 150 },
            { persona: 'regulatory', confidence: 0.75 },
          ],
          frost_snapshot_count: 0,
        });
      }
      if (path.startsWith('/trace/ka-execution-feed')) {
        return Promise.resolve({
          items: [
            { id: 1, uid: '', ka_id: '', status: '', execution_time_ms: -4, started_at: '' },
            { id: 2, ka_id: 'KA-002', status: 'unavailable', execution_time_ms: Number.POSITIVE_INFINITY },
          ],
        });
      }
      return Promise.resolve(null);
    });
    render(<LiveTracePanel />);
    expect(await screen.findByText('COMPLETED')).toBeInTheDocument();
    expect(screen.getByText('No captured input text for this run.')).toBeInTheDocument();
    expect(screen.getByText('Created: Unknown')).toBeInTheDocument();
    expect(screen.getByText('No active reasoning layer')).toBeInTheDocument();
    expect(screen.getByText('Named KA')).toBeInTheDocument();
    expect(screen.getByText('0.0%')).toBeInTheDocument();
    expect(screen.getByText('100.0%')).toBeInTheDocument();
    expect(screen.getAllByText('--').length).toBeGreaterThan(0);
    expect(screen.getByText('unknown KA')).toBeInTheDocument();
    expect(screen.getByText('unknown (0ms)')).toBeInTheDocument();
    expect(screen.getByText('unavailable')).toBeInTheDocument();
  });

  it('uses desktop telemetry bridges and supports manual refresh', async () => {
    const progress = vi.fn().mockResolvedValue({
      active_run_id: 'run-1', status: 'running', current_layer: 7, layer_name: 'AGI',
      kas_running: [], confidence_so_far: 0.5, persona_confidences: [], frost_snapshot_count: 2,
    });
    const feed = vi.fn().mockResolvedValue({ items: [] });
    Object.defineProperty(window, 'electronAPI', {
      configurable: true,
      value: { getReasoningLayerProgress: progress, getKAExecutionFeed: feed },
    });
    render(<LiveTracePanel />);
    expect(await screen.findByText('AGI')).toBeInTheDocument();
    expect(progress).toHaveBeenCalled();
    expect(feed).toHaveBeenCalled();
    expect(requestMock).not.toHaveBeenCalledWith('/trace/live-progress');
    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => expect(listMock).toHaveBeenCalledTimes(2));
  });

  it('shows an explicit error when stage telemetry is unavailable', async () => {
    getStagesMock.mockRejectedValueOnce(new Error('stage unavailable'));
    requestMock.mockRejectedValue(new Error('telemetry unavailable'));
    render(<LiveTracePanel />);
    expect(await screen.findByText('stage unavailable')).toBeInTheDocument();
    expect(screen.queryByText('10%')).not.toBeInTheDocument();
  });

  it('does not disguise a trace listing failure as an empty idle result', async () => {
    listMock.mockRejectedValueOnce(new Error('startup race'));
    render(<LiveTracePanel />);
    expect(await screen.findByText('IDLE')).toBeInTheDocument();
    expect(screen.getByText('startup race')).toBeInTheDocument();
    expect(screen.queryByText(/No trace runs found yet/i)).not.toBeInTheDocument();
  });
});
