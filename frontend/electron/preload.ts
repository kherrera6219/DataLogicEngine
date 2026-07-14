import { contextBridge, ipcRenderer } from 'electron';

const IPC_TIMEOUT = 5000; // 5 second timeout for most IPC calls
const IPC_CHANNEL_TIMEOUTS = new Map<string, number>([
  ['run-database-backup', 10 * 60 * 1000],
  ['run-local-ingestion', 30 * 60 * 1000],
]);
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
  'choose-ingestion-source',
  'run-local-ingestion',
  'cancel-desktop-operation',
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
  const timeoutMs = IPC_CHANNEL_TIMEOUTS.get(channel) ?? IPC_TIMEOUT;
  const timeoutPromise = new Promise((_, reject) => {
    timeoutHandle = setTimeout(() => {
      const payload = args[0];
      if (
        payload &&
        typeof payload === 'object' &&
        typeof (payload as { operation_id?: unknown }).operation_id === 'string'
      ) {
        void ipcRenderer.invoke('cancel-desktop-operation', {
          operation_id: (payload as { operation_id: string }).operation_id,
        });
      }
      reject(new Error(`IPC_TIMEOUT: ${channel} failed to respond within ${timeoutMs}ms`));
    }, timeoutMs);
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
  runDatabaseBackup: (payload: { target_capability?: string; operation_id: string; recovery_secret: string }) => invokeWithTimeout('run-database-backup', payload),
  chooseIngestionSource: () => invokeWithTimeout('choose-ingestion-source'),
  runLocalIngestion: (payload: {
    source_capability: string;
    recursive: boolean;
    chunk_size: number;
    max_file_bytes: number;
    source_label?: string;
    async_mode: boolean;
    sync_neo4j: boolean;
    operation_id: string;
  }) => invokeWithTimeout('run-local-ingestion', payload),
  cancelDesktopOperation: (operationId: string) => invokeWithTimeout('cancel-desktop-operation', { operation_id: operationId }),
  getUpdateState: () => invokeWithTimeout('get-update-state'),
  checkForUpdates: () => invokeWithTimeout('check-for-updates'),
  downloadUpdate: () => invokeWithTimeout('download-update'),
  onBackendLog: (callback: (log: string) => void) => attachChannelListener('backend-log', callback),
  onBackendError: (callback: (error: string) => void) => attachChannelListener('backend-error', callback)
});
