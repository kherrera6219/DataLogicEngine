import { SimulationSession } from './types';
import { request } from '@/lib/api/client';

export const simulation = {
    list: () => request<SimulationSession[]>('/simulations'),
    create: (name: string, parameters: Record<string, unknown> = {}) => 
        request('/simulations', {
            method: 'POST',
            body: JSON.stringify({ name, parameters })
        }),
    step: (uid: string) => request(`/simulations/${uid}/step`, { method: 'POST' })
};
