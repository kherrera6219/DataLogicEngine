import { app, BrowserWindow, ipcMain, protocol, session } from 'electron';
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
    mainWindow.loadURL('http://localhost:3000/dashboard');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load via custom protocol
    mainWindow.loadURL('app://-/dashboard');
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  // Register protocol handler for 'app://'
  protocol.handle('app', async (request) => {
    const url = new URL(request.url);
    const appPath = path.join(__dirname, '../out');
    const hostSegment =
      url.hostname && url.hostname !== '-' ? `/${decodeURIComponent(url.hostname)}` : '';
    const logicalPathname = `${hostSegment}${url.pathname || '/'}`.replace(/\/{2,}/g, '/');

    const cleanSegments = logicalPathname.split('/').filter(Boolean);
    if (
      cleanSegments.length === 2 &&
      cleanSegments[0] === 'projects' &&
      cleanSegments[1] !== 'view'
    ) {
      const legacyId = decodeURIComponent(cleanSegments[1]);
      const redirected = `app://-/projects/view?id=${encodeURIComponent(legacyId)}`;
      return Response.redirect(redirected, 302);
    }

    const resolveFilePath = (rawPathname: string): string => {
      const decodedPath = decodeURIComponent(rawPathname || '/');
      const stripped = decodedPath.replace(/^\/+/, '').replace(/\/+$/, '');
      const normalized = path.normalize(stripped || 'index').replace(/^(\.\.(\/|\\|$))+/, '');
      const hasExtension = path.extname(normalized).length > 0;

      const candidatePaths: string[] = [path.join(appPath, normalized)];
      if (!hasExtension) {
        candidatePaths.push(path.join(appPath, `${normalized}.html`));
        candidatePaths.push(path.join(appPath, normalized, 'index.html'));
      }
      candidatePaths.push(path.join(appPath, 'index.html'));

      for (const candidate of candidatePaths) {
        try {
          const stats = fs.statSync(candidate);
          if (stats.isFile()) {
            return candidate;
          }
          if (stats.isDirectory()) {
            const directoryIndex = path.join(candidate, 'index.html');
            if (fs.existsSync(directoryIndex) && fs.statSync(directoryIndex).isFile()) {
              return directoryIndex;
            }
          }
        } catch {
          // Ignore and continue to next candidate.
        }
      }

      return path.join(appPath, 'index.html');
    };

    const finalPath = resolveFilePath(logicalPathname);

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

  // Tag desktop-originated requests so Next middleware can bypass web login redirects.
  session.defaultSession.webRequest.onBeforeSendHeaders((details, callback) => {
    const requestHeaders = { ...details.requestHeaders };
    if (
      details.url.startsWith('http://localhost:3000') ||
      details.url.startsWith('http://127.0.0.1:3000')
    ) {
      requestHeaders['X-DataLogic-Desktop'] = 'true';
    }

    callback({ requestHeaders });
  });

  // Security: Set CSP headers
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
    IS_DESKTOP_APP: 'true',
    SESSION_COOKIE_SECURE: 'false',
    SESSION_COOKIE_SAMESITE: 'Lax',
    CORS_ORIGINS: 'http://localhost:3000,http://127.0.0.1:3000,app://dashboard,app://-'
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
