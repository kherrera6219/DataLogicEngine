import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ingestion } from '@/lib/api/ingestion';

const requestMock = vi.fn();

vi.mock('@/lib/api/client', () => ({
  request: (...args: unknown[]) => requestMock(...args),
}));

describe('ingestion api', () => {
  beforeEach(() => {
    requestMock.mockReset();
  });

  it('loads supported ingestion defaults', async () => {
    requestMock.mockResolvedValue({
      extensions: ['.txt'],
      default_chunk_size: 1200,
      default_max_file_bytes: 10485760,
      default_max_total_bytes: 104857600,
      default_max_files: 1000,
      default_max_pages: 500,
      default_max_archive_entries: 10000,
      default_max_decompressed_bytes: 104857600,
      default_max_archive_depth: 1,
      default_parser_timeout_seconds: 60,
    });

    await expect(ingestion.supported()).resolves.toEqual({
      extensions: ['.txt'],
      default_chunk_size: 1200,
      default_max_file_bytes: 10485760,
      default_max_total_bytes: 104857600,
      default_max_files: 1000,
      default_max_pages: 500,
      default_max_archive_entries: 10000,
      default_max_decompressed_bytes: 104857600,
      default_max_archive_depth: 1,
      default_parser_timeout_seconds: 60,
    });
    expect(requestMock).toHaveBeenCalledWith('/ingestion/supported');
  });

  it('loads history items', async () => {
    requestMock.mockResolvedValue({ items: [{ ingestion_id: 'run-1' }] });

    await expect(ingestion.history(5)).resolves.toEqual([{ ingestion_id: 'run-1' }]);
    expect(requestMock).toHaveBeenCalledWith('/ingestion/history?limit=5');
  });

  it('rejects malformed history instead of treating it as an empty corpus', async () => {
    requestMock.mockResolvedValue({});

    await expect(ingestion.history(5)).rejects.toThrow('Invalid ingestion history response');
  });

  it('starts local ingestion', async () => {
    requestMock.mockResolvedValue({ ingestion_id: 'run-2' });

    await ingestion.startLocal({ path: 'C:/corpus', recursive: true, chunk_size: 1200 });

    expect(requestMock).toHaveBeenCalledWith('/ingestion/local', {
      method: 'POST',
      body: JSON.stringify({ path: 'C:/corpus', recursive: true, chunk_size: 1200 }),
    });
  });

  it('controls and scans durable ingestion jobs', async () => {
    requestMock.mockResolvedValue({ status: 'paused' });

    await ingestion.pause('run-3');
    expect(requestMock).toHaveBeenCalledWith('/ingestion/jobs/run-3/pause', { method: 'POST' });

    await ingestion.consistency();
    expect(requestMock).toHaveBeenCalledWith('/ingestion/corpus/consistency');
  });
});
