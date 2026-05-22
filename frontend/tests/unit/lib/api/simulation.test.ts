import { describe, it, expect, vi } from 'vitest';
import { simulation } from '@/lib/api/simulation';
import { request } from '@/lib/api/client';

vi.mock('@/lib/api/client', () => ({
    request: vi.fn()
}));

describe('Simulation API Client', () => {
    it('list should return empty array on failure', async () => {
        vi.mocked(request).mockRejectedValue(new Error('API Down'));
        
        const result = await simulation.list();
        expect(result).toEqual([]);
    });

    it('create should call /simulations with POST', async () => {
        const mockSession = { uid: 'sim-1', name: 'Test Sim' };
        vi.mocked(request).mockResolvedValue(mockSession);

        const result = await simulation.create('Test Sim', { depth: 5 });
        
        expect(request).toHaveBeenCalledWith('/simulations', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"name":"Test Sim"')
        }));
        expect(result).toEqual(mockSession);
    });

    it('step should call step endpoint', async () => {
        vi.mocked(request).mockResolvedValue({ success: true });

        await simulation.step('sim-123');
        
        expect(request).toHaveBeenCalledWith('/simulations/sim-123/step', {
            method: 'POST'
        });
    });
});
