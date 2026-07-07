import { beforeEach, describe, expect, it, vi } from 'vitest';

import { isDesktopRendererRuntime, shouldUseDesktopSessionFlow } from '@/lib/runtime/policy';

vi.mock('@/lib/security/input-sanitization', () => ({
  sanitizeJsonPayload: vi.fn((value: unknown) => value),
  sanitizeTextInput: vi.fn((value: string) => value),
  sanitizeFileName: vi.fn((value: string) => value),
  validateUploadFile: vi.fn(() => ({ valid: true })),
}));

vi.mock('@/lib/runtime/policy', () => ({
  isDesktopRendererRuntime: vi.fn(() => false),
  shouldUseDesktopSessionFlow: vi.fn(() => false),
}));

vi.mock('@/lib/telemetry/client-errors', () => ({
  reportClientError: vi.fn(),
}));

vi.mock('@/lib/state/storage', () => ({
  removeLocalStorageItem: vi.fn(() => true),
}));

type MockResponseInit = {
  ok?: boolean;
  status?: number;
  statusText?: string;
  headers?: Record<string, string>;
  json?: unknown;
  text?: string;
};

function createMockResponse({
  ok = true,
  status = 200,
  statusText = 'OK',
  headers = { 'content-type': 'application/json' },
  json = undefined,
  text,
}: MockResponseInit = {}) {
  const resolvedText =
    text ?? (typeof json === 'string' ? json : json === undefined ? '' : JSON.stringify(json));

  return {
    ok,
    status,
    statusText,
    headers: new Headers(headers),
    json: vi.fn(async () => json),
    text: vi.fn(async () => resolvedText),
  } as unknown as Response;
}

async function loadClientModule() {
  vi.resetModules();
  return import('@/lib/api/client');
}

