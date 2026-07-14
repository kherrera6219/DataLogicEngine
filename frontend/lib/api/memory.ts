import { request } from '@/lib/api/client';

export interface MemoryReviewItem {
  vertex_id: string;
  content: string;
  validation_state: string;
  source_run_id?: string | null;
  policy_result?: string | null;
  retention_class?: string | null;
  session_id?: string | null;
  created_at?: string | null;
  last_accessed?: string | null;
}

export interface MemoryStats {
  status: string;
  memory_vertices: number;
  memory_edges: number;
  last_recall_timestamp?: string | null;
}

export const memory = {
  review: (includeWorking = false) =>
    request<{ items: MemoryReviewItem[]; stats: MemoryStats }>(
      `/memory/review?include_working=${includeWorking ? 'true' : 'false'}`,
    ),
  exportGraph: () => request<Record<string, unknown>>('/memory/export'),
  compact: (maxWorkingVertices: number) =>
    request<{ working_before: number; working_after: number; removed: number }>('/memory/compact', {
      method: 'POST',
      body: JSON.stringify({ max_working_vertices: maxWorkingVertices }),
    }),
  remove: (vertexId: string) =>
    request<{ deleted: boolean }>(`/memory/${encodeURIComponent(vertexId)}`, { method: 'DELETE' }),
  recover: () => request<MemoryStats>('/memory/recover', { method: 'POST' }),
};
