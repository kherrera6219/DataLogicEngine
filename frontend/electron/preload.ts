import { contextBridge, ipcRenderer } from 'electron';

const IPC_TIMEOUT = 5000; // 5 second timeout for most IPC calls
const ALLOWED_INVOKE_CHANNELS = new Set([
  'ping',
  'get-backend-status',
  'get-db-status',
  'get-update-state',
  'check-for-updates',
  'download-update',
]);

type ListenerCallback = (payload: string) => void;

function attachChannelListener(channel: 'backend-log' | 'backend-error', callback: ListenerCallback) {
  const listener = (_event: unknown, value: string) => callback(value);
  ipcRenderer.on(channel, listener);
  return () => {
    ipcRenderer.removeListener(channel, listener);
  };
}

/**
 * Executes an IPC call with a timeout safety net.
 */
async function invokeWithTimeout(channel: string, ...args: unknown[]) {
  if (!ALLOWED_INVOKE_CHANNELS.has(channel)) {
    throw new Error(`IPC_SECURITY: ${channel} is not an allowed invoke channel`);
  }

  let timeoutHandle: ReturnType<typeof setTimeout> | undefined;
  const timeoutPromise = new Promise((_, reject) => {
    timeoutHandle = setTimeout(() => reject(new Error(`IPC_TIMEOUT: ${channel} failed to respond within ${IPC_TIMEOUT}ms`)), IPC_TIMEOUT);
  });

  try {
    return await Promise.race([
      ipcRenderer.invoke(channel, ...args),
      timeoutPromise
    ]);
  } catch (error) {
    console.error(`[IPC Error] ${channel}:`, error);
    throw error;
  } finally {
    if (timeoutHandle) {
      clearTimeout(timeoutHandle);
    }
  }
}

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  ping: () => invokeWithTimeout('ping'),
  getBackendStatus: () => invokeWithTimeout('get-backend-status'),
  getDbStatus: () => invokeWithTimeout('get-db-status'),
  getUpdateState: () => invokeWithTimeout('get-update-state'),
  checkForUpdates: () => invokeWithTimeout('check-for-updates'),
  downloadUpdate: () => invokeWithTimeout('download-update'),
  onBackendLog: (callback: (log: string) => void) => attachChannelListener('backend-log', callback),
  onBackendError: (callback: (error: string) => void) => attachChannelListener('backend-error', callback)
});
