import { request } from '@/lib/api/client';
import type { IngestionResult, IngestionSupportedTypes } from './types';

export interface StartLocalIngestionRequest {
  path: string;
  recursive?: boolean;
  chunk_size?: number;
  max_file_bytes?: number;
  max_total_bytes?: number;
  max_files?: number;
  max_pages?: number;
  max_archive_entries?: number;
  max_decompressed_bytes?: number;
  max_archive_depth?: number;
  parser_timeout_seconds?: number;
  source_label?: string;
  metadata?: Record<string, unknown>;
}

export interface StartLocalAsyncRequest extends StartLocalIngestionRequest {
  sync_neo4j?: boolean;
}

export interface AsyncIngestionStatus {
  ingestion_id?: string;
  status: 'queued' | 'running' | 'paused' | 'materialization_pending' | 'deletion_pending' | 'completed' | 'failed' | 'cancelled' | 'superseded' | 'interrupted';
  source: string;
  started_at?: string;
  completed_at?: string;
  checkpoint?: string;
  cancellation_requested?: boolean;
  pause_requested?: boolean;
  files_scanned?: number;
  files_ingested?: number;
  files_rejected?: number;
  chunks_created?: number;
  materializations_pending?: number;
  result?: IngestionResult;
  error?: string;
  neo4j_sync?: Record<string, unknown> | null;
  files?: IngestionResult['files'];
}

export const ingestion = {
  supported: () =>
    request<IngestionSupportedTypes>(
      '/ingestion/supported'
    ),
  history: (limit: number = 20) =>
    request<{ items?: IngestionResult[] }>(`/ingestion/history?limit=${limit}`).then((data) => {
      if (!Array.isArray(data.items)) {
        throw new Error('Invalid ingestion history response');
      }
      return data.items;
    }),
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
  cancel: (ingestionId: string) =>
    request<AsyncIngestionStatus>(`/ingestion/jobs/${ingestionId}/cancel`, { method: 'POST' }),
  pause: (ingestionId: string) =>
    request<AsyncIngestionStatus>(`/ingestion/jobs/${ingestionId}/pause`, { method: 'POST' }),
  resume: (ingestionId: string) =>
    request<AsyncIngestionStatus>(`/ingestion/jobs/${ingestionId}/resume`, { method: 'POST' }),
  retry: (ingestionId: string) =>
    request<AsyncIngestionStatus>(`/ingestion/jobs/${ingestionId}/retry`, { method: 'POST' }),
  remove: (ingestionId: string) =>
    request<AsyncIngestionStatus>(`/ingestion/jobs/${ingestionId}/delete`, { method: 'POST' }),
  repair: (ingestionId: string) =>
    request<Record<string, unknown>>(`/ingestion/jobs/${ingestionId}/repair`, { method: 'POST' }),
  consistency: () =>
    request<{
      scanned_jobs: number;
      consistent_jobs: number;
      divergence_count: number;
      jobs: Array<Record<string, unknown>>;
    }>('/ingestion/corpus/consistency'),
};
