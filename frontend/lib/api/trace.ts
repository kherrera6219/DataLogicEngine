import { request } from '@/lib/api/client';
import type { TraceBundle } from './types';

export const trace = {
    list: (limit: number = 20) => request<{ runs?: unknown[] }>(`/trace/runs?per_page=${limit}`).then((d) => d.runs || []),
    get: (id: string) => request<unknown>(`/trace/runs/${id}`),
    getBundle: (id: string) => request<TraceBundle>(`/trace/runs/${id}/bundle`),
    getStages: (id: string) => request<{stages: unknown[]}>(`/trace/runs/${id}/stages`),
    getEvidence: (id: string) => request<{evidence: unknown[]}>(`/trace/runs/${id}/evidence`),
    getPersonas: (id: string) => request<{personas: unknown[]}>(`/trace/runs/${id}/personas`),
    getAxes: (id: string) => request<{axes: unknown}>(`/trace/runs/${id}/axes`),
    getKAs: (id: string) => request<{kas: unknown[]}>(`/trace/runs/${id}/kas`),
    getMetrics: (id: string) => request<{metrics: Record<string, unknown>}>(`/trace/runs/${id}/metrics`),
    export: (id: string) => request<string>(`/trace/runs/${id}/export`, { method: 'POST' }).catch(() => null)
};
