export type DesktopLogLevel = 'INFO' | 'WARN' | 'ERROR';

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export function redactDesktopLogText(raw: string, homePath = ''): string {
  let safe = raw.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim();
  if (homePath) {
    safe = safe.replace(new RegExp(escapeRegExp(homePath), 'gi'), '%USERPROFILE%');
  }
  return safe
    .replace(/\b(bearer\s+)[A-Za-z0-9._~+/=-]{8,}/gi, '$1[REDACTED_SECRET]')
    .replace(
      /\b((?:api[_-]?key|token|secret|password|authorization)\s*[:=]\s*)[^\s,;]+/gi,
      '$1[REDACTED_SECRET]',
    )
    .replace(/\bsk-[A-Za-z0-9_-]{16,}\b/g, '[REDACTED_SECRET]')
    .replace(/\bAIza[A-Za-z0-9_-]{20,}\b/g, '[REDACTED_SECRET]')
    .replace(/\bukg_[A-Za-z0-9_-]{16,}\b/g, '[REDACTED_SECRET]')
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, '[REDACTED_EMAIL]')
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[REDACTED_SSN]')
    .replace(
      /\b(prompt|document|content|response|provider[_-]?payload|request[_-]?body)\s*[:=]\s*[^,;]+/gi,
      '$1=[REDACTED_CONTENT]',
    );
}

export function createDesktopLogLine(
  level: DesktopLogLevel,
  rawMessage: string,
  options: {
    timestamp?: string;
    homePath?: string;
    correlationId?: string;
    event?: string;
  } = {},
): string | null {
  const message = redactDesktopLogText(rawMessage, options.homePath);
  if (!message) {
    return null;
  }
  return `${JSON.stringify({
    schema_version: 'dle.log.v1',
    timestamp: options.timestamp ?? new Date().toISOString(),
    severity: level,
    level,
    service: 'datalogicengine-desktop',
    component: 'electron-main',
    event: options.event ?? 'desktop.runtime',
    message,
    correlation_id: options.correlationId ?? 'desktop',
    request_id: options.correlationId ?? 'desktop',
    error_code: null,
    duration_ms: null,
    state_transition: null,
    redaction_classification: 'deterministic_redacted',
  })}\n`;
}
