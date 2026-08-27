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
    mockRequest.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === '/dataset/capture-settings') {
        const requested = options?.body
          ? JSON.parse(String(options.body)) as { enabled?: boolean }
          : null;
        return {
          enabled: options?.method === 'PUT' ? Boolean(requested?.enabled) : false,
          default: false,
          policy: 'export-only',
          redaction_enforced: true,
        };
      }
      return {
        status: 'active',
        total_trace_runs: 42,
        release_candidate_runs: 35,
        supported_types: ['sft', 'prm'],
        supported_formats: ['parquet', 'jsonl'],
        pyarrow_available: true,
        redaction_enforced: true,
        capture_enabled: false,
        capture_default: false,
        staged_capture_rows: 0,
        last_capture_at: null,
        policy: 'export-only',
      };
    });
  });

  it('renders title and is disabled by default', async () => {
    render(<DatasetExporterSettings />);

    expect(
      screen.getByText('Dataset preparation & export (no in-app trainer)')
    ).toBeInTheDocument();
    const exportToggle = screen.getByLabelText('Toggle dataset exporter');
    const captureToggle = screen.getByLabelText('Toggle runtime usage capture');
    expect(exportToggle).toBeInTheDocument();
    expect(exportToggle).not.toBeChecked();
    expect(captureToggle).not.toBeChecked();

    await waitFor(() => {
      expect(mockRequest).toHaveBeenCalledWith('/dataset/capture-settings');
    });
  });

  it('persists runtime capture through the owner API', async () => {
    render(<DatasetExporterSettings />);
    await waitFor(() => {
      expect(mockRequest).toHaveBeenCalledWith('/dataset/capture-settings');
    });

    fireEvent.click(screen.getByLabelText('Toggle runtime usage capture'));

    await waitFor(() => {
      expect(screen.getByText(/Runtime usage capture is on/i)).toBeInTheDocument();
    });
    const putCall = mockRequest.mock.calls.find(
      (call) => call[0] === '/dataset/capture-settings' && call[1]?.method === 'PUT'
    );
    expect(putCall).toBeDefined();
    expect(JSON.parse(putCall?.[1]?.body as string).enabled).toBe(true);
  });

  it('allows triggering a dataset export batch when enabled', async () => {
    render(<DatasetExporterSettings />);

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
