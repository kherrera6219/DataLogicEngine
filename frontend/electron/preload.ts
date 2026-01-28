import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  ping: () => ipcRenderer.invoke('ping'),
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  onBackendLog: (callback: (log: string) => void) => {
    ipcRenderer.on('backend-log', (_event, value) => callback(value));
  },
  onBackendError: (callback: (error: string) => void) => {
    ipcRenderer.on('backend-error', (_event, value) => callback(value));
  }
});
