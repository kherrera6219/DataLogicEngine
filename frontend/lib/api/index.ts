import { auth } from './auth';
import { simulation } from './simulation';
import { knowledge } from './knowledge';
import { trace } from './trace';
import { chat } from './chat';
import { mcp } from './mcp';
import { compliance } from './compliance';

export * from './types';


export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1';

function isDesktopRuntime(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(
    (window as typeof window & { electronAPI?: unknown }).electronAPI ||
    window.navigator.userAgent.includes('Electron')
  );
}

async function tryDesktopAutoLogin(): Promise<boolean> {
  const response = await fetch(`${API_BASE}/auth/desktop/auto-login`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return response.ok;
}

/**
 * Standardized API Client for Enterprise Resilience
 */
export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const desktopRuntime = isDesktopRuntime();
  
  try {
    const response = await fetch(url, {
      ...options,
      credentials: options.credentials ?? 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (response.status === 401 || response.status === 403) {
      if (desktopRuntime && !endpoint.includes('/auth/desktop/auto-login')) {
        const recovered = await tryDesktopAutoLogin().catch(() => false);
        if (recovered) {
          const retryResponse = await fetch(url, {
            ...options,
            credentials: options.credentials ?? 'include',
            headers: {
              'Content-Type': 'application/json',
              ...options.headers,
            },
          });
          if (retryResponse.ok) {
            const retryJson = await retryResponse.json();
            return retryJson.data !== undefined ? retryJson.data : retryJson;
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
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `System Error: ${response.statusText}`);
    }

    const json = await response.json();
    return json.data !== undefined ? json.data : json;
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
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
