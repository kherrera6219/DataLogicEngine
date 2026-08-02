import { request } from './client';
import type {
  KAProductPlanEnvelope,
  KAProductRun,
  KAProductRunEnvelope,
  KAProductRunListEnvelope,
} from './types';

export interface KAProductPlanInput {
  ka_id: string;
  input: Record<string, unknown>;
  idempotency_key: string;
  mode?: 'production' | 'evaluation' | 'dry_run';
  request_id?: string;
  session_id?: string;
  tier?: string;
  layer?: string;
  persona?: string;
  metadata?: Record<string, unknown>;
  budget?: Record<string, number>;
}

function runPath(runId: string, suffix = ''): string {
  return `/ka/runs/${encodeURIComponent(runId)}${suffix}`;
}

export const algorithms = {
  plan: (payload: KAProductPlanInput) =>
    request<KAProductPlanEnvelope>('/ka/runs/plan', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  runs: (limit = 50) =>
    request<KAProductRunListEnvelope>(
      `/ka/runs?limit=${Math.max(1, Math.min(200, Math.trunc(limit)))}`,
    ),

  run: (runId: string) =>
    request<KAProductRunEnvelope>(runPath(runId)),

  execute: (runId: string, confirmationToken?: string | null) =>
    request<KAProductRunEnvelope>(runPath(runId, '/execute'), {
      method: 'POST',
      body: JSON.stringify(
        confirmationToken
          ? { confirmation_token: confirmationToken }
          : {},
      ),
    }),

  cancel: (runId: string) =>
    request<KAProductRunEnvelope>(runPath(runId, '/cancel'), {
      method: 'POST',
      body: JSON.stringify({}),
    }),

  result: (runId: string) =>
    request<Record<string, unknown>>(runPath(runId, '/result')),

  trace: (runId: string) =>
    request<Record<string, unknown>>(runPath(runId, '/trace')),

  artifacts: (runId: string) =>
    request<{ artifacts: Array<Record<string, unknown>> }>(
      runPath(runId, '/artifacts'),
    ),

  effects: (runId: string) =>
    request<{ effects: Array<Record<string, unknown>> }>(
      runPath(runId, '/effects'),
    ),
};

export function isKATerminalStatus(status: KAProductRun['status']): boolean {
  return [
    'succeeded',
    'partial',
    'blocked',
    'failed',
    'cancelled',
    'timed_out',
    'dry_run',
    'expired',
  ].includes(status);
}
