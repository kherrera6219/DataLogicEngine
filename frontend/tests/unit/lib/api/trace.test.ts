import { describe, it, expect, vi, beforeEach } from 'vitest';
import { trace } from '@/lib/api/trace';
import * as apiBase from '@/lib/api/client';

vi.mock('@/lib/api/client', () => ({
  request: vi.fn(),
  API_BASE: 'http://localhost:5000/api/v1'
}));

describe('trace API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('lists traces with default limit', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce([]);
    await trace.list();
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs?per_page=20');
  });

  it('gets a specific trace by ID', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ id: '123' });
    await trace.get('123');
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/123');
  });

  it('gets an aggregate trace bundle', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ run_id: '123', stages: [] });
    await trace.getBundle('123');
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/123/bundle');
  });

  it('gets stages for a trace', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ stages: [] });
    await trace.getStages('123');
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/123/stages');
  });

  it('gets personas for a trace', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ personas: [] });
    await trace.getPersonas('123');
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/123/personas');
  });

  it('gets evidence, KAs, and metrics for a trace', async () => {
    vi.mocked(apiBase.request)
      .mockResolvedValueOnce({ evidence: [] })
      .mockResolvedValueOnce({ kas: [] })
      .mockResolvedValueOnce({ metrics: {} });

    await trace.getEvidence('123');
    await trace.getKAs('123');
    await trace.getMetrics('123');

    expect(apiBase.request).toHaveBeenNthCalledWith(1, '/trace/runs/123/evidence');
    expect(apiBase.request).toHaveBeenNthCalledWith(2, '/trace/runs/123/kas');
    expect(apiBase.request).toHaveBeenNthCalledWith(3, '/trace/runs/123/metrics');
  });

  it('gets axes for a trace', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ axes: {} });
    await trace.getAxes('123');
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/123/axes');
  });

  it('exports trace and returns null on failure', async () => {
    vi.mocked(apiBase.request).mockRejectedValueOnce(new Error('Export Failed'));
    const result = await trace.export('123');
    expect(result).toBeNull();
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/123/export', { method: 'POST' });
  });
});