describe('lib/api/client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    const runtimePolicy = vi.mocked(shouldUseDesktopSessionFlow);
    runtimePolicy.mockReturnValue(false);
    const desktopPolicy = vi.mocked(isDesktopRendererRuntime);
    desktopPolicy.mockReturnValue(false);
  });

  describe('ApiError', () => {
    it('normalizes string and structured messages', async () => {
      const { ApiError } = await loadClientModule();

      expect(new ApiError('Oops', 400).message).toBe('Oops');
      expect(new ApiError({ message: 'Primary' }, 400).message).toBe('Primary');
      expect(new ApiError({ detail: 'Fallback detail' }, 400).message).toBe('Fallback detail');
      expect(new ApiError({ msg: 'Fallback msg' }, 400).message).toBe('Fallback msg');
      expect(new ApiError({ code: 'X1' }, 400).message).toBe('{"code":"X1"}');
      expect(new ApiError(null, 400).message).toBe('Request failed');
    });
  });

  describe('buildApiUrl', () => {
    it('keeps absolute URLs and prefixes relative endpoints', async () => {
      const { API_BASE, buildApiUrl } = await loadClientModule();

      expect(buildApiUrl('https://example.com/endpoint')).toBe('https://example.com/endpoint');
      expect(buildApiUrl('/auth/check')).toBe(`${API_BASE}/auth/check`);
      expect(buildApiUrl('gateway/chat')).toBe(`${API_BASE}/gateway/chat`);
    });
  });

  describe('request', () => {
    it('unwraps JSON data responses for GET requests', async () => {
      const fetchMock = vi.fn().mockResolvedValue(
        createMockResponse({ json: { data: { id: 1, name: 'demo' } } }),
      );
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();
      await expect(request('/demo')).resolves.toEqual({ id: 1, name: 'demo' });
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/demo'),
        expect.objectContaining({ credentials: 'include' }),
      );
    });

    it('adds a CSRF token to mutation requests and sanitizes JSON payloads', async () => {
      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { csrf_token: 'csrf-token-1' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ json: { data: { saved: true } } }));
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();
      const { sanitizeJsonPayload } = await import('@/lib/security/input-sanitization');

      await expect(
        request('/settings/save', {
          method: 'POST',
          body: JSON.stringify({ prompt: 'hello' }),
        }),
      ).resolves.toEqual({ saved: true });

      expect(sanitizeJsonPayload).toHaveBeenCalledWith({ prompt: 'hello' });

      const mutationHeaders = fetchMock.mock.calls[1][1].headers as Headers;
      expect(mutationHeaders.get('Content-Type')).toBe('application/json');
      expect(mutationHeaders.get('X-CSRF-Token')).toBe('csrf-token-1');
    });

    it('adds a CSRF token to desktop mutation requests while preserving the desktop header', async () => {
      const { isDesktopRendererRuntime, shouldUseDesktopSessionFlow } = await import('@/lib/runtime/policy');
      vi.mocked(shouldUseDesktopSessionFlow).mockReturnValue(true);
      vi.mocked(isDesktopRendererRuntime).mockReturnValue(true);

      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { nonce: 'desktop-nonce' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ json: { data: { authenticated: true } } }))
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { csrf_token: 'desktop-csrf-token' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ json: { data: { saved: true } } }));
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();

      await expect(
        request('/gateway/keys', {
          method: 'POST',
          body: JSON.stringify({ provider: 'google', key: 'provider-key', model: 'gemini-3.1-pro-preview' }),
        }),
      ).resolves.toEqual({ saved: true });

      expect(fetchMock.mock.calls[0][0]).toContain('/auth/desktop/challenge');
      expect(fetchMock.mock.calls[1][0]).toContain('/auth/desktop/auto-login');
      expect(fetchMock.mock.calls[2][0]).toContain('/auth/csrf-token');
      const csrfHeaders = new Headers(fetchMock.mock.calls[2][1].headers as HeadersInit);
      expect(csrfHeaders.get('X-DataLogic-Desktop')).toBe('true');
      const mutationHeaders = new Headers(fetchMock.mock.calls[3][1].headers as HeadersInit);
      expect(mutationHeaders.get('X-DataLogic-Desktop')).toBe('true');
      expect(mutationHeaders.get('X-Desktop-Auth-Timestamp')).toBe('electron-main-process-signed');
      expect(mutationHeaders.get('X-Desktop-Auth-Request-Signature')).toBe('electron-main-process-signed');
      expect(mutationHeaders.get('X-Desktop-Auth-Signature')).toBe('electron-main-process-signed');
      expect(mutationHeaders.get('X-CSRF-Token')).toBe('desktop-csrf-token');
    });

    it('retries a mutation after a CSRF refresh on 403', async () => {
      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { csrf_token: 'csrf-token-1' } } }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 403,
            statusText: 'Forbidden',
            json: { message: 'csrf expired' },
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { csrf_token: 'csrf-token-2' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ json: { data: { retried: true } } }));
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();

      await expect(
        request('/settings/update', { method: 'PATCH', body: JSON.stringify({ ok: true }) }),
      ).resolves.toEqual({ retried: true });

      const retriedHeaders = fetchMock.mock.calls[3][1].headers as Headers;
      expect(retriedHeaders.get('X-CSRF-Token')).toBe('csrf-token-2');
    });

    it('does not force a content-type for FormData uploads', async () => {
      const fetchMock = vi.fn().mockResolvedValue(createMockResponse({ json: { data: { ok: true } } }));
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();
      const body = new FormData();
      body.append('file', new Blob(['hello']), 'demo.txt');

      await request('/upload', { method: 'POST', body });

      const headers = new Headers(fetchMock.mock.calls[0][1].headers as HeadersInit);
      expect(headers.has('Content-Type')).toBe(false);
    });

    it('supports desktop auto-login nonce injection for explicit desktop auth calls', async () => {
      const { isDesktopRendererRuntime, shouldUseDesktopSessionFlow } = await import('@/lib/runtime/policy');
      vi.mocked(shouldUseDesktopSessionFlow).mockReturnValue(true);
      vi.mocked(isDesktopRendererRuntime).mockReturnValue(true);

      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { nonce: 'desktop-nonce' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ json: { data: { authenticated: true } } }));
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();

      await request('/auth/desktop/auto-login', { method: 'POST' });

      const headers = fetchMock.mock.calls[1][1].headers as Headers;
      expect(headers.get('X-DataLogic-Desktop')).toBe('true');
      expect(headers.get('X-Desktop-Auth-Nonce')).toBe('desktop-nonce');
      expect(headers.get('X-Desktop-Auth-Timestamp')).toBe('electron-main-process-signed');
      expect(headers.get('X-Desktop-Auth-Request-Signature')).toBe('electron-main-process-signed');
      expect(headers.get('X-Desktop-Auth-Signature')).toBe('electron-main-process-signed');
    });

    it('retries the original request after desktop session recovery', async () => {
      const { isDesktopRendererRuntime, shouldUseDesktopSessionFlow } = await import('@/lib/runtime/policy');
      vi.mocked(shouldUseDesktopSessionFlow).mockReturnValue(true);
      vi.mocked(isDesktopRendererRuntime).mockReturnValue(true);

      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { nonce: 'initial-nonce' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ json: { data: { ok: true } } }))
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { csrf_token: 'stale-desktop-csrf' } } }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 401,
            statusText: 'Unauthorized',
            json: { message: 'expired' },
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { nonce: 'recovery-nonce' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ json: { data: { ok: true } } }))
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { csrf_token: 'recovered-desktop-csrf' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ json: { data: { recovered: true } } }));
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();

      await expect(request('/chat/send', { method: 'POST', body: JSON.stringify({ q: 'hello' }) })).resolves.toEqual({
        recovered: true,
      });

      expect(fetchMock.mock.calls[1][0]).toContain('/auth/desktop/auto-login');
      const initialLoginHeaders = new Headers(fetchMock.mock.calls[1][1].headers as HeadersInit);
      expect(initialLoginHeaders.get('X-Desktop-Auth-Nonce')).toBe('initial-nonce');
      expect(fetchMock.mock.calls[5][0]).toContain('/auth/desktop/auto-login');
      const recoveryHeaders = new Headers(fetchMock.mock.calls[5][1].headers as HeadersInit);
      expect(recoveryHeaders.get('X-Desktop-Auth-Nonce')).toBe('recovery-nonce');
      const retriedHeaders = new Headers(fetchMock.mock.calls[7][1].headers as HeadersInit);
      expect(retriedHeaders.get('X-CSRF-Token')).toBe('recovered-desktop-csrf');
    });

    it('clears the session and throws when auth check returns 403', async () => {
      const fetchMock = vi.fn().mockResolvedValue(
        createMockResponse({
          ok: false,
          status: 403,
          statusText: 'Forbidden',
          json: { message: 'forbidden' },
        }),
      );
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();
      const { removeLocalStorageItem } = await import('@/lib/state/storage');

      await expect(request('/auth/check')).rejects.toThrow('Session expired. Please re-authenticate.');
      expect(removeLocalStorageItem).toHaveBeenCalledWith('user-session');
    });

    it('does not treat provider test failures as session expiration', async () => {
      const fetchMock = vi.fn().mockResolvedValue(
        createMockResponse({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          json: { error: { message: 'Invalid API key' } },
        }),
      );
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();
      await expect(request('/gateway/providers/openai/test')).rejects.toMatchObject({
        status: 401,
        message: 'Invalid API key',
      });
    });

    it('preserves structured non-OK payloads on ApiError', async () => {
      const errorPayload = {
        error: 'Gateway failed',
        run_id: 'run-fail-001',
        audit_trail: {
          decision_path: '/api/v1/trace/runs/run-fail-001/decision',
          complete_trace_url: '/api/v1/trace/runs/run-fail-001',
          download_url: '/api/v1/trace/runs/run-fail-001/download',
        },
        provider_used: 'openai',
        model_used: 'gpt-5',
      };
      const fetchMock = vi.fn().mockResolvedValue(
        createMockResponse({
          ok: false,
          status: 503,
          statusText: 'Service Unavailable',
          json: errorPayload,
        }),
      );
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();
      await expect(
        request('/gateway/chat', {
          method: 'POST',
          headers: { 'X-CSRF-Token': 'csrf-token' },
          body: JSON.stringify({ messages: [] }),
        }),
      ).rejects.toMatchObject({
        status: 503,
        message: 'Gateway failed',
        payload: errorPayload,
      });
    });

    it('parses detail arrays and nested error codes from failed responses', async () => {
      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 422,
            statusText: 'Unprocessable Entity',
            json: { detail: [{ msg: 'Validation error from array' }] },
          }),
        )
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 500,
            statusText: 'Server Error',
            json: { error: { code: 'SERVER_FAILURE' } },
          }),
        );
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();
      await expect(request('/validation')).rejects.toMatchObject({
        message: 'Validation error from array',
        status: 422,
      });
      await expect(request('/server')).rejects.toMatchObject({
        message: 'SERVER_FAILURE',
        status: 500,
      });
    });

    it('falls back to response text and transforms failed-to-fetch errors', async () => {
      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(
          createMockResponse({
            ok: false,
            status: 503,
            statusText: 'Unavailable',
            headers: { 'content-type': 'text/plain' },
            text: 'Service unavailable now',
          }),
        )
        .mockRejectedValueOnce(new TypeError('Failed to fetch'));
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();

      await expect(request('/text-error')).rejects.toMatchObject({
        message: 'Service unavailable now',
        status: 503,
      });
      await expect(request('/offline')).rejects.toThrow('Failed to fetch from API');
    });

    it('returns 204 and plain text responses correctly', async () => {
      const fetchMock = vi
        .fn()
        .mockResolvedValueOnce(
          createMockResponse({ json: { data: { csrf_token: 'delete-csrf-token' } } }),
        )
        .mockResolvedValueOnce(createMockResponse({ status: 204, json: null }))
        .mockResolvedValueOnce(
          createMockResponse({
            headers: { 'content-type': 'text/plain' },
            json: undefined,
            text: 'plain response',
          }),
        );
      vi.stubGlobal('fetch', fetchMock);

      const { request } = await loadClientModule();

      await expect(request('/delete', { method: 'DELETE' })).resolves.toBeUndefined();
      await expect(request('/plain')).resolves.toBe('plain response');
    });

    it('respects disabled strict sanitization and sanitizes invalid JSON as text', async () => {
      vi.stubEnv(
        'NEXT_PUBLIC_FEATURE_FLAGS',
        JSON.stringify({ strictInputSanitization: false }),
      );

      const fetchMock = vi.fn().mockResolvedValue(createMockResponse({ json: { data: { ok: true } } }));
      vi.stubGlobal('fetch', fetchMock);

      let client = await loadClientModule();
      const sanitizers = await import('@/lib/security/input-sanitization');

      await client.request('/raw', { method: 'POST', body: '  keep raw  ' });
      expect(sanitizers.sanitizeTextInput).not.toHaveBeenCalled();

      vi.clearAllMocks();
      vi.stubEnv(
        'NEXT_PUBLIC_FEATURE_FLAGS',
        JSON.stringify({ strictInputSanitization: true }),
      );
      client = await loadClientModule();
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue(createMockResponse({ json: { data: { ok: true } } })));

      await client.request('/invalid-json', { method: 'POST', body: '{not-json' });
      expect(sanitizers.sanitizeTextInput).toHaveBeenCalledWith('{not-json', { trim: false });
    });
  });
});
