import { sanitizeJsonPayload, sanitizeTextInput } from '@/lib/security/input-sanitization';
import { reportClientError } from '@/lib/telemetry/client-errors';
import { shouldUseDesktopSessionFlow } from '@/lib/runtime/policy';
import { removeLocalStorageItem } from '@/lib/state/storage';

/**
 * HTTP error thrown by `request()` for non-OK responses.
 * Carries the raw HTTP `status` code so callers can map it to actionable
 * messages (e.g. 401 → "Invalid API key" on the provider-test endpoint).
 *
 * `message` is typed as `unknown` so that structural error payloads passed
 * from `parseErrorMessage` can never silently coerce to "[object Object]"
 * via the Error constructor's implicit toString(). The constructor guarantees
 * the stored message is always a human-readable string.
 */
export class ApiError extends Error {
  constructor(message: unknown, public readonly status: number) {
    let safeMsg: string;
    if (typeof message === 'string') {
      safeMsg = message;
    } else if (message !== null && typeof message === 'object') {
      // Structured payload: prefer .message, fall back to .detail, then JSON
      const m = message as Record<string, unknown>;
      if (typeof m.message === 'string' && m.message) {
        safeMsg = m.message;
      } else if (typeof m.detail === 'string' && m.detail) {
        safeMsg = m.detail;
      } else if (typeof m.msg === 'string' && m.msg) {
        safeMsg = m.msg;
      } else {
        safeMsg = JSON.stringify(message);
      }
    } else {
      safeMsg = String(message ?? 'Request failed');
    }
    super(safeMsg);
    this.name = 'ApiError';
  }
}

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
      // Backend uses the envelope shape { error: { code, message } } for non-OK
      // responses. Typed as `unknown` so the runtime value is not assumed to be
      // a string — callers that pass objects would otherwise produce "[object Object]"
      // via the Error constructor's implicit toString().
      error?: unknown;
      detail?: string;
      details?: unknown;
    } | null;
    if (errorData) {
      if (typeof errorData.message === 'string' && errorData.message) return errorData.message;
      // Envelope shape: { "error": { "code": "...", "message": "..." } }
      if (errorData.error !== null && errorData.error !== undefined) {
        if (typeof errorData.error === 'string') return errorData.error;
        if (typeof errorData.error === 'object') {
          const nestedErr = errorData.error as { message?: unknown; code?: unknown };
          if (typeof nestedErr.message === 'string' && nestedErr.message) return nestedErr.message;
          if (typeof nestedErr.code === 'string' && nestedErr.code) return nestedErr.code;
        }
      }
      // `detail` can be a string, or an array of Pydantic/validation error objects
      // [{loc, msg, type}]. Guard against returning a non-string value.
      if (typeof errorData.detail === 'string' && errorData.detail) return errorData.detail;
      if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
        const firstItem = errorData.detail[0] as Record<string, unknown>;
        if (typeof firstItem.msg === 'string') return firstItem.msg;
        if (typeof firstItem.message === 'string') return firstItem.message;
        return 'Validation error';
      }
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
    // Provider-test 401 means the *provider's* API key is invalid, not that
    // the DataLogicEngine session has expired. Skip the redirect so the caller
    // receives an ApiError with status 401 and can show an actionable message.
    const isProviderTest =
      /\/gateway\/providers\/[^/]+\/test/.test(endpoint);
    if (sessionAuthFailure && !isProviderTest) {
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
        removeLocalStorageItem('user-session');
        if (!desktopRuntime) {
          window.location.href = '/login?error=session_expired';
        }
      }
      throw new Error('Session expired. Please re-authenticate.');
    }

    if (!response.ok) {
      const message = await parseErrorMessage(response);
      throw new ApiError(message, response.status);
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
