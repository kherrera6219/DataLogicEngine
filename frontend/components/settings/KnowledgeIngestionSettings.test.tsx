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
      cancel: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      retry: vi.fn(),
      remove: vi.fn(),
      repair: vi.fn(),
      consistency: vi.fn(),
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
      default_max_total_bytes: 100 * 1024 * 1024,
      default_max_files: 1000,
      default_max_pages: 500,
      default_max_archive_entries: 10000,
      default_max_decompressed_bytes: 100 * 1024 * 1024,
      default_max_archive_depth: 1,
      default_parser_timeout_seconds: 60,
    });
    vi.mocked(api.ingestion.history).mockResolvedValue([]);
    vi.mocked(api.ingestion.consistency).mockResolvedValue({
      scanned_jobs: 0,
      consistent_jobs: 0,
      divergence_count: 0,
      jobs: [],
    });
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
      expect(screen.getByRole('button', { name: /scan corpus consistency/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /clear local path/i })).toBeInTheDocument();
      expect(screen.getByRole('switch', { name: /recursive folder scan/i })).toBeInTheDocument();
      expect(screen.getByRole('switch', { name: /async mode/i })).toBeInTheDocument();
    });
  });

  it('renders rich history and supports repair, retry, delete, refresh, and divergent consistency', async () => {
    vi.mocked(api.ingestion.history).mockResolvedValue([
      {
        ingestion_id: 'failed-run',
        source: 'C:/corpus',
        status: 'failed',
        files_scanned: 2,
        files_ingested: 1,
        files_rejected: 1,
        chunks_created: 2,
        chunks_indexed: 1,
        materializations_pending: 1,
        manifest_path: 'reports/failed.json',
        rejected_files: [{ path: 'bad.exe', reason: 'unsupported' }],
        files: [{
          relative_path: 'policy.pdf',
          status: 'indexed',
          parser_result: { status: 'parsed' },
          defense_result: { disposition: 'accepted' },
          object_status: 'stored',
          normalized_object_status: 'stored',
          vector_status: 'pending',
          graph_status: 'pending',
          embedding_revision: 'rev-1',
          last_retrieved_at: '2026-08-16T00:00:00Z',
          last_retrieval_trace_id: 'trace 1',
          source_revision: 'sha256:abc',
        }],
      } as any,
    ]);
    vi.mocked(api.ingestion.repair).mockResolvedValue({} as any);
    vi.mocked(api.ingestion.retry).mockResolvedValue({} as any);
    vi.mocked(api.ingestion.remove).mockResolvedValue({} as any);
    vi.mocked(api.ingestion.consistency).mockResolvedValue({
      scanned_jobs: 2,
      consistent_jobs: 1,
      divergence_count: 1,
      jobs: [],
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    render(<KnowledgeIngestionSettings />);
    expect(await screen.findByText('policy.pdf')).toBeInTheDocument();
    expect(screen.getByText('unsupported: bad.exe')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /view last answer trace/i })).toHaveAttribute('href', '/runs/view?id=trace%201');
    fireEvent.click(screen.getByRole('button', { name: /repair ingestion failed-run/i }));
    fireEvent.click(screen.getByRole('button', { name: /retry ingestion failed-run/i }));
    fireEvent.click(screen.getByRole('button', { name: /delete ingestion failed-run/i }));
    fireEvent.click(screen.getByRole('button', { name: /scan corpus consistency/i }));
    await waitFor(() => {
      expect(api.ingestion.repair).toHaveBeenCalledWith('failed-run');
      expect(api.ingestion.retry).toHaveBeenCalledWith('failed-run');
      expect(api.ingestion.remove).toHaveBeenCalledWith('failed-run');
      expect(screen.getByText(/1\/2 jobs consistent; 1 differences/i)).toBeInTheDocument();
    });
    expect(toastMock).toHaveBeenCalledWith('Corpus differences require attention.', 'error');
    fireEvent.click(screen.getByRole('button', { name: /refresh ingestion history/i }));
    await waitFor(() => expect(api.ingestion.supported).toHaveBeenCalledTimes(5));
  });

  it('cancels source deletion and reports consistent stores', async () => {
    vi.mocked(api.ingestion.history).mockResolvedValue([{
      ingestion_id: 'run-1', source: 'C:/corpus', status: 'completed', files_scanned: 1,
      files_ingested: 1, files_rejected: 0, chunks_created: 1, chunks_indexed: 1,
      rejected_files: [], chunks: [],
    } as any]);
    vi.spyOn(window, 'confirm').mockReturnValue(false);
    render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /delete ingestion run-1/i }));
    expect(api.ingestion.remove).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: /scan corpus consistency/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Corpus stores are consistent.', 'success'));
  });

  it('handles missing, cancelled, thrown Error, and non-Error source selection', async () => {
    Object.defineProperty(window, 'electronAPI', { configurable: true, value: undefined });
    const first = render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /choose local ingestion source/i }));
    expect(await screen.findByText(/available only in the desktop application/i)).toBeInTheDocument();
    first.unmount();

    installElectronApi({ chooseIngestionSource: vi.fn().mockResolvedValue(null) });
    const second = render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /choose local ingestion source/i }));
    await waitFor(() => expect(screen.getByLabelText('Local path')).toHaveValue(''));
    second.unmount();

    installElectronApi({ chooseIngestionSource: vi.fn().mockRejectedValue(new Error('picker failed')) });
    const third = render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /choose local ingestion source/i }));
    expect(await screen.findByText('picker failed')).toBeInTheDocument();
    third.unmount();

    installElectronApi({ chooseIngestionSource: vi.fn().mockRejectedValue('offline') });
    render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /choose local ingestion source/i }));
    expect(await screen.findByText('Unable to select an ingestion source.')).toBeInTheDocument();
  });

  it('validates desktop sync response shapes and non-Error ingestion failures', async () => {
    const invalidSync = vi.fn().mockResolvedValue({ status: 'queued', ingestion_id: 'wrong' });
    installElectronApi({ runLocalIngestion: invalidSync });
    const first = render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /choose local ingestion source/i }));
    await screen.findByDisplayValue('corpus');
    fireEvent.change(screen.getByLabelText('Source label'), { target: { value: '  Policies  ' } });
    for (const [label, value] of [
      ['Chunk size', '0'], ['Max file MB', '0'], ['Max job MB', '0'], ['Max files', '0'],
      ['Max pages', '0'], ['Parser seconds', '0'], ['Archive items', '0'], ['Expanded MB', '0'], ['Archive depth', '-1'],
    ]) fireEvent.change(screen.getByLabelText(label), { target: { value } });
    fireEvent.click(screen.getByRole('switch', { name: /recursive folder scan/i }));
    fireEvent.click(screen.getByRole('button', { name: /start local knowledge ingestion/i }));
    expect(await screen.findByText('Desktop ingestion returned an invalid synchronous response.')).toBeInTheDocument();
    expect(invalidSync).toHaveBeenCalledWith(expect.objectContaining({
      recursive: false,
      chunk_size: 1200,
      source_label: 'Policies',
      max_archive_depth: 0,
    }));
    first.unmount();

    installElectronApi({ runLocalIngestion: vi.fn().mockRejectedValue('offline') });
    render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /choose local ingestion source/i }));
    await screen.findByDisplayValue('corpus');
    fireEvent.click(screen.getByRole('button', { name: /start local knowledge ingestion/i }));
    expect(await screen.findByText('Local ingestion failed.')).toBeInTheDocument();
  });

  it('starts async ingestion and supports pause, resume, and API cancellation', async () => {
    const runLocalIngestion = vi.fn().mockResolvedValue({ status: 'queued', ingestion_id: 'async-1' });
    installElectronApi({ runLocalIngestion });
    vi.mocked(api.ingestion.pause).mockResolvedValue({ status: 'paused', source: 'corpus' } as any);
    vi.mocked(api.ingestion.resume).mockResolvedValue({ status: 'running', source: 'corpus' } as any);
    vi.mocked(api.ingestion.cancel).mockResolvedValue({ status: 'cancelled', source: 'corpus' } as any);
    render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /choose local ingestion source/i }));
    await screen.findByDisplayValue('corpus');
    fireEvent.click(screen.getByRole('switch', { name: /async mode/i }));
    fireEvent.click(screen.getByRole('switch', { name: /sync to neo4j/i }));
    fireEvent.click(screen.getByRole('button', { name: /start local knowledge ingestion/i }));
    expect(await screen.findByText(/Async ingestion running/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /pause local knowledge ingestion/i }));
    expect(await screen.findByText(/Async ingestion paused/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /resume local knowledge ingestion/i }));
    expect(await screen.findByText(/Async ingestion running/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /cancel local knowledge ingestion/i }));
    await waitFor(() => expect(api.ingestion.cancel).toHaveBeenCalledWith('async-1'));
    expect(runLocalIngestion).toHaveBeenCalledWith(expect.objectContaining({ async_mode: true, sync_neo4j: true }));
  });

  it('rejects invalid async responses and reports history Error and non-Error failures', async () => {
    installElectronApi({ runLocalIngestion: vi.fn().mockResolvedValue({ ingestion_id: 'wrong', files_ingested: 0 }) });
    const first = render(<KnowledgeIngestionSettings />);
    fireEvent.click(await screen.findByRole('button', { name: /choose local ingestion source/i }));
    await screen.findByDisplayValue('corpus');
    fireEvent.click(screen.getByRole('switch', { name: /async mode/i }));
    fireEvent.click(screen.getByRole('button', { name: /start local knowledge ingestion/i }));
    expect(await screen.findByText('Desktop ingestion returned an invalid async response.')).toBeInTheDocument();
    first.unmount();

    vi.mocked(api.ingestion.supported).mockRejectedValueOnce(new Error('history failed'));
    const second = render(<KnowledgeIngestionSettings />);
    expect(await screen.findByText('history failed')).toBeInTheDocument();
    second.unmount();
    vi.mocked(api.ingestion.supported).mockRejectedValueOnce('offline');
    render(<KnowledgeIngestionSettings />);
    expect(await screen.findByText('Unable to load ingestion status.')).toBeInTheDocument();
  });
});
