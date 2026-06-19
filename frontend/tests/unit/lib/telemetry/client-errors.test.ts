import { beforeEach, describe, expect, it, vi } from 'vitest';

describe('lib/telemetry/client-errors', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.restoreAllMocks();
    delete (window as Window & { Sentry?: unknown }).Sentry;
  });

  it('captures Error instances with Sentry when available', async () => {
    const sentryCapture = vi.fn();
    (window as Window & { Sentry?: { captureException: typeof sentryCapture } }).Sentry = {
      captureException: sentryCapture,
    };

    const { reportClientError } = await import('@/lib/telemetry/client-errors');
    const error = new Error('Boom');
    reportClientError(error, { module: 'chat', action: 'send' });

    expect(sentryCapture).toHaveBeenCalledWith(error, {
      extra: { module: 'chat', action: 'send' },
    });
  });

  it('falls back to console.error for non-Error payloads', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { reportClientError } = await import('@/lib/telemetry/client-errors');

    reportClientError('string failure', { endpoint: '/health' });
    reportClientError({ weird: true }, { action: 'normalize' });

    expect(consoleError).toHaveBeenCalledWith(
      '[ClientError]',
      expect.objectContaining({ name: 'StringError', message: 'string failure' }),
      { endpoint: '/health' },
    );
    expect(consoleError).toHaveBeenCalledWith(
      '[ClientError]',
      expect.objectContaining({ name: 'UnknownError', message: 'Unknown client error' }),
      { action: 'normalize' },
    );
  });

  it('installs and removes global error handlers', async () => {
    const addListener = vi.spyOn(window, 'addEventListener');
    const removeListener = vi.spyOn(window, 'removeEventListener');
    const { installGlobalClientErrorHandlers } = await import('@/lib/telemetry/client-errors');

    const cleanup = installGlobalClientErrorHandlers();

    expect(addListener).toHaveBeenCalledWith('error', expect.any(Function));
    expect(addListener).toHaveBeenCalledWith('unhandledrejection', expect.any(Function));

    cleanup();

    expect(removeListener).toHaveBeenCalledWith('error', expect.any(Function));
    expect(removeListener).toHaveBeenCalledWith('unhandledrejection', expect.any(Function));
  });

  it('reports dispatched window error events', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { installGlobalClientErrorHandlers } = await import('@/lib/telemetry/client-errors');

    const cleanup = installGlobalClientErrorHandlers();
    const event = new ErrorEvent('error', {
      message: 'runtime blowup',
      filename: 'ChatInterface.tsx',
      lineno: 22,
      colno: 7,
    });

    window.dispatchEvent(event);

    expect(consoleError).toHaveBeenCalledWith(
      '[ClientError]',
      expect.objectContaining({ message: 'runtime blowup' }),
      expect.objectContaining({
        module: 'window',
        action: 'onerror',
        metadata: expect.objectContaining({
          filename: 'ChatInterface.tsx',
          lineno: 22,
          colno: 7,
        }),
      }),
    );

    cleanup();
  });

  it('reports dispatched unhandled rejection events', async () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    const { installGlobalClientErrorHandlers } = await import('@/lib/telemetry/client-errors');

    const cleanup = installGlobalClientErrorHandlers();
    const event = new Event('unhandledrejection') as PromiseRejectionEvent;
    Object.defineProperty(event, 'reason', {
      value: new Error('async rejection'),
      configurable: true,
    });

    window.dispatchEvent(event);

    expect(consoleError).toHaveBeenCalledWith(
      '[ClientError]',
      expect.objectContaining({ message: 'async rejection' }),
      expect.objectContaining({
        module: 'window',
        action: 'unhandledrejection',
      }),
    );

    cleanup();
  });
});
