import { afterEach, describe, expect, it, vi } from 'vitest';

import { runBoundedShutdown } from './lifecycle';

afterEach(() => {
  vi.useRealTimers();
});

describe('runBoundedShutdown', () => {
  it('forces cleanup when an active backend request does not drain in time', async () => {
    vi.useFakeTimers();
    const terminate = vi.fn();
    const pendingNotification = new Promise<void>(() => undefined);

    const shutdown = runBoundedShutdown(() => pendingNotification, terminate, 2500);
    await vi.advanceTimersByTimeAsync(2500);
    await shutdown;

    expect(terminate).toHaveBeenCalledTimes(1);
  });

  it('cleans up immediately after a graceful lifecycle acknowledgement', async () => {
    const terminate = vi.fn();

    await runBoundedShutdown(async () => true, terminate, 2500);

    expect(terminate).toHaveBeenCalledTimes(1);
  });
});
