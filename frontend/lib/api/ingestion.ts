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
};
