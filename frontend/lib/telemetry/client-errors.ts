export interface ClientErrorContext {
  module?: string;
  action?: string;
  endpoint?: string;
  metadata?: Record<string, unknown>;
}

interface NormalizedClientError {
  name: string;
  message: string;
  stack?: string;
}

function normalizeError(error: unknown): NormalizedClientError {
  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
    };
  }

  if (typeof error === 'string') {
    return {
      name: 'StringError',
      message: error,
    };
  }

  return {
    name: 'UnknownError',
    message: 'Unknown client error',
  };
}

export function reportClientError(error: unknown, context: ClientErrorContext = {}) {
  const normalized = normalizeError(error);

  if (typeof window !== 'undefined') {
    const sentry = (window as Window & { Sentry?: { captureException?: (error: Error, context?: unknown) => void } }).Sentry;
    if (sentry?.captureException && error instanceof Error) {
      sentry.captureException(error, { extra: context });
      return;
    }
  }

  console.error('[ClientError]', normalized, context);
}

export function installGlobalClientErrorHandlers() {
  if (typeof window === 'undefined') {
    return () => undefined;
  }

  const onError = (event: ErrorEvent) => {
    const error = event.error ?? new Error(event.message);
    reportClientError(error, {
      module: 'window',
      action: 'onerror',
      metadata: {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      },
    });
  };

  const onUnhandledRejection = (event: PromiseRejectionEvent) => {
    reportClientError(event.reason, {
      module: 'window',
      action: 'unhandledrejection',
    });
  };

  window.addEventListener('error', onError);
  window.addEventListener('unhandledrejection', onUnhandledRejection);

  return () => {
    window.removeEventListener('error', onError);
    window.removeEventListener('unhandledrejection', onUnhandledRejection);
  };
}
