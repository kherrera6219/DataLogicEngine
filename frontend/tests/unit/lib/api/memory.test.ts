import { beforeEach, describe, expect, it, vi } from 'vitest';

import { memory } from '@/lib/api/memory';
import * as apiClient from '@/lib/api/client';

vi.mock('@/lib/api/client', () => ({ request: vi.fn() }));

describe('memory API', () => {
  beforeEach(() => vi.clearAllMocks());

  it('reviews validated or working memory explicitly', async () => {
    vi.mocked(apiClient.request).mockResolvedValueOnce({ items: [], stats: {} });
    await memory.review(true);
    expect(apiClient.request).toHaveBeenCalledWith('/memory/review?include_working=true');
  });

  it('uses owner lifecycle endpoints', async () => {
    vi.mocked(apiClient.request).mockResolvedValue({});
    await memory.compact(500);
    await memory.remove('vertex/one');
    await memory.recover();

    expect(apiClient.request).toHaveBeenCalledWith('/memory/compact', {
      method: 'POST',
      body: JSON.stringify({ max_working_vertices: 500 }),
    });
    expect(apiClient.request).toHaveBeenCalledWith('/memory/vertex%2Fone', { method: 'DELETE' });
    expect(apiClient.request).toHaveBeenCalledWith('/memory/recover', { method: 'POST' });
  });
});
