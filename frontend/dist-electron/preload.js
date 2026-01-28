"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    ping: () => electron_1.ipcRenderer.invoke('ping'),
    getBackendStatus: () => electron_1.ipcRenderer.invoke('get-backend-status'),
    getDbStatus: () => electron_1.ipcRenderer.invoke('get-db-status'),
    onBackendLog: (callback) => {
        electron_1.ipcRenderer.on('backend-log', (_event, value) => callback(value));
    },
    onBackendError: (callback) => {
        electron_1.ipcRenderer.on('backend-error', (_event, value) => callback(value));
    }
});
