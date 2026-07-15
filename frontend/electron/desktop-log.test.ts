import { describe, expect, it } from 'vitest';

import { createDesktopLogLine, redactDesktopLogText } from './desktop-log';

describe('desktop structured logging', () => {
  it('redacts secrets, PII, content, and the user home path', () => {
    const redacted = redactDesktopLogText(
      'C:\\Users\\Kevin token=super-secret-value user@example.com prompt=private user text; done',
      'C:\\Users\\Kevin',
    );

    expect(redacted).toContain('%USERPROFILE%');
    expect(redacted).toContain('token=[REDACTED_SECRET]');
    expect(redacted).toContain('[REDACTED_EMAIL]');
    expect(redacted).toContain('prompt=[REDACTED_CONTENT]');
    expect(redacted).not.toContain('super-secret-value');
    expect(redacted).not.toContain('user@example.com');
    expect(redacted).not.toContain('private user text');
  });

  it('emits the canonical local JSON log shape', () => {
    const line = createDesktopLogLine('WARN', 'Backend unavailable', {
      timestamp: '2026-07-14T12:00:00.000Z',
      correlationId: 'corr-1',
      event: 'desktop.backend_unavailable',
    });
    const record = JSON.parse(line ?? '{}');

    expect(record).toMatchObject({
      schema_version: 'dle.log.v1',
      severity: 'WARN',
      component: 'electron-main',
      event: 'desktop.backend_unavailable',
      correlation_id: 'corr-1',
      request_id: 'corr-1',
      redaction_classification: 'deterministic_redacted',
    });
    expect(record.error_code).toBeNull();
    expect(record.duration_ms).toBeNull();
    expect(record.state_transition).toBeNull();
  });
});
