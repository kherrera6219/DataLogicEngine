"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const IPC_TIMEOUT = 5000; // 5 second timeout for most IPC calls
/**
 * Executes an IPC call with a timeout safety net.
 */
async function invokeWithTimeout(channel, ...args) {
    const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error(`IPC_TIMEOUT: ${channel} failed to respond within ${IPC_TIMEOUT}ms`)), IPC_TIMEOUT);
    });
    try {
        return await Promise.race([
            electron_1.ipcRenderer.invoke(channel, ...args),
            timeoutPromise
        ]);
    }
    catch (error) {
        console.error(`[IPC Error] ${channel}:`, error);
        throw error;
    }
}
// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    ping: () => invokeWithTimeout('ping'),
    getBackendStatus: () => invokeWithTimeout('get-backend-status'),
    getDbStatus: () => invokeWithTimeout('get-db-status'),
    onBackendLog: (callback) => {
        electron_1.ipcRenderer.on('backend-log', (_event, value) => callback(value));
    },
    onBackendError: (callback) => {
        electron_1.ipcRenderer.on('backend-error', (_event, value) => callback(value));
    }
});
