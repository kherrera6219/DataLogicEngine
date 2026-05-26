export interface DesktopUpdateState {
  enabled: boolean;
  status:
    | 'disabled'
    | 'idle'
    | 'checking'
    | 'available'
    | 'not_available'
    | 'downloaded'
    | 'error';
  lastCheckAt: string | null;
  currentVersion: string;
  availableVersion: string | null;
  message: string;
}

export interface DesktopDatabaseStatus {
  status: string;
  chroma_collections: Record<string, number>;
  redis_ping_ms: number | null;
}

export interface QuadAnalysisStatus {
  pod_count: number;
  collective_confidence: number;
  mode: string;
}

export interface ElectronAPI {
  ping: () => Promise<string>;
  getBackendStatus: () => Promise<string>;
  getDbStatus: () => Promise<DesktopDatabaseStatus>;
  quadAnalysisStatus: () => Promise<QuadAnalysisStatus>;
  getUpdateState: () => Promise<DesktopUpdateState>;
  checkForUpdates: () => Promise<DesktopUpdateState>;
  downloadUpdate: () => Promise<DesktopUpdateState>;
  onBackendLog: (callback: (log: string) => void) => () => void;
  onBackendError: (callback: (error: string) => void) => () => void;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}
