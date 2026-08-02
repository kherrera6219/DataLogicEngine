import { beforeEach, describe, expect, it, vi } from 'vitest';

import { algorithms, isKATerminalStatus } from './algorithms';

const { requestMock } = vi.hoisted(() => ({
  requestMock: vi.fn(),
}));

vi.mock('./client', () => ({
  request: requestMock,
}));

describe('Knowledge Algorithm product API client', () => {
  beforeEach(() => {
    requestMock.mockReset();
    requestMock.mockResolvedValue({ success: true });
  });

  it('uses the canonical plan, run, cancel, and evidence routes', async () => {
    await algorithms.plan({
      ka_id: 'KA-004',
      input: { query: 'validate' },
      idempotency_key: 'cp19j-frontend-client',
    });
    await algorithms.runs(999);
    await algorithms.run('run/unsafe');
    await algorithms.execute('run/unsafe', 'confirm-19j');
    await algorithms.cancel('run/unsafe');
    await algorithms.result('run/unsafe');
    await algorithms.trace('run/unsafe');
    await algorithms.artifacts('run/unsafe');
    await algorithms.effects('run/unsafe');

    expect(requestMock).toHaveBeenNthCalledWith(
      1,
      '/ka/runs/plan',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(requestMock).toHaveBeenNthCalledWith(2, '/ka/runs?limit=200');
    expect(requestMock).toHaveBeenNthCalledWith(3, '/ka/runs/run%2Funsafe');
    expect(requestMock).toHaveBeenNthCalledWith(
      4,
      '/ka/runs/run%2Funsafe/execute',
      {
        method: 'POST',
        body: JSON.stringify({ confirmation_token: 'confirm-19j' }),
      },
    );
    expect(requestMock).toHaveBeenNthCalledWith(
      5,
      '/ka/runs/run%2Funsafe/cancel',
      {
        method: 'POST',
        body: JSON.stringify({}),
      },
    );
    expect(requestMock).toHaveBeenNthCalledWith(6, '/ka/runs/run%2Funsafe/result');
    expect(requestMock).toHaveBeenNthCalledWith(7, '/ka/runs/run%2Funsafe/trace');
    expect(requestMock).toHaveBeenNthCalledWith(8, '/ka/runs/run%2Funsafe/artifacts');
    expect(requestMock).toHaveBeenNthCalledWith(9, '/ka/runs/run%2Funsafe/effects');
  });

  it('recognizes every truthful terminal state', () => {
    for (const status of [
      'succeeded',
      'partial',
      'blocked',
      'failed',
      'cancelled',
      'timed_out',
      'dry_run',
      'expired',
    ] as const) {
      expect(isKATerminalStatus(status)).toBe(true);
    }
    expect(isKATerminalStatus('planned')).toBe(false);
    expect(isKATerminalStatus('queued')).toBe(false);
    expect(isKATerminalStatus('running')).toBe(false);
  });
});
