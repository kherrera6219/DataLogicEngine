import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import TraceDetailPage from './page';

const { getBundleMock, exportMock, searchParamGetMock } = vi.hoisted(() => ({
  getBundleMock: vi.fn(),
  exportMock: vi.fn(),
  searchParamGetMock: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  api: {
    trace: {
      getBundle: getBundleMock,
      export: exportMock,
    },
  },
}));

vi.mock('next/navigation', () => ({
  useSearchParams: () => ({
    get: searchParamGetMock,
  }),
}));

describe('TraceDetailPage', () => {
  beforeEach(() => {
    getBundleMock.mockReset();
    exportMock.mockReset();
    searchParamGetMock.mockReset();
  });

  it('renders partial trace bundles without invalid date output or crashes', async () => {
    searchParamGetMock.mockImplementation((key: string) => (key === 'trace' ? 'trace/1' : null));
    getBundleMock.mockResolvedValueOnce({
      run_id: 'trace/1',
      status: 'pass',
      run: {
        run_id: 'trace/1',
        status: 'pass',
        created_at: null,
        ka_id: null,
        scores: {
          confidence: null,
          bias_risk: null,
        },
      },
      stages: [
        {
          stage_id: 'stage-1',
          run_id: 'trace/1',
          name: 'Bootstrap',
          stage_type: 'layer',
          layer_index: 0,
          status: 'pass',
          start_time: null,
          outputs: { summary: 'ok' },
        },
      ],
      personas: [
        {
          persona_id: 'persona-1',
          run_id: 'trace/1',
          persona_type: 'analyst',
          persona_name: null,
          status: 'pass',
          confidence: null,
          draft: {},
        },
      ],
      axes: {
        vector_id: 'axis-1',
        run_id: 'trace/1',
        axes: null,
      },
      evidence_sources: [],
      evidence: [],
      ka_invocations: [],
      kas: [],
      policy_decisions: [],
      memory_events: [],
      metrics: {
        total_duration_ms: null,
        total_tokens_in: 0,
        total_tokens_out: 0,
        total_retrievals: null,
        stage_count: null,
        confidence: null,
        entropy: null,
      },
    });

    render(<TraceDetailPage />);

    expect(await screen.findByText('trace/1')).toBeInTheDocument();
    expect(getBundleMock).toHaveBeenCalledWith('trace/1');
    expect(screen.getByText('L0')).toBeInTheDocument();
    expect(screen.getByText(/Started: Unknown time/)).toBeInTheDocument();
    expect(screen.getAllByText('Unknown time').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('{"summary":"ok"}')).toBeInTheDocument();
    expect(screen.queryByText('Invalid Date')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: /Expert Analysis/i }));
    expect(screen.getAllByText('analyst')).toHaveLength(2);
    expect(screen.getByText('No draft recorded.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('tab', { name: /Coordinates/i }));
    expect(screen.getByText('No coordinate vector data found for this run.')).toBeInTheDocument();
  });

  it('surfaces bundle load failures instead of a generic missing trace state', async () => {
    searchParamGetMock.mockImplementation((key: string) => (key === 'id' ? 'trace-404' : null));
    getBundleMock.mockRejectedValueOnce(new Error('missing bundle'));

    render(<TraceDetailPage />);

    expect(await screen.findByText('missing bundle')).toBeInTheDocument();
    expect(screen.queryByText('Trace not found')).not.toBeInTheDocument();
  });
});
