import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import DiagnosticsPage from './page';

const mocks = vi.hoisted(() => ({
  summary: vi.fn(),
  preview: vi.fn(),
  exportBundle: vi.fn(),
  mutate: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('swr', () => ({
  default: () => ({
    data: {
      schema_version: 'dle.diagnostics.v1',
      status: 'ok',
      runtime: {
        phase: 'ready',
        ready: true,
        services: { postgresql: { state: 'ready', safe_reason: null } },
      },
      requests: { total: 42, inflight: 1, uptime_seconds: 120 },
      logging: { schema_version: 'dle.log.v1', format: 'json', redaction: 'best_effort_redacted' },
      external_telemetry: { opted_in: false, enabled: false, provider: 'none', state_code: null },
      support_bundle: {
        schema_version: 'dle.support-bundle.v1',
        content_policy: 'redacted_diagnostics_only',
        user_content_included: false,
        generic_reports_included: false,
        preview_required: true,
        encryption_available_via_cli: true,
      },
      correlation_id: 'corr-diagnostics-1',
      timestamp: '2026-07-15T00:00:00Z',
    },
    error: null,
    isLoading: false,
    mutate: mocks.mutate,
  }),
}));

vi.mock('@/lib/api', () => ({
  api: {
    diagnostics: {
      summary: mocks.summary,
      previewSupportBundle: mocks.preview,
      exportSupportBundle: mocks.exportBundle,
    },
  },
}));

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: mocks.toast }),
}));

vi.mock('@/components/ConfirmationDialog', () => ({
  ConfirmationDialog: ({
    open,
    onConfirm,
  }: {
    open: boolean;
    onConfirm: () => void;
  }) => open ? <button onClick={onConfirm}>Confirm support export</button> : null,
}));

describe('DiagnosticsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.preview.mockResolvedValue({
      schema_version: 'dle.support-bundle.v1',
      archive_created: false,
      content_policy: 'redacted_diagnostics_only',
      user_content_included: false,
      preview_fingerprint: 'a'.repeat(64),
      files: [
        {
          path: 'manifest.json',
          size_bytes: 512,
          sha256: 'b'.repeat(64),
          classification: 'redacted_diagnostics',
        },
      ],
    });
    mocks.exportBundle.mockResolvedValue({
      success: true,
      artifact_name: 'support_bundle.zip',
      sidecar_name: 'support_bundle.zip.sha256',
      sha256: 'c'.repeat(64),
      size_bytes: 2048,
      encrypted: false,
      location: 'application_support_bundles_directory',
      timestamp: '2026-07-15T00:01:00Z',
    });
  });

  it('shows truthful local runtime and privacy state', () => {
    render(<DiagnosticsPage />);

    expect(screen.getByRole('heading', { name: 'System Diagnostics' })).toBeInTheDocument();
    expect(screen.getByText('corr-diagnostics-1')).toBeInTheDocument();
    expect(screen.getByText('postgresql')).toBeInTheDocument();
    expect(screen.getByText('External telemetry')).toBeInTheDocument();
    expect(screen.getAllByText('Excluded')).toHaveLength(2);
  });

  it('requires preview before confirmed local bundle generation', async () => {
    render(<DiagnosticsPage />);

    const generateButton = screen.getByRole('button', { name: /generate local bundle/i });
    expect(generateButton).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: /preview bundle/i }));
    await waitFor(() => expect(mocks.preview).toHaveBeenCalledTimes(1));
    expect(await screen.findByText('manifest.json')).toBeInTheDocument();
    expect(generateButton).toBeEnabled();

    fireEvent.click(generateButton);
    fireEvent.click(screen.getByRole('button', { name: /confirm support export/i }));

    await waitFor(() => {
      expect(mocks.exportBundle).toHaveBeenCalledWith('a'.repeat(64));
    });
    expect(await screen.findByText('Bundle generated locally')).toBeInTheDocument();
    expect(screen.getByText(/support_bundle\.zip/)).toBeInTheDocument();
  });

  it('refreshes the summary on request', () => {
    render(<DiagnosticsPage />);
    fireEvent.click(screen.getByRole('button', { name: /refresh diagnostics/i }));
    expect(mocks.mutate).toHaveBeenCalledTimes(1);
  });
});
