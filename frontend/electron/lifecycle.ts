export async function runBoundedShutdown(
  notify: () => Promise<unknown>,
  terminate: () => void,
  timeoutMs = 3500,
): Promise<void> {
  let timeout: NodeJS.Timeout | null = null;
  try {
    await Promise.race([
      notify(),
      new Promise<void>((resolve) => {
        timeout = setTimeout(resolve, timeoutMs);
      }),
    ]);
  } finally {
    if (timeout) {
      clearTimeout(timeout);
    }
    terminate();
  }
}
