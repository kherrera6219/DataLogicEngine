import { request } from '@/lib/api/index';

export const trace = {
    list: (limit: number = 20) => request<unknown[]>(`/traces/runs?per_page=${limit}`),
    get: (id: string) => request<unknown>(`/traces/runs/${id}`),
    getStages: (id: string) => request<{stages: unknown[]}>(`/traces/runs/${id}/stages`),
    getPersonas: (id: string) => request<{personas: unknown[]}>(`/traces/runs/${id}/personas`),
    getAxes: (id: string) => request<{axes: unknown}>(`/traces/runs/${id}/axes`),
    export: (id: string) => request<Blob>(`/traces/runs/${id}/export`).catch(() => null)
};
