import { request } from '@/lib/api/client';
import type {
  TraceAxisVector,
  TraceBundle,
  TraceEvidenceSource,
  TraceKAInvocation,
  TracePersona,
  TraceRun,
  TraceStage,
} from './types';

type TraceListResponse = { runs?: TraceRun[] };

const DEFAULT_TRACE_LIMIT = 20;
const MAX_TRACE_LIMIT = 100;

function boundedLimit(limit: number): number {
  if (!Number.isFinite(limit)) return DEFAULT_TRACE_LIMIT;
  return Math.min(Math.max(Math.trunc(limit), 1), MAX_TRACE_LIMIT);
}

function traceRunPath(id: string): string {
  return `/trace/runs/${encodeURIComponent(id)}`;
}

function traceRunsFromResponse(data: TraceListResponse | TraceRun[] | null | undefined): TraceRun[] {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.runs)) return data.runs;
  return [];
}

export const trace = {
  list: (limit: number = DEFAULT_TRACE_LIMIT) =>
    request<TraceListResponse | TraceRun[]>(`/trace/runs?per_page=${boundedLimit(limit)}`).then(traceRunsFromResponse),
  get: (id: string) => request<TraceRun>(traceRunPath(id)),
  getBundle: (id: string) => request<TraceBundle>(`${traceRunPath(id)}/bundle`),
  getStages: (id: string) => request<{ stages: TraceStage[] }>(`${traceRunPath(id)}/stages`),
  getEvidence: (id: string) => request<{ evidence: TraceEvidenceSource[] }>(`${traceRunPath(id)}/evidence`),
  getPersonas: (id: string) => request<{ personas: TracePersona[] }>(`${traceRunPath(id)}/personas`),
  getAxes: (id: string) => request<{ axes: TraceAxisVector | null }>(`${traceRunPath(id)}/axes`),
  getKAs: (id: string) => request<{ kas: TraceKAInvocation[] }>(`${traceRunPath(id)}/kas`),
  getMetrics: (id: string) => request<{ metrics: TraceBundle['metrics'] }>(`${traceRunPath(id)}/metrics`),
  export: (id: string) => request<unknown>(`${traceRunPath(id)}/export`, { method: 'POST' }).catch(() => null),
};
