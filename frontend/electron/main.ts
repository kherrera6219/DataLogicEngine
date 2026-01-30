import { app, BrowserWindow, ipcMain, protocol, net } from 'electron';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import * as os from 'os';
import * as fs from 'fs';

let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;

// Register the custom scheme 'app' as privileged
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true, supportFetchAPI: true, corsEnabled: true } }
]);

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'DataLogicEngine Desktop',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });

  // Security: Stop navigation to external sites unless specifically allowed
  mainWindow.webContents.on('will-navigate', (event, url) => {
    const parsedUrl = new URL(url);
    if (parsedUrl.protocol !== 'app:' && parsedUrl.origin !== 'http://localhost:3000') {
      console.warn(`Blocked navigation to: ${url}`);
      event.preventDefault();
    }
  });

  // Security: Block new window creation
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    console.warn(`Blocked window open request to: ${url}`);
    return { action: 'deny' };
  });

  const isDev = !app.isPackaged;
  
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load via custom protocol
    mainWindow.loadURL('app://index.html');
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  // Register protocol handler for 'app://'
  protocol.handle('app', async (request) => {
    const url = new URL(request.url);
    let pathname = url.pathname;

    // Remove leading slash if present (Windows compatibility)
    if (pathname.startsWith('/')) {
      pathname = pathname.slice(1);
    }
    
    // Default to index.html if empty path
    if (!pathname) {
      pathname = 'index.html';
    }

    // Determine path to the 'out' directory
    // When packaged, __dirname is inside resources/app.asar/dist-electron
    // The 'out' folder is at resources/app.asar/out
    const appPath = path.join(__dirname, '../out');
    let filePath = path.join(appPath, pathname);

    // If file doesn't exist, try appending .html (for clean URLs) or serve index.html (SPA routing)
    let finalPath = filePath;
    try {
        if (!fs.existsSync(filePath)) {
            if (fs.existsSync(filePath + '.html')) {
                finalPath = filePath + '.html';
            } else {
                 // Fallback to index.html for client-side routing
                 finalPath = path.join(appPath, 'index.html');
            }
        }
    } catch (e) {
        // Fallback for whatever reason (e.g. invalid path chars)
        finalPath = path.join(appPath, 'index.html');
    }

    try {
        const data = await fs.promises.readFile(finalPath);
        const extension = path.extname(finalPath).toLowerCase();
        let mimeType = 'text/html';

        if (extension === '.js') mimeType = 'text/javascript';
        else if (extension === '.css') mimeType = 'text/css';
        else if (extension === '.json') mimeType = 'application/json';
        else if (extension === '.png') mimeType = 'image/png';
        else if (extension === '.jpg' || extension === '.jpeg') mimeType = 'image/jpeg';
        else if (extension === '.svg') mimeType = 'image/svg+xml';
        else if (extension === '.ico') mimeType = 'image/x-icon';

        return new Response(data, {
            headers: { 'content-type': mimeType }
        });
    } catch (error) {
        console.error('Failed to read file:', finalPath, error);
        return new Response('Not Found', { status: 404 });
    }
  });

  // Security: Set CSP headers
  const { session } = require('electron'); // Inline require for session to avoid early access
  session.defaultSession.webRequest.onHeadersReceived((details: any, callback: any) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self' app:; " +
          "script-src 'self' 'unsafe-inline' app:; " +
          "style-src 'self' 'unsafe-inline' app:; " +
          "img-src 'self' data: https: app:; " +
          "connect-src 'self' http://localhost:5000 https://api.openai.com https://api.anthropic.com app:; " +
          "font-src 'self' data: app:;"
        ]
      }
    });
  });

  startBackend();
  createWindow();
});

function startBackend() {
  console.log('Starting Python backend... v0.1.1');
  
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
  const env = { 
    ...process.env, 
    PORT: '5000', 
    FLASK_ENV: isDev ? 'development' : 'production',
    IS_DESKTOP_APP: 'true' 
  };

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

// (This tool call is strictly for deleting the old block, so empty replacement or comments)
// Old app.on('ready') removed because it is now handled above with protocol registration.


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

ipcMain.handle('get-db-status', () => {
  // This is a simplification; a real check would query the ports
  return backendProcess ? 'managed' : 'offline';
});
