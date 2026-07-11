import { describe, it, expect, vi, beforeEach } from 'vitest';
import { knowledge } from '@/lib/api/knowledge';
import * as apiBase from '@/lib/api/client';

vi.mock('@/lib/api/client', () => ({
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
    expect(apiBase.request).toHaveBeenCalledWith('/pillar-levels');
  });

  it('fetches knowledge stats', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({});
    await knowledge.stats();
    expect(apiBase.request).toHaveBeenCalledWith('/analytics/overview');
  });

  it('fetches graph nodes', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ nodes: [{ id: 1, label: 'Node 1', value: 3 }] });
    const nodes = await knowledge.getNodes();
    expect(apiBase.request).toHaveBeenCalledWith('/graph');
    expect(nodes).toEqual([{ id: '1', label: 'Node 1', name: 'Node 1', value: 3, val: 3 }]);
  });

  it('fetches graph edges', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ links: [{ source: 1, target: 2, label: 'related', value: 0.5 }] });
    const edges = await knowledge.getEdges();
    expect(apiBase.request).toHaveBeenCalledWith('/graph');
    expect(edges).toEqual([{
      source: '1',
      target: '2',
      label: 'related',
      value: 0.5,
      edge_type: 'related',
      weight: 0.5,
    }]);
  });

  it('fetches and normalizes the graph in one request', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ nodes: [], links: [] });
    await knowledge.graph();
    expect(apiBase.request).toHaveBeenCalledTimes(1);
    expect(apiBase.request).toHaveBeenCalledWith('/graph');
  });

  it('sends the selected axis to the graph endpoint', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ nodes: [], links: [] });
    await knowledge.graph(8);
    expect(apiBase.request).toHaveBeenCalledWith('/graph?axis=8');
  });
});
