import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import DatasetExporterSettings from './DatasetExporterSettings';

const mockRequest = vi.fn();

vi.mock('@/lib/api', () => ({
  request: (...args: any[]) => mockRequest(...args),
}));

describe('DatasetExporterSettings Component', () => {
  beforeEach(() => {
    mockRequest.mockReset();
    mockRequest.mockResolvedValue({
      status: 'active',
      total_trace_runs: 42,
      release_candidate_runs: 35,
      supported_types: ['sft', 'prm'],
      supported_formats: ['parquet', 'jsonl'],
      pyarrow_available: true,
      redaction_enforced: true,
    });
  });

  it('renders title and is disabled by default', () => {
    render(<DatasetExporterSettings />);

    expect(screen.getByText('Training Data Creation & Dataset Exporter')).toBeInTheDocument();
    const toggle = screen.getByLabelText('Toggle dataset exporter');
    expect(toggle).toBeInTheDocument();
    expect(toggle).not.toBeChecked();

    expect(mockRequest).not.toHaveBeenCalled();
  });

  it('allows triggering a dataset export batch when enabled', async () => {
    render(<DatasetExporterSettings />);

    // Enable feature via toggle
    const toggle = screen.getByLabelText('Toggle dataset exporter');
    fireEvent.click(toggle);

    await waitFor(() => {
      expect(screen.getByText('35')).toBeInTheDocument();
    });

    mockRequest.mockResolvedValueOnce({
      status: 'success',
      exported_rows: 35,
      artifact_name: 'sft-export.parquet',
    });

    const exportBtn = screen.getByRole('button', { name: /Trigger Dataset Export Batch/i });
    fireEvent.click(exportBtn);

    await waitFor(() => {
      expect(screen.getByText(/Created sft-export.parquet with 35 rows/i)).toBeInTheDocument();
    });
    const exportCall = mockRequest.mock.calls.find((call) => call[0] === '/dataset/export');
    expect(exportCall).toBeDefined();
    const requestBody = JSON.parse(exportCall?.[1]?.body as string);
    expect(requestBody).not.toHaveProperty('output_path');
    expect(requestBody.export_type).toBe('sft');
  });

  it('hides controls when disabled', async () => {
    render(<DatasetExporterSettings />);

    expect(screen.queryByRole('button', { name: /Trigger Dataset Export Batch/i })).not.toBeInTheDocument();
  });

  it('keeps privacy redaction non-bypassable', async () => {
    render(<DatasetExporterSettings />);
    fireEvent.click(screen.getByLabelText('Toggle dataset exporter'));

    expect(await screen.findByText('Enforced')).toBeInTheDocument();
    expect(screen.queryByLabelText('Toggle secret redaction')).not.toBeInTheDocument();
    expect(screen.queryByRole('option', { name: /DPO/i })).not.toBeInTheDocument();
  });
});
