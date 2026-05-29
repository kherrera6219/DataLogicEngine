import { contextBridge, ipcRenderer } from 'electron';

const IPC_TIMEOUT = 5000; // 5 second timeout for most IPC calls
const ALLOWED_INVOKE_CHANNELS = new Set([
  'ping',
  'get-backend-status',
  'get-db-status',
  'quad-analysis-status',
  'dmrf-status',
  'dsqp-persona-profiles',
  'network-status',
  'local-model-status',
  'reasoning-layer-progress',
  'ka-execution-feed',
  'get-desktop-storage-metrics',
  'choose-backup-folder',
  'run-database-backup',
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
  quadAnalysisStatus: () => invokeWithTimeout('quad-analysis-status'),
  dmrfStatus: () => invokeWithTimeout('dmrf-status'),
  dsqpPersonaProfiles: () => invokeWithTimeout('dsqp-persona-profiles'),
  getNetworkStatus: () => invokeWithTimeout('network-status'),
  getLocalModelStatus: () => invokeWithTimeout('local-model-status'),
  getReasoningLayerProgress: () => invokeWithTimeout('reasoning-layer-progress'),
  getKAExecutionFeed: () => invokeWithTimeout('ka-execution-feed'),
  getDesktopStorageMetrics: () => invokeWithTimeout('get-desktop-storage-metrics'),
  chooseBackupFolder: () => invokeWithTimeout('choose-backup-folder'),
  runDatabaseBackup: (payload: { target_dir?: string }) => invokeWithTimeout('run-database-backup', payload),
  getUpdateState: () => invokeWithTimeout('get-update-state'),
  checkForUpdates: () => invokeWithTimeout('check-for-updates'),
  downloadUpdate: () => invokeWithTimeout('download-update'),
  onBackendLog: (callback: (log: string) => void) => attachChannelListener('backend-log', callback),
  onBackendError: (callback: (error: string) => void) => attachChannelListener('backend-error', callback)
});
