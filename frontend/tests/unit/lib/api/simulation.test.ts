import { beforeEach, describe, it, expect, vi } from 'vitest';
import { simulation } from '@/lib/api/simulation';
import { request } from '@/lib/api/client';

vi.mock('@/lib/api/client', () => ({
    request: vi.fn()
}));

describe('Simulation API Client', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('list should propagate service failures', async () => {
        vi.mocked(request).mockRejectedValue(new Error('API Down'));
        
        await expect(simulation.list()).rejects.toThrow('API Down');
    });

    it('create should call /simulations with POST', async () => {
        const mockSession = { session_id: 'sim-1', name: 'Test Sim' };
        vi.mocked(request).mockResolvedValue(mockSession);

        const result = await simulation.create('Test Sim', { depth: 5 });
        
        expect(request).toHaveBeenCalledWith('/simulations', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"name":"Test Sim"')
        }));
        expect(result).toEqual(mockSession);
    });

    it('run should call run endpoint', async () => {
        vi.mocked(request).mockResolvedValue({ success: true });

        await simulation.run('sim-123');
        
        expect(request).toHaveBeenCalledWith('/simulations/sim-123/run', {
            method: 'POST'
        });
    });

    it('pause, resume, retry, and cancel use durable control endpoints', async () => {
        vi.mocked(request).mockResolvedValue({ success: true });

        await simulation.pause('sim-123');
        await simulation.resume('sim-123');
        await simulation.retry('sim-123');
        await simulation.cancel('sim-123');

        expect(request).toHaveBeenNthCalledWith(1, '/simulations/sim-123/pause', {
            method: 'POST'
        });
        expect(request).toHaveBeenNthCalledWith(2, '/simulations/sim-123/resume', {
            method: 'POST'
        });
        expect(request).toHaveBeenNthCalledWith(3, '/simulations/sim-123/retry', {
            method: 'POST'
        });
        expect(request).toHaveBeenNthCalledWith(4, '/simulations/sim-123/cancel', {
            method: 'POST'
        });
    });

    it('preflight posts a versioned scenario before creation', async () => {
        vi.mocked(request).mockResolvedValue({ scenario_revision: 'sha' });

        await simulation.preflight({ query: 'Evaluate this', depth: 'quick' });

        expect(request).toHaveBeenCalledWith('/simulations/preflight', {
            method: 'POST',
            body: JSON.stringify({ query: 'Evaluate this', depth: 'quick' })
        });
    });
});
