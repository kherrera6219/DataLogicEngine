import { SimulationEvent, SimulationPreflight, SimulationSession } from './types';
import { request } from '@/lib/api/client';

export const simulation = {
    list: () => request<SimulationSession[]>('/simulations'),
    get: (sessionId: string) => request<SimulationSession>(`/simulations/${sessionId}`),
    preflight: (parameters: Record<string, unknown>) =>
        request<SimulationPreflight>('/simulations/preflight', {
            method: 'POST',
            body: JSON.stringify(parameters)
        }),
    create: (name: string, parameters: Record<string, unknown> = {}) => 
        request('/simulations', {
            method: 'POST',
            body: JSON.stringify({ name, parameters })
        }),
    run: (sessionId: string) => request(`/simulations/${sessionId}/run`, { method: 'POST' }),
    pause: (sessionId: string) => request(`/simulations/${sessionId}/pause`, { method: 'POST' }),
    resume: (sessionId: string) => request(`/simulations/${sessionId}/resume`, { method: 'POST' }),
    retry: (sessionId: string) => request(`/simulations/${sessionId}/retry`, { method: 'POST' }),
    cancel: (sessionId: string) => request(`/simulations/${sessionId}/cancel`, { method: 'POST' }),
    events: (sessionId: string, after = 0) =>
        request<SimulationEvent[]>(`/simulations/${sessionId}/events?after=${after}`)
};
