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

  it('renders named nested canonical refinement receipt details from the trace stage', async () => {
    searchParamGetMock.mockImplementation((key: string) => (key === 'id' ? 'trace-refinement' : null));
    getBundleMock.mockResolvedValueOnce({
      run_id: 'trace-refinement',
      status: 'completed',
      run: { run_id: 'trace-refinement', status: 'completed', created_at: '2026-08-18T10:00:00Z' },
      stages: [
        {
          stage_id: 'refinement-stage',
          run_id: 'trace-refinement',
          name: 'refinement_1',
          stage_type: 'step',
          step_index: 1,
          status: 'completed',
          outputs: {
            refinement: {
              schema_version: 'dle.canonical-refinement-result.v1',
              registry_version: '2026.08.08-rw12.1',
              status: 'completed',
              step_count: 12,
              step_status_counts: { executed: 1, skipped: 11 },
              rewrite_authorized: true,
              provider_subcalls_used: 0,
              max_provider_rewrites: 1,
              blocked_by_step: null,
              rewrite_constraints: ['retain citations'],
              steps: [
                {
                  step: 1,
                  step_id: 'claim_inventory',
                  name: 'Claim inventory',
                  status: 'executed',
                  reason: 'Claims were inventoried.',
                  selected_ka_ids: ['KA-018'],
                  executed_ka_ids: ['KA-018'],
                  reused_ka_ids: [],
                  findings: [{ kind: 'claim' }],
                  constraints: ['retain citations'],
                  effects: [],
                },
              ],
            },
          },
        },
      ],
      personas: [],
      axes: null,
      evidence_sources: [],
      evidence: [],
      ka_invocations: [],
      kas: [],
      policy_decisions: [],
      memory_events: [],
      metrics: { stage_count: 1 },
    });

    render(<TraceDetailPage />);

    expect(await screen.findByText('12-Step Refinement Receipt')).toBeInTheDocument();
    expect(screen.getByText(/2026\.08\.08-rw12\.1; 12 recorded steps/)).toBeInTheDocument();
    expect(screen.getByText('Claim inventory')).toBeInTheDocument();
    expect(screen.getByText('claim_inventory')).toBeInTheDocument();
    expect(screen.getByText('Claims were inventoried.')).toBeInTheDocument();
    expect(screen.getByText(/Selected KAs: KA-018/)).toBeInTheDocument();
    expect(screen.getByText(/Executed KAs: KA-018/)).toBeInTheDocument();
    expect(screen.getByText('Authorized')).toBeInTheDocument();
  });

  it('renders a not-needed refinement decision even when no refinement stage exists', async () => {
    searchParamGetMock.mockImplementation((key: string) => (key === 'id' ? 'trace-no-refinement' : null));
    getBundleMock.mockResolvedValue({
      run_id: 'trace-no-refinement',
      status: 'completed',
      run: {
        run_id: 'trace-no-refinement',
        status: 'completed',
        created_at: '2026-08-18T10:00:00Z',
        data_snapshot: {
          refinement_disposition: {
            schema_version: 'dle.refinement-disposition.v1',
            status: 'not_needed',
            reason: 'measured_candidate_met_release_gate',
            enabled: true,
            measurement_status: 'measured',
            convergence_action: 'finalize',
            workflow_status: null,
            step_count: 0,
            rewrite_performed: false,
          },
        },
      },
      stages: [],
      frost_layers: [],
      personas: [],
      persona_positions: [],
      evidence_sources: [],
      evidence: [],
      ka_invocations: [],
      kas: [],
      axes: null,
      coordinate: null,
      policy_decisions: [],
      memory_events: [],
      metrics: {},
      export_url: '/trace/export',
    });

    render(<TraceDetailPage />);

    expect(await screen.findByText('Refinement decision')).toBeInTheDocument();
    expect(screen.getByText('Not needed')).toBeInTheDocument();
    expect(screen.getByText(/measured candidate met the release gate/i)).toBeInTheDocument();
  });
});
