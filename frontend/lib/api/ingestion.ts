import { request } from '@/lib/api/client';
import type { IngestionResult, IngestionSupportedTypes } from './types';

export interface StartLocalIngestionRequest {
  path: string;
  recursive?: boolean;
  chunk_size?: number;
  max_file_bytes?: number;
  source_label?: string;
  metadata?: Record<string, unknown>;
}

export interface StartLocalAsyncRequest extends StartLocalIngestionRequest {
  sync_neo4j?: boolean;
}

export interface AsyncIngestionStatus {
  status: 'running' | 'completed' | 'failed';
  source: string;
  started_at: string;
  completed_at?: string;
  result?: IngestionResult;
  error?: string;
  neo4j_sync?: Record<string, unknown> | null;
}

export const ingestion = {
  supported: () =>
    request<{ extensions: string[]; default_chunk_size: number; default_max_file_bytes: number }>(
      '/ingestion/supported'
    ).then((data) => data as IngestionSupportedTypes),
  history: (limit: number = 20) =>
    request<{ items?: IngestionResult[] }>(`/ingestion/history?limit=${limit}`).then(
      (data) => data.items || []
    ),
  startLocal: (payload: StartLocalIngestionRequest) =>
    request<IngestionResult>('/ingestion/local', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  startLocalAsync: (payload: StartLocalAsyncRequest) =>
    request<{ ingestion_id: string; status: string }>('/ingestion/local/async', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  status: (ingestionId: string) =>
    request<AsyncIngestionStatus>(`/ingestion/status/${ingestionId}`),
};
