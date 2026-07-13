import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import KnowledgeIngestionSettings from './KnowledgeIngestionSettings';
import { api } from '@/lib/api';

const toastMock = vi.fn();

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: toastMock }),
}));

vi.mock('@/lib/api', () => ({
  api: {
    ingestion: {
      supported: vi.fn(),
      history: vi.fn(),
      status: vi.fn(),
    },
  },
}));

function installElectronApi(overrides: Record<string, unknown> = {}) {
  Object.defineProperty(window, 'electronAPI', {
    configurable: true,
    value: {
      chooseIngestionSource: vi.fn().mockResolvedValue({
        token: 'ingestion-token',
        display_name: 'corpus',
        expires_at: '2026-07-13T01:00:00Z',
      }),
      runLocalIngestion: vi.fn(),
      ...overrides,
    },
  });
}

describe('KnowledgeIngestionSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    toastMock.mockReset();
    vi.mocked(api.ingestion.supported).mockResolvedValue({
      extensions: ['.txt', '.md'],
      default_chunk_size: 1200,
      default_max_file_bytes: 10 * 1024 * 1024,
    });
    vi.mocked(api.ingestion.history).mockResolvedValue([]);
    installElectronApi();
  });

  it('loads supported types and empty history', async () => {
    render(<KnowledgeIngestionSettings />);

    await waitFor(() => {
      expect(screen.getByText('Local Knowledge Ingestion')).toBeInTheDocument();
      expect(screen.getByText('Supported: .txt, .md')).toBeInTheDocument();
      expect(screen.getByText('No ingestion runs recorded.')).toBeInTheDocument();
    });
  });

  it('starts ingestion and records the latest result', async () => {
    const runLocalIngestion = vi.fn().mockResolvedValue({
      ingestion_id: 'run-1',
      source: 'C:/corpus',
      files_scanned: 1,
      files_ingested: 1,
      files_rejected: 0,
      chunks_created: 2,
      chunks_indexed: 2,
      rejected_files: [],
      chunks: [],
      manifest_path: 'reports/ingestion/run-1.json',
    });
    installElectronApi({ runLocalIngestion });

    render(<KnowledgeIngestionSettings />);
    await waitFor(() => expect(api.ingestion.supported).toHaveBeenCalled());

    fireEvent.click(screen.getByRole('button', { name: /choose local ingestion source/i }));
    await waitFor(() => expect(screen.getByLabelText('Local path')).toHaveValue('corpus'));
    fireEvent.click(screen.getByRole('button', { name: /start local knowledge ingestion/i }));

    await waitFor(() => {
      expect(runLocalIngestion).toHaveBeenCalledWith(
        expect.objectContaining({ source_capability: 'ingestion-token', recursive: true, operation_id: expect.any(String) })
      );
      expect(screen.getByText('Last ingestion')).toBeInTheDocument();
      expect(screen.getAllByText('1 files').length).toBeGreaterThan(0);
    });
    expect(toastMock).toHaveBeenCalledWith('Ingestion complete: 1 files, 2 chunks, 2 indexed', 'success');
  });

  it('exposes accessible ingestion controls', async () => {
    render(<KnowledgeIngestionSettings />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /start local knowledge ingestion/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /choose local ingestion source/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /refresh ingestion history/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear local path/i })).toBeInTheDocument();
      expect(screen.getByRole('switch', { name: /recursive folder scan/i })).toBeInTheDocument();
      expect(screen.getByRole('switch', { name: /async mode/i })).toBeInTheDocument();
    });
  });
});
