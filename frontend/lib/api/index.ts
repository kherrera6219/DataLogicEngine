import { auth } from './auth';
import { simulation } from './simulation';
import { knowledge } from './knowledge';
import { trace } from './trace';
import { chat } from './chat';
import { mcp } from './mcp';
import { compliance } from './compliance';

export * from './types';

const DEFAULT_API_BASE = 'http://localhost:5000/api/v1';
export const API_BASE = (process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE).replace(/\/$/, '');

function isDesktopRuntime(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(
    (window as typeof window & { electronAPI?: unknown }).electronAPI ||
    window.navigator.userAgent.includes('Electron')
  );
}

export function buildApiUrl(endpoint: string): string {
  if (/^https?:\/\//i.test(endpoint)) {
    return endpoint;
  }

  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE}${normalizedEndpoint}`;
}

async function tryDesktopAutoLogin(): Promise<boolean> {
  const response = await fetch(buildApiUrl('/auth/desktop/auto-login'), {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-DataLogic-Desktop': 'true',
    },
  });
  return response.ok;
}

function buildHeaders(options: RequestInit): Headers {
  const headers = new Headers(options.headers || {});
  const isFormDataBody = typeof FormData !== 'undefined' && options.body instanceof FormData;

  if (!isFormDataBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  return headers;
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers?.get?.('content-type') || '';
  const canReadJson = typeof response.json === 'function';
  if (contentType.includes('application/json') || (!contentType && canReadJson)) {
    const json = await response.json().catch(() => null);
    if (json !== null) {
      return (json.data !== undefined ? json.data : json) as T;
    }
  }

  if (typeof response.text === 'function') {
    return (await response.text()) as T;
  }

  return undefined as T;
}

async function parseErrorMessage(response: Response): Promise<string> {
  if (typeof response.json === 'function') {
    const errorData = await response.json().catch(() => null) as {
      message?: string;
      error?: string;
      detail?: string;
      details?: unknown;
    } | null;
    if (errorData) {
      if (errorData.message) return errorData.message;
      if (errorData.error) return errorData.error;
      if (errorData.detail) return errorData.detail;
      if (typeof errorData.details === 'string') return errorData.details;
    }
  }

  if (typeof response.text === 'function') {
    const text = await response.text().catch(() => '');
    if (text) {
      return text;
    }
  }

  return `System Error: ${response.statusText}`;
}

/**
 * Standardized API Client for Enterprise Resilience
 */
export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = buildApiUrl(endpoint);
  const desktopRuntime = isDesktopRuntime();
  const headers = buildHeaders(options);
  if (desktopRuntime && !headers.has('X-DataLogic-Desktop')) {
    headers.set('X-DataLogic-Desktop', 'true');
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      credentials: options.credentials ?? 'include',
      headers,
    });

    if (response.status === 401 || response.status === 403) {
      if (desktopRuntime && !endpoint.includes('/auth/desktop/auto-login')) {
        const recovered = await tryDesktopAutoLogin().catch(() => false);
        if (recovered) {
          const retryResponse = await fetch(url, {
            ...options,
            credentials: options.credentials ?? 'include',
            headers,
          });
          if (retryResponse.ok) {
            return parseResponse<T>(retryResponse);
          }
        }
      }

      if (typeof window !== 'undefined') {
        localStorage.removeItem('user-session');
        if (!desktopRuntime) {
          window.location.href = '/login?error=session_expired';
        }
      }
      throw new Error("Session expired. Please re-authenticate.");
    }

    if (!response.ok) {
      const message = await parseErrorMessage(response);
      throw new Error(message);
    }

    return parseResponse<T>(response);
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    if (
      error instanceof TypeError &&
      /failed to fetch/i.test(error.message)
    ) {
      throw new Error(
        `Failed to fetch from API (${API_BASE}). Verify backend service is running and reachable.`
      );
    }
    throw error;
  }
}

export const api = {
  chat,
  auth,
  simulation,
  knowledge,
  trace,
  mcp,
  compliance,
  system: {
    health: () => Promise.resolve('Operational')
  },
  analytics: {
    summary: () => request('/analytics/summary'),
    trends: (metric: string, days: number = 7) => 
      request(`/analytics/trends?metric=${metric}&days=${days}`),
    overview: () => request('/analytics/overview'),
    activity: (limit: number = 10) => request(`/analytics/activity?limit=${limit}`),
    mcp: () => request('/analytics/mcp')
  },
  get: <T>(url: string) => request<T>(url, { method: 'GET' }),
};
