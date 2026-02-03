import { describe, it, expect, vi, beforeEach } from 'vitest';
import { trace } from './trace';
import * as apiBase from './index';

vi.mock('./index', () => ({
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
    expect(apiBase.request).toHaveBeenCalledWith('/traces/runs?per_page=20');
  });

  it('gets a specific trace by ID', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ id: '123' });
    await trace.get('123');
    expect(apiBase.request).toHaveBeenCalledWith('/traces/runs/123');
  });

  it('gets stages for a trace', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ stages: [] });
    await trace.getStages('123');
    expect(apiBase.request).toHaveBeenCalledWith('/traces/runs/123/stages');
  });

  it('gets personas for a trace', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ personas: [] });
    await trace.getPersonas('123');
    expect(apiBase.request).toHaveBeenCalledWith('/traces/runs/123/personas');
  });

  it('gets axes for a trace', async () => {
    vi.mocked(apiBase.request).mockResolvedValueOnce({ axes: {} });
    await trace.getAxes('123');
    expect(apiBase.request).toHaveBeenCalledWith('/traces/runs/123/axes');
  });

  it('exports trace and returns null on failure', async () => {
    vi.mocked(apiBase.request).mockRejectedValueOnce(new Error('Export Failed'));
    const result = await trace.export('123');
    expect(result).toBeNull();
    expect(apiBase.request).toHaveBeenCalledWith('/traces/runs/123/export');
  });
});
