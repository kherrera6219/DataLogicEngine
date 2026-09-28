import { beforeEach, describe, expect, it, vi } from 'vitest';
import { trace } from '@/lib/api/trace';
import * as apiBase from '@/lib/api/client';

vi.mock('@/lib/api/client', () => ({
  request: vi.fn(),
  API_BASE: 'http://localhost:5000/api/v1',
}));

describe('trace API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('lists traces with default limit and unwraps the backend envelope', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({
      runs: [{ run_id: 'run-1', status: 'pass', created_at: null }],
    });

    const result = await trace.list();

    expect(result).toHaveLength(1);
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs?per_page=20');
  });

  it('clamps trace list limits before building the request URL', async () => {
    vi.mocked(apiBase.request).mockResolvedValue([]);

    await trace.list(1000);
    await trace.list(Number.NaN);
    await trace.list(0);

    expect(apiBase.request).toHaveBeenNthCalledWith(1, '/trace/runs?per_page=100');
    expect(apiBase.request).toHaveBeenNthCalledWith(2, '/trace/runs?per_page=20');
    expect(apiBase.request).toHaveBeenNthCalledWith(3, '/trace/runs?per_page=1');
  });

  it('gets a specific trace by encoded ID', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ id: '123' });
    await trace.get('abc/123');
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/abc%2F123');
  });

  it('gets an aggregate trace bundle by encoded ID', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ run_id: '123', stages: [] });
    await trace.getBundle('abc/123');
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/abc%2F123/bundle');
  });

  it('gets bounded trace analytics with encoded filters', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ runs: [], summary: { run_count: 0 } });

    await trace.analytics({
      days: 7,
      limit: 25,
      status: 'policy block',
      mode: 'governed',
      provider: 'google/gemini',
      scope: 'all',
    });

    expect(apiBase.request).toHaveBeenCalledWith(
      '/trace/analytics?days=7&limit=25&status=policy+block&mode=governed&provider=google%2Fgemini&scope=all',
    );
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
    const result = await trace.export('abc/123');
    expect(result).toBeNull();
    expect(apiBase.request).toHaveBeenCalledWith('/trace/runs/abc%2F123/export', { method: 'POST' });
  });
});
