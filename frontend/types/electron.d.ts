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

export interface ElectronAPI {
  ping: () => Promise<string>;
  getBackendStatus: () => Promise<string>;
  getDbStatus: () => Promise<string>;
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
