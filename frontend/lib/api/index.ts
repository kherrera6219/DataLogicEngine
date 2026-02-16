import { auth } from './auth';
import { simulation } from './simulation';
import { knowledge } from './knowledge';
import { trace } from './trace';
import { chat } from './chat';
import { mcp } from './mcp';
import { compliance } from './compliance';
import { sanitizeJsonPayload, sanitizeTextInput } from '@/lib/security/input-sanitization';
import { reportClientError } from '@/lib/telemetry/client-errors';
import { shouldUseDesktopSessionFlow } from '@/lib/runtime/policy';

export * from './types';

const DEFAULT_API_BASE = 'http://localhost:5000/api/v1';
export const API_BASE = (process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_BASE).replace(/\/$/, '');
const CSRF_TOKEN_ENDPOINT = '/auth/csrf-token';
const DESKTOP_CHALLENGE_ENDPOINT = '/auth/desktop/challenge';
const CSRF_EXEMPT_ENDPOINT_PREFIXES = [
  '/auth/login',
  '/auth/register',
  '/auth/mfa/verify',
  '/auth/desktop/challenge',
  '/auth/desktop/auto-login',
];

let csrfTokenCache: string | null = null;
let csrfTokenInFlight: Promise<string | null> | null = null;

export function buildApiUrl(endpoint: string): string {
  if (/^https?:\/\//i.test(endpoint)) {
    return endpoint;
  }

  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE}${normalizedEndpoint}`;
}

function isMutationMethod(method: string): boolean {
  return !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method.toUpperCase());
}

function isCsrfExemptEndpoint(endpoint: string): boolean {
  return CSRF_EXEMPT_ENDPOINT_PREFIXES.some((prefix) => endpoint.startsWith(prefix));
}

function extractResponseDataNode(payload: unknown): unknown {
  if (payload && typeof payload === 'object' && 'data' in payload) {
    return (payload as { data: unknown }).data;
  }
  return payload;
}

async function fetchDesktopChallengeNonce(): Promise<string | null> {
  const response = await fetch(buildApiUrl(DESKTOP_CHALLENGE_ENDPOINT), {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-DataLogic-Desktop': 'true',
    },
  });

  if (!response.ok) {
    return null;
  }

  const payload = await response.json().catch(() => null);
  if (!payload) {
    return null;
  }

  const dataNode = extractResponseDataNode(payload) as { nonce?: unknown } | null;
  if (!dataNode || typeof dataNode.nonce !== 'string') {
    return null;
  }

  return dataNode.nonce;
}

async function tryDesktopAutoLogin(): Promise<boolean> {
  const nonce = await fetchDesktopChallengeNonce().catch(() => null);
  if (!nonce) {
    return false;
  }

  const response = await fetch(buildApiUrl('/auth/desktop/auto-login'), {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-DataLogic-Desktop': 'true',
      'X-Desktop-Auth-Nonce': nonce,
    },
  });
  return response.ok;
}

async function fetchCsrfToken(): Promise<string | null> {
  if (csrfTokenCache) {
    return csrfTokenCache;
  }

  if (csrfTokenInFlight) {
    return csrfTokenInFlight;
  }

  csrfTokenInFlight = (async () => {
    const response = await fetch(buildApiUrl(CSRF_TOKEN_ENDPOINT), {
      method: 'GET',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      return null;
    }

    const payload = await response.json().catch(() => null);
    if (!payload) {
      return null;
    }

    const dataNode = extractResponseDataNode(payload) as { csrf_token?: unknown } | null;
    if (!dataNode || typeof dataNode.csrf_token !== 'string') {
      return null;
    }

    csrfTokenCache = dataNode.csrf_token;
    return csrfTokenCache;
  })()
    .catch(() => null)
    .finally(() => {
      csrfTokenInFlight = null;
    });

  return csrfTokenInFlight;
}

function buildHeaders(options: RequestInit): Headers {
  const headers = new Headers(options.headers || {});
  const isFormDataBody = typeof FormData !== 'undefined' && options.body instanceof FormData;

  if (!isFormDataBody && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  return headers;
}

function isStrictInputSanitizationEnabled(): boolean {
  const rawFlagPayload = process.env.NEXT_PUBLIC_FEATURE_FLAGS;
  if (!rawFlagPayload) {
    return true;
  }

  try {
    const parsed = JSON.parse(rawFlagPayload) as { strictInputSanitization?: unknown };
    const rawValue = parsed.strictInputSanitization;
    if (typeof rawValue === 'boolean') {
      return rawValue;
    }
    if (typeof rawValue === 'string') {
      const normalized = rawValue.trim().toLowerCase();
      if (normalized === 'false' || normalized === '0') {
        return false;
      }
      if (normalized === 'true' || normalized === '1') {
        return true;
      }
    }
    return true;
  } catch {
    return true;
  }
}

function normalizeRequestBody(body: RequestInit['body']): RequestInit['body'] {
  if (typeof body !== 'string') {
    return body;
  }

  const strictSanitizationEnabled = isStrictInputSanitizationEnabled();
  if (!strictSanitizationEnabled) {
    return body;
  }

  const trimmedBody = body.trim();
  const maybeJsonPayload = trimmedBody.startsWith('{') || trimmedBody.startsWith('[');
  if (maybeJsonPayload) {
    try {
      const parsed = JSON.parse(body) as unknown;
      return JSON.stringify(sanitizeJsonPayload(parsed));
    } catch {
      return sanitizeTextInput(body, { trim: false });
    }
  }

  return sanitizeTextInput(body, { trim: false });
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
  const desktopRuntime = shouldUseDesktopSessionFlow();
  const requestMethod = (options.method || 'GET').toUpperCase();
  const headers = buildHeaders(options);
  const normalizedBody = normalizeRequestBody(options.body);
  if (desktopRuntime && !headers.has('X-DataLogic-Desktop')) {
    headers.set('X-DataLogic-Desktop', 'true');
  }

  if (
    desktopRuntime &&
    endpoint.includes('/auth/desktop/auto-login') &&
    !headers.has('X-Desktop-Auth-Nonce')
  ) {
    const nonce = await fetchDesktopChallengeNonce().catch(() => null);
    if (nonce) {
      headers.set('X-Desktop-Auth-Nonce', nonce);
    }
  }

  if (
    !desktopRuntime &&
    isMutationMethod(requestMethod) &&
    !isCsrfExemptEndpoint(endpoint) &&
    !headers.has('X-CSRF-Token')
  ) {
    const csrfToken = await fetchCsrfToken().catch(() => null);
    if (csrfToken) {
      headers.set('X-CSRF-Token', csrfToken);
    }
  }
  
  try {
    let response = await fetch(url, {
      ...options,
      credentials: options.credentials ?? 'include',
      body: normalizedBody,
      headers,
    });

    if (
      response.status === 403 &&
      !desktopRuntime &&
      isMutationMethod(requestMethod) &&
      !isCsrfExemptEndpoint(endpoint)
    ) {
      csrfTokenCache = null;
      const refreshedToken = await fetchCsrfToken().catch(() => null);
      if (refreshedToken) {
        headers.set('X-CSRF-Token', refreshedToken);
        response = await fetch(url, {
          ...options,
          credentials: options.credentials ?? 'include',
          body: normalizedBody,
          headers,
        });
      }
    }

    const sessionAuthFailure =
      response.status === 401 ||
      (response.status === 403 && endpoint.includes('/auth/check'));
    if (sessionAuthFailure) {
      if (desktopRuntime && !endpoint.includes('/auth/desktop/auto-login')) {
        const recovered = await tryDesktopAutoLogin().catch(() => false);
        if (recovered) {
          const retryResponse = await fetch(url, {
            ...options,
            credentials: options.credentials ?? 'include',
            body: normalizedBody,
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
    reportClientError(error, {
      module: 'api.request',
      action: 'fetch',
      endpoint,
    });
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
