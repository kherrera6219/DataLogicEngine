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
      startLocal: vi.fn(),
    },
  },
}));

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
    vi.mocked(api.ingestion.startLocal).mockResolvedValue({
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

    render(<KnowledgeIngestionSettings />);
    await waitFor(() => expect(api.ingestion.supported).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText('Local path'), { target: { value: 'C:/corpus' } });
    fireEvent.click(screen.getByRole('button', { name: /start ingestion/i }));

    await waitFor(() => {
      expect(api.ingestion.startLocal).toHaveBeenCalledWith(
        expect.objectContaining({ path: 'C:/corpus', recursive: true })
      );
      expect(screen.getByText('Last ingestion')).toBeInTheDocument();
      expect(screen.getAllByText('1 files').length).toBeGreaterThan(0);
    });
    expect(toastMock).toHaveBeenCalledWith('Ingestion complete: 1 files, 2 chunks, 2 indexed', 'success');
  });
});
