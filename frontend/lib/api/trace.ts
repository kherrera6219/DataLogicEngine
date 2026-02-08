import { request } from '@/lib/api/index';

export const trace = {
    list: (limit: number = 20) => request<{ runs?: unknown[] }>(`/trace/runs?per_page=${limit}`).then((d) => d.runs || []),
    get: (id: string) => request<unknown>(`/trace/runs/${id}`),
    getStages: (id: string) => request<{stages: unknown[]}>(`/trace/runs/${id}/stages`),
    getPersonas: (id: string) => request<{personas: unknown[]}>(`/trace/runs/${id}/personas`),
    getAxes: (id: string) => request<{axes: unknown}>(`/trace/runs/${id}/axes`),
    export: (id: string) => request<string>(`/trace/runs/${id}/export`, { method: 'POST' }).catch(() => null)
};
