import { auth } from './auth';
import { simulation } from './simulation';
import { knowledge } from './knowledge';
import { trace } from './trace';
import { chat } from './chat';
import { mcp } from './mcp';
import { compliance } from './compliance';
import { ingestion } from './ingestion';
import { request } from './client';

export { API_BASE, buildApiUrl, request } from './client';
export * from './types';

export const api = {
  chat,
  auth,
  simulation,
  knowledge,
  trace,
  ingestion,
  mcp,
  compliance,
  system: {
    health: () => Promise.resolve('Operational'),
  },
  analytics: {
    summary: () => request('/analytics/summary'),
    trends: (metric: string, days: number = 7) =>
      request(`/analytics/trends?metric=${metric}&days=${days}`),
    overview: () => request('/analytics/overview'),
    activity: (limit: number = 10) => request(`/analytics/activity?limit=${limit}`),
    mcp: () => request('/analytics/mcp'),
  },
  get: <T>(url: string) => request<T>(url, { method: 'GET' }),
};
