import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatTracePanel } from './ChatTracePanel';
import * as apiModule from '@/lib/api';
import type { TraceBundle } from '@/lib/api/types';

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
  stages: [],
  metrics: { duration_ms: 1000, token_count: 100 },
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
});
