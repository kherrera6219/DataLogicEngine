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

function redactClientText(value: string): string {
  return value
    .replace(/\b(bearer\s+)[A-Za-z0-9._~+/=-]{8,}/gi, '$1[REDACTED_SECRET]')
    .replace(
      /\b((?:api[_-]?key|token|secret|password|authorization)\s*[:=]\s*)[^\s,;]+/gi,
      '$1[REDACTED_SECRET]',
    )
    .replace(/\bsk-[A-Za-z0-9_-]{16,}\b/g, '[REDACTED_SECRET]')
    .replace(/\bAIza[A-Za-z0-9_-]{20,}\b/g, '[REDACTED_SECRET]')
    .replace(/\bukg_[A-Za-z0-9_-]{16,}\b/g, '[REDACTED_SECRET]')
    .replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, '[REDACTED_EMAIL]');
}

function externalTelemetryEnabled(): boolean {
  return process.env.NEXT_PUBLIC_EXTERNAL_TELEMETRY_ENABLED === 'true';
}

function redactClientValue(value: unknown, depth = 0): unknown {
  if (depth > 4) {
    return '[TRUNCATED]';
  }
  if (typeof value === 'string') {
    return redactClientText(value);
  }
  if (Array.isArray(value)) {
    return value.slice(0, 50).map((item) => redactClientValue(item, depth + 1));
  }
  if (value && typeof value === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value).slice(0, 50)) {
      result[key] = /password|secret|token|api[_-]?key|authorization|cookie|private[_-]?key/i.test(key)
        ? '[REDACTED_SECRET]'
        : redactClientValue(item, depth + 1);
    }
    return result;
  }
  return value;
}

function normalizeError(error: unknown): NormalizedClientError {
  if (error instanceof Error) {
    return {
      name: error.name,
      message: redactClientText(error.message),
      stack: error.stack ? redactClientText(error.stack) : undefined,
    };
  }

  if (typeof error === 'string') {
    return {
      name: 'StringError',
      message: redactClientText(error),
    };
  }

  return {
    name: 'UnknownError',
    message: 'Unknown client error',
  };
}

export function reportClientError(error: unknown, context: ClientErrorContext = {}) {
  const normalized = normalizeError(error);

  if (typeof window !== 'undefined' && externalTelemetryEnabled()) {
    const sentry = (window as Window & { Sentry?: { captureException?: (error: Error, context?: unknown) => void } }).Sentry;
    if (sentry?.captureException && error instanceof Error) {
      sentry.captureException(error, { extra: context });
      return;
    }
  }

  const safeContext = redactClientValue(context) as ClientErrorContext;
  console.error('[ClientError]', normalized, safeContext);
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
