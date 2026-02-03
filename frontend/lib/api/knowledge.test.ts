import { describe, it, expect, vi, beforeEach } from 'vitest';
import { knowledge } from './knowledge';
import * as apiBase from './index';

vi.mock('./index', () => ({
  request: vi.fn(),
  API_BASE: 'http://localhost:5000/api/v1'
}));

describe('knowledge API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches knowledge pillars', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce([]);
    await knowledge.pillars();
    expect(apiBase.request).toHaveBeenCalledWith('/ukg/pillars');
  });

  it('fetches knowledge stats', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({});
    await knowledge.stats();
    expect(apiBase.request).toHaveBeenCalledWith('/analytics/summary');
  });

  it('fetches graph nodes', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce([]);
    await knowledge.getNodes();
    expect(apiBase.request).toHaveBeenCalledWith('/ukg/nodes');
  });

  it('fetches graph edges', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce([]);
    await knowledge.getEdges();
    expect(apiBase.request).toHaveBeenCalledWith('/ukg/edges');
  });
});
