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
    });

    await expect(ingestion.supported()).resolves.toEqual({
      extensions: ['.txt'],
      default_chunk_size: 1200,
      default_max_file_bytes: 10485760,
    });
    expect(requestMock).toHaveBeenCalledWith('/ingestion/supported');
  });

  it('loads history items', async () => {
    requestMock.mockResolvedValue({ items: [{ ingestion_id: 'run-1' }] });

    await expect(ingestion.history(5)).resolves.toEqual([{ ingestion_id: 'run-1' }]);
    expect(requestMock).toHaveBeenCalledWith('/ingestion/history?limit=5');
  });

  it('starts local ingestion', async () => {
    requestMock.mockResolvedValue({ ingestion_id: 'run-2' });

    await ingestion.startLocal({ path: 'C:/corpus', recursive: true, chunk_size: 1200 });

    expect(requestMock).toHaveBeenCalledWith('/ingestion/local', {
      method: 'POST',
      body: JSON.stringify({ path: 'C:/corpus', recursive: true, chunk_size: 1200 }),
    });
  });
});
