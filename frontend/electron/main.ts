import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import * as os from 'os';

let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'DataLogicEngine Desktop',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  const isDev = !app.isPackaged;
  const url = isDev ? 'http://localhost:3000' : `file://${path.join(__dirname, '../out/index.html')}`;

  if (isDev) {
    mainWindow.loadURL(url);
    mainWindow.webContents.openDevTools();
  } else {
    // For production, we might need a custom protocol or serve static files
    mainWindow.loadFile(path.join(__dirname, '../out/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  console.log('Starting Python backend...');
  
  const isDev = !app.isPackaged;
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

  backendProcess = spawn(pythonPath, args, { env, cwd: rootDir });

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

app.on('ready', () => {
  startBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('quit', () => {
  if (backendProcess) {
    console.log('Terminating Python backend...');
    backendProcess.kill();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// IPC Handlers
ipcMain.handle('ping', () => 'pong');

ipcMain.handle('get-backend-status', () => {
  return backendProcess ? (backendProcess.exitCode === null ? 'running' : 'stopped') : 'not_started';
});
