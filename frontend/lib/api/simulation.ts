import { SimulationSession } from './types';
import { request } from './index';

export const simulation = {
    list: () => request<SimulationSession[]>('/simulations').catch(() => []),
    create: (name: string, parameters: Record<string, unknown> = {}) => 
        request('/simulations', {
            method: 'POST',
            body: JSON.stringify({ name, parameters })
        }),
    step: (uid: string) => request(`/simulations/${uid}/step`, { method: 'POST' })
};
