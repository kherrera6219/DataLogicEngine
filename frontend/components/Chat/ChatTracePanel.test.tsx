import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatTracePanel } from './ChatTracePanel';
import * as apiModule from '@/lib/api';
import type { TraceBundle } from '@/lib/api/types';
import { useTraceStream } from '@/hooks/useTraceStream';

// Mock the API module
vi.mock('@/lib/api', () => ({
  api: {
    trace: {
      getBundle: vi.fn(),
      export: vi.fn(),
    },
  },
}));

// Mock the useTraceStream hook
vi.mock('@/hooks/useTraceStream', () => ({
  useTraceStream: vi.fn(() => ({ layers: [] })),
}));

const mockTraceBundle: TraceBundle = {
  run_id: 'test-run-123',
  status: 'completed',
  run: {
    run_id: 'test-run-123',
    status: 'completed',
    created_at: null,
    data_snapshot: {
      confidence_measurement: {
        formula_version: 'dle-confidence.v1',
        value: null,
        status: 'not_measured',
        explanation: 'Required provenance inputs were unavailable.',
      },
    },
  },
  frost_layers: [],
  stages: [],
  evidence_sources: [],
  evidence: [],
  claims: [],
  persona_positions: [],
  personas: [],
  ka_invocations: [],
  kas: [],
  coordinate: null,
  axes: null,
  policy_decisions: [],
  memory_events: [],
  metrics: { total_duration_ms: 1000, confidence: null },
  export_url: '/api/v1/trace/runs/test-run-123/export',
};

