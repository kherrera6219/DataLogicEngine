"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const path = __importStar(require("path"));
const child_process_1 = require("child_process");
const os = __importStar(require("os"));
let mainWindow = null;
let backendProcess = null;
function createWindow() {
    mainWindow = new electron_1.BrowserWindow({
        width: 1200,
        height: 800,
        title: 'DataLogicEngine Desktop',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });
    const isDev = !electron_1.app.isPackaged;
    const url = isDev ? 'http://localhost:3000' : `file://${path.join(__dirname, '../out/index.html')}`;
    if (isDev) {
        mainWindow.loadURL(url);
        mainWindow.webContents.openDevTools();
    }
    else {
        // For production, we might need a custom protocol or serve static files
        mainWindow.loadFile(path.join(__dirname, '../out/index.html'));
    }
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}
function startBackend() {
    console.log('Starting Python backend...');
    const isDev = !electron_1.app.isPackaged;
    const rootDir = path.join(__dirname, '../../');
    let pythonPath = 'python'; // Default to system python
    let scriptPath = path.join(rootDir, 'main.py');
    if (!isDev) {
        // In production, backend is bundled as an executable
        const exeName = os.platform() === 'win32' ? 'DataLogic_Backend.exe' : 'DataLogic_Backend';
        pythonPath = path.join(process.resourcesPath, 'backend', exeName);
        scriptPath = ''; // Not used when running exe directly
    }
    const args = scriptPath ? [scriptPath] : [];
    const env = { ...process.env, PORT: '5000', FLASK_ENV: isDev ? 'development' : 'production' };
    backendProcess = (0, child_process_1.spawn)(pythonPath, args, { env, cwd: rootDir });
    backendProcess.stdout?.on('data', (data) => {
        const log = data.toString();
        console.log(`[Backend] ${log}`);
        mainWindow?.webContents.send('backend-log', log);
    });
    backendProcess.stderr?.on('data', (data) => {
        const log = data.toString();
        console.error(`[Backend Error] ${log}`);
        mainWindow?.webContents.send('backend-error', log);
    });
    backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
    });
}
electron_1.app.on('ready', () => {
    startBackend();
    createWindow();
});
electron_1.app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        electron_1.app.quit();
    }
});
electron_1.app.on('quit', () => {
    if (backendProcess) {
        console.log('Terminating Python backend...');
        backendProcess.kill();
    }
});
electron_1.app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});
// IPC Handlers
electron_1.ipcMain.handle('ping', () => 'pong');
electron_1.ipcMain.handle('get-backend-status', () => {
    return backendProcess ? (backendProcess.exitCode === null ? 'running' : 'stopped') : 'not_started';
});
