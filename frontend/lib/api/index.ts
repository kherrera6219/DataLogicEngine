import { auth } from './auth';
import { simulation } from './simulation';
import { knowledge } from './knowledge';
import { trace } from './trace';
import { chat, sendChat } from './system_chat';
import { mcp } from './mcp';
import { compliance } from './compliance';

export * from './types';
export { sendChat };

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1';

/**
 * Standardized API Client for Enterprise Resilience
 */
export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (response.status === 401 || response.status === 403) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('user-session');
        window.location.href = '/login?error=session_expired';
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
      request(`/analytics/trends?metric=${metric}&days=${days}`)
  }
};
