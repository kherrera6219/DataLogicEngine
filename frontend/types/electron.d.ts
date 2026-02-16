export interface ElectronAPI {
  ping: () => Promise<string>;
  getBackendStatus: () => Promise<string>;
  getDbStatus: () => Promise<string>;
  onBackendLog: (callback: (log: string) => void) => () => void;
  onBackendError: (callback: (error: string) => void) => () => void;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}