describe('ChatTracePanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render nothing when no runId and no auditTrail', () => {
    const { container } = render(<ChatTracePanel />);
    expect(container.firstChild).toBeNull();
  });

  it('should render with runId', () => {
    render(<ChatTracePanel runId="test-run-123" />);
    expect(screen.getByText(/Reasoning Trace/i)).toBeInTheDocument();
  });

  it('should load bundle on expand', async () => {
    const mockGetBundle = vi.mocked(apiModule.api.trace.getBundle);
    mockGetBundle.mockResolvedValue(mockTraceBundle);

    render(<ChatTracePanel runId="test-run-123" />);
    const expandButton = screen.getByRole('button', { name: /Reasoning Trace/i });
    
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(mockGetBundle).toHaveBeenCalledWith('test-run-123');
    });
    expect(screen.getByText('Not measured')).toBeInTheDocument();
    expect(screen.getByText(/Required provenance inputs were unavailable/)).toBeInTheDocument();
  });

  it('should handle error loading bundle', async () => {
    const mockGetBundle = vi.mocked(apiModule.api.trace.getBundle);
    mockGetBundle.mockRejectedValue(new Error('Network error'));

    render(<ChatTracePanel runId="test-run-123" />);
    const expandButton = screen.getByRole('button', { name: /Reasoning Trace/i });
    
    fireEvent.click(expandButton);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('should export trace bundle', async () => {
    const mockGetBundle = vi.mocked(apiModule.api.trace.getBundle);
    mockGetBundle.mockResolvedValue(mockTraceBundle);
    
    const mockExport = vi.mocked(apiModule.api.trace.export);
    mockExport.mockResolvedValue(JSON.stringify(mockTraceBundle));

    const createObjectURLSpyOn = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url');
    const revokeSpy = vi.spyOn(URL, 'revokeObjectURL');

    render(<ChatTracePanel runId="test-run-123" />);
    const expandButton = screen.getByRole('button', { name: /Reasoning Trace/i });
    
    fireEvent.click(expandButton);

    // Wait for the bundle to load
    await waitFor(() => {
      expect(mockGetBundle).toHaveBeenCalledWith('test-run-123');
    });

    // Now wait for the export button to appear
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Export/i })).toBeInTheDocument();
    });

    const exportButton = screen.getByRole('button', { name: /Export/i });
    fireEvent.click(exportButton);

    // Verify export was called
    await waitFor(() => {
      expect(mockExport).toHaveBeenCalledWith('test-run-123');
    });
    
    createObjectURLSpyOn.mockRestore();
    revokeSpy.mockRestore();
  });

  it('should derive runId from auditTrail complete_trace_url', () => {
    const auditTrail = {
      complete_trace_url: '/runs/derived-run-id/trace',
    };

    render(<ChatTracePanel auditTrail={auditTrail as any} />);
    expect(screen.getByText(/Reasoning Trace/i)).toBeInTheDocument();
  });

  it('renders running stage and stream detail with score normalization', async () => {
    vi.mocked(useTraceStream).mockReturnValue({
      layers: [
        { stage_id: 'live-1', layer_index: 7, name: 'Live analysis', status: 'running' },
        { stage_id: '', layer_index: 0, name: '', status: '' },
      ],
    } as ReturnType<typeof useTraceStream>);
    vi.mocked(apiModule.api.trace.getBundle).mockReset().mockResolvedValue({
      ...mockTraceBundle,
      status: 'running',
      metrics: { confidence: 0.75, stage_count: 4, total_duration_ms: 10 },
      personas: [{ id: 'persona-1' }],
      evidence_sources: [{ id: 'source-1' }, { id: 'source-2' }],
      frost_layers: [
        { stage_id: 'stage-1', layer_index: 2, name: 'Evidence', status: 'completed' },
        { stage_id: 'stage-2', layer_index: 0, name: 'Synthesis', status: 'running' },
      ],
      run: { ...mockTraceBundle.run, data_snapshot: { confidence_measurement: {} } },
    } as TraceBundle);

    render(<ChatTracePanel runId="running-run" auditTrail={{ decision_path: '/api/v1/trace/runs/running-run' } as any} />);
    fireEvent.click(screen.getByRole('button', { name: /Reasoning Trace/i }));
    expect(await screen.findByText('75.0%')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('L2 Evidence')).toBeInTheDocument();
    expect(screen.getByText('Synthesis')).toBeInTheDocument();
    expect(screen.getByText('L7 Live analysis')).toBeInTheDocument();
    expect(screen.getByText('Trace update')).toBeInTheDocument();
    expect(screen.getByText('live')).toBeInTheDocument();
    expect(screen.getByText(/Versioned evidence-support measurement recorded/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Open details' })).toHaveAttribute('href', '/runs/view?id=running-run');
  });

  it('handles non-Error loads and object or empty exports', async () => {
    vi.mocked(useTraceStream).mockReturnValue({ layers: [] } as ReturnType<typeof useTraceStream>);
    vi.mocked(apiModule.api.trace.getBundle).mockRejectedValueOnce('trace unavailable');
    const view = render(<ChatTracePanel auditTrail={{ complete_trace_url: '/not-a-run-url' } as any} />);
    fireEvent.click(screen.getByRole('button', { name: /Reasoning Trace/i }));
    expect(apiModule.api.trace.getBundle).not.toHaveBeenCalled();

    view.unmount();
    vi.mocked(apiModule.api.trace.getBundle).mockReset().mockResolvedValue({
      ...mockTraceBundle,
      metrics: { confidence: 82, total_duration_ms: 5 },
    });
    vi.mocked(apiModule.api.trace.export).mockResolvedValueOnce({ run_id: 'object-export' } as any).mockResolvedValueOnce('');
    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:object-export');
    vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    render(<ChatTracePanel runId="object-run" />);
    fireEvent.click(screen.getByRole('button', { name: /Reasoning Trace/i }));
    expect(await screen.findByText('Not measured')).toBeInTheDocument();
    expect(screen.getByText('Required provenance inputs were unavailable.')).toBeInTheDocument();
    const exportButton = screen.getByRole('button', { name: /Export/i });
    fireEvent.click(exportButton);
    await waitFor(() => expect(URL.createObjectURL).toHaveBeenCalled());
    fireEvent.click(exportButton);
    await waitFor(() => expect(apiModule.api.trace.export).toHaveBeenCalledTimes(2));
  });
});
