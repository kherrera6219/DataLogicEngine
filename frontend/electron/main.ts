import { app, BrowserWindow, dialog, ipcMain, protocol, safeStorage, session } from 'electron';
import type { IpcMainInvokeEvent, OpenDialogOptions } from 'electron';
import { autoUpdater } from 'electron-updater';
import * as path from 'path';
import { spawn, ChildProcess } from 'child_process';
import * as os from 'os';
import * as fs from 'fs';
import * as crypto from 'crypto';

let mainWindow: BrowserWindow | null = null;
let splashWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;
let desktopInstallSecret = '';
let updateCheckTimer: NodeJS.Timeout | null = null;
let intentionalBackendShutdown = false;
let backendRestartAttempts = 0;

app.setName('DataLogicEngine Desktop');

type UpdateStatus =
  | 'disabled'
  | 'idle'
  | 'checking'
  | 'available'
  | 'not_available'
  | 'downloaded'
  | 'error';

type UpdateState = {
  enabled: boolean;
  status: UpdateStatus;
  lastCheckAt: string | null;
  currentVersion: string;
  availableVersion: string | null;
  message: string;
};

type ObjectStoreBucketStats = Record<string, { object_count: number; total_bytes: number }>;

type StructuredMemoryStats = {
  memory_vertices: number;
  memory_edges: number;
  last_recall_timestamp: string | null;
};

const ALLOWED_IPC_ORIGINS = ['app://', 'http://localhost:3000', 'http://127.0.0.1:3000'];
const DESKTOP_SECRET_PREFIX = 'enc:v1:';
const MAX_DESKTOP_LOG_FILE_BYTES = 5 * 1024 * 1024;
const AUTO_UPDATE_CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000;
const BACKEND_HEALTH_TIMEOUT_MS = 60 * 1000;
const MAX_BACKEND_RESTART_ATTEMPTS = 3;

const updateState: UpdateState = {
  enabled: false,
  status: 'disabled',
  lastCheckAt: null,
  currentVersion: app.getVersion(),
  availableVersion: null,
  message: 'Auto-update is disabled.',
};

function desktopSecretFilePath(): string {
  return path.join(app.getPath('userData'), 'desktop-install-secret');
}

function desktopLogFilePath(): string {
  return path.join(app.getPath('userData'), 'logs', 'desktop-runtime.log');
}

function desktopRuntimeDir(): string {
  return path.join(app.getPath('userData'), 'runtime');
}

function desktopSecretVaultDir(): string {
  return path.join(app.getPath('userData'), 'secrets');
}

async function responseJson<T>(response: Response): Promise<T> {
  return (await response.json()) as T;
}

function normalizeLogLine(raw: string): string {
  return raw.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim();
}

function secureDirectoryBestEffort(targetPath: string): void {
  try {
    fs.mkdirSync(targetPath, { recursive: true });
    fs.chmodSync(targetPath, 0o700);
  } catch {
    // Best-effort hardening. Some platforms do not apply chmod semantics.
  }
}

function appendDesktopLog(level: 'INFO' | 'WARN' | 'ERROR', rawMessage: string): void {
  const message = normalizeLogLine(rawMessage);
  if (!message) {
    return;
  }

  const logPath = desktopLogFilePath();
  const logDir = path.dirname(logPath);
  secureDirectoryBestEffort(logDir);

  try {
    if (fs.existsSync(logPath)) {
      const size = fs.statSync(logPath).size;
      if (size > MAX_DESKTOP_LOG_FILE_BYTES) {
        fs.truncateSync(logPath, 0);
      }
    }
    const line = `${new Date().toISOString()} [${level}] ${message}\n`;
    fs.appendFileSync(logPath, line, { encoding: 'utf8', mode: 0o600 });
  } catch {
    // Logging must never block app startup/runtime.
  }
}

function readStoredDesktopSecret(secretPath: string): string | null {
  if (!fs.existsSync(secretPath)) {
    return null;
  }

  const storedValue = fs.readFileSync(secretPath, 'utf8').trim();
  if (!storedValue) {
    return null;
  }

  if (!storedValue.startsWith(DESKTOP_SECRET_PREFIX)) {
    return storedValue;
  }

  if (!safeStorage.isEncryptionAvailable()) {
    return null;
  }

  const encryptedPayload = storedValue.slice(DESKTOP_SECRET_PREFIX.length);
  const decrypted = safeStorage.decryptString(Buffer.from(encryptedPayload, 'base64')).trim();
  return decrypted || null;
}

function persistDesktopSecret(secretPath: string, secret: string): void {
  const useSafeStorage = safeStorage.isEncryptionAvailable();
  const payload = useSafeStorage
    ? `${DESKTOP_SECRET_PREFIX}${safeStorage.encryptString(secret).toString('base64')}`
    : secret;

  secureDirectoryBestEffort(path.dirname(secretPath));
  fs.writeFileSync(secretPath, payload, { encoding: 'utf8', mode: 0o600 });
}

function loadOrCreatePlainSecretFile(secretName: string): string {
  const secretPath = path.join(desktopSecretVaultDir(), `${secretName.toLowerCase()}.secret`);

  try {
    const existing = fs.existsSync(secretPath)
      ? fs.readFileSync(secretPath, 'utf8').trim()
      : '';
    if (existing) {
      return secretPath;
    }
  } catch {
    appendDesktopLog('WARN', `Failed to read ${secretName} secret file; rotating desktop-managed secret.`);
  }

  secureDirectoryBestEffort(path.dirname(secretPath));
  fs.writeFileSync(secretPath, crypto.randomBytes(32).toString('hex'), {
    encoding: 'utf8',
    mode: 0o600,
  });
  return secretPath;
}

function loadOrCreateDesktopInstallSecret(): string {
  const envSecret = (process.env.DESKTOP_INSTALL_SECRET || '').trim();
  if (envSecret) {
    return envSecret;
  }

  const secretPath = desktopSecretFilePath();
  try {
    const existing = readStoredDesktopSecret(secretPath);
    if (existing) {
      // Migrate plaintext to safeStorage-protected payload when available.
      const existingRaw = fs.readFileSync(secretPath, 'utf8').trim();
      if (
        safeStorage.isEncryptionAvailable() &&
        existingRaw &&
        !existingRaw.startsWith(DESKTOP_SECRET_PREFIX)
      ) {
        persistDesktopSecret(secretPath, existing);
      }
      return existing;
    }
  } catch (error) {
    console.warn('Failed to read desktop install secret file, generating new secret', error);
    appendDesktopLog('WARN', 'Failed to read desktop install secret file; generating a new secret.');
  }

  const generated = crypto.randomBytes(32).toString('hex');
  try {
    persistDesktopSecret(secretPath, generated);
  } catch (error) {
    console.warn('Failed to persist desktop install secret to disk', error);
    appendDesktopLog('WARN', 'Failed to persist desktop install secret to disk.');
  }
  return generated;
}

function envFlag(name: string, defaultValue: boolean): boolean {
  const raw = (process.env[name] || '').trim().toLowerCase();
  if (!raw) {
    return defaultValue;
  }
  return raw === '1' || raw === 'true' || raw === 'yes' || raw === 'on';
}

function setUpdateState(
  status: UpdateStatus,
  message: string,
  availableVersion: string | null = updateState.availableVersion,
) {
  updateState.status = status;
  updateState.message = message;
  updateState.availableVersion = availableVersion;
}

function configureAutoUpdater(isDev: boolean): void {
  const updatesAllowed = !isDev && envFlag('DLE_AUTO_UPDATE_ENABLED', false);
  updateState.enabled = updatesAllowed;
  updateState.currentVersion = app.getVersion();

  if (!updatesAllowed) {
    setUpdateState('disabled', 'Auto-update disabled by runtime policy.', null);
    return;
  }

  const feedUrl = (process.env.DLE_AUTO_UPDATE_FEED_URL || '').trim();
  if (!feedUrl) {
    updateState.enabled = false;
    setUpdateState('disabled', 'Auto-update disabled (no feed URL configured).', null);
    return;
  }

  autoUpdater.setFeedURL({
    provider: 'generic',
    url: feedUrl,
  });

  autoUpdater.autoDownload = envFlag('DLE_AUTO_UPDATE_AUTO_DOWNLOAD', false);
  autoUpdater.autoInstallOnAppQuit = envFlag('DLE_AUTO_UPDATE_AUTO_INSTALL_ON_QUIT', true);
  setUpdateState('idle', 'Auto-update ready.', null);

  autoUpdater.on('checking-for-update', () => {
    setUpdateState('checking', 'Checking for updates...', null);
  });

  autoUpdater.on('update-available', (info) => {
    const version = info?.version || null;
    setUpdateState('available', 'Update available.', version);
    appendDesktopLog('INFO', `Update available: ${version || 'unknown version'}`);
  });

  autoUpdater.on('update-not-available', () => {
    setUpdateState('not_available', 'No updates available.', null);
  });

  autoUpdater.on('update-downloaded', (info) => {
    const version = info?.version || updateState.availableVersion;
    setUpdateState('downloaded', 'Update downloaded and ready to install.', version || null);
    appendDesktopLog('INFO', `Update downloaded: ${version || 'unknown version'}`);
  });

  autoUpdater.on('error', (error) => {
    const message = error instanceof Error ? error.message : String(error);
    setUpdateState('error', `Update check failed: ${message}`);
    appendDesktopLog('ERROR', `Auto-update error: ${message}`);
  });

  const checkForUpdates = async () => {
    if (!updateState.enabled) {
      return;
    }
    updateState.lastCheckAt = new Date().toISOString();
    try {
      await autoUpdater.checkForUpdates();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setUpdateState('error', `Update check failed: ${message}`);
    }
  };

  void checkForUpdates();
  updateCheckTimer = setInterval(() => {
    void checkForUpdates();
  }, AUTO_UPDATE_CHECK_INTERVAL_MS);
}

function readHeaderValue(
  headers: Record<string, string | string[] | undefined>,
  canonicalName: string,
): string | null {
  const exactValue = headers[canonicalName];
  if (typeof exactValue === 'string') {
    return exactValue;
  }
  if (Array.isArray(exactValue) && exactValue.length > 0) {
    return String(exactValue[0]);
  }

  const lowered = canonicalName.toLowerCase();
  const matchKey = Object.keys(headers).find((key) => key.toLowerCase() === lowered);
  if (!matchKey) {
    return null;
  }

  const matchedValue = headers[matchKey];
  if (typeof matchedValue === 'string') {
    return matchedValue;
  }
  if (Array.isArray(matchedValue) && matchedValue.length > 0) {
    return String(matchedValue[0]);
  }
  return null;
}

function setHeaderValue(
  headers: Record<string, string | string[] | undefined>,
  canonicalName: string,
  value: string,
): void {
  const lowered = canonicalName.toLowerCase();
  for (const key of Object.keys(headers)) {
    if (key.toLowerCase() === lowered && key !== canonicalName) {
      delete headers[key];
    }
  }
  headers[canonicalName] = value;
}

function signDesktopAuthPayload(payload: string): string {
  return crypto
    .createHmac('sha256', desktopInstallSecret)
    .update(payload, 'utf8')
    .digest('hex');
}

function signDesktopAuthNonce(nonce: string): string {
  return signDesktopAuthPayload(nonce);
}

function signedDesktopRequestPayload(method: string, requestUrl: string, timestamp: string): string {
  const parsedUrl = new URL(requestUrl);
  return `${method.toUpperCase()}\n${parsedUrl.pathname}${parsedUrl.search}\n${timestamp}`;
}

function isTrustedIpcSender(event: IpcMainInvokeEvent): boolean {
  const senderUrl = event.senderFrame?.url || event.sender.getURL();
  return ALLOWED_IPC_ORIGINS.some((origin) => senderUrl.startsWith(origin));
}

function assertTrustedIpcInvoke(event: IpcMainInvokeEvent, channel: string, args: unknown[]) {
  if (!isTrustedIpcSender(event)) {
    throw new Error(`Blocked untrusted IPC sender for channel "${channel}"`);
  }
  if (args.length > 0) {
    throw new Error(`Blocked unexpected IPC payload for channel "${channel}"`);
  }
}

// Register the custom scheme 'app' as privileged
protocol.registerSchemesAsPrivileged([
  { scheme: 'app', privileges: { secure: true, standard: true, supportFetchAPI: true, corsEnabled: true } }
]);

function createWindow() {
  const isDev = !app.isPackaged;

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'DataLogicEngine Desktop',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webviewTag: false,
      devTools: isDev,
      spellcheck: false,
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

  if (isDev) {
    mainWindow.loadURL('http://localhost:3000/dashboard');
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load via custom protocol
    mainWindow.loadURL('app://-/');
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function assertTrustedIpcSender(event: IpcMainInvokeEvent, channel: string): void {
  if (!isTrustedIpcSender(event)) {
    throw new Error(`Blocked untrusted IPC sender for channel "${channel}"`);
  }
}

function desktopRequestHeaders(method: string, requestUrl: string): Record<string, string> {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  return {
    'Content-Type': 'application/json',
    'X-DataLogic-Desktop': 'true',
    'X-Desktop-Auth-Timestamp': timestamp,
    'X-Desktop-Auth-Request-Signature': signDesktopAuthPayload(
      signedDesktopRequestPayload(method, requestUrl, timestamp),
    ),
  };
}

function desktopFetch(requestUrl: string, init: RequestInit = {}): Promise<Response> {
  const method = (init.method || 'GET').toString().toUpperCase();
  return fetch(requestUrl, {
    ...init,
    method,
    headers: {
      ...desktopRequestHeaders(method, requestUrl),
      ...(init.headers as Record<string, string> | undefined),
    },
  });
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 420,
    height: 220,
    resizable: false,
    frame: false,
    show: true,
    title: 'Starting DataLogicEngine',
    webPreferences: {
      contextIsolation: true,
      sandbox: true,
    },
  });

  const html = `
    <html>
      <body style="margin:0;background:#0f172a;color:#e2e8f0;font-family:Segoe UI,Arial,sans-serif;display:grid;place-items:center;height:100vh">
        <main style="text-align:center">
          <h1 style="font-size:18px;font-weight:600;margin:0 0 10px">DataLogicEngine</h1>
          <p style="font-size:13px;margin:0;color:#94a3b8">Starting local reasoning services...</p>
        </main>
      </body>
    </html>
  `;
  void splashWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);
  splashWindow.on('closed', () => {
    splashWindow = null;
  });
}

async function waitForBackendHealth(timeoutMs = BACKEND_HEALTH_TIMEOUT_MS): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (!backendProcess || backendProcess.exitCode !== null) {
      return false;
    }
    try {
      const response = await fetch('http://127.0.0.1:5000/health');
      if (response.ok) {
        backendRestartAttempts = 0;
        appendDesktopLog('INFO', 'Backend health check passed.');
        return true;
      }
    } catch {
      // Backend is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  appendDesktopLog('WARN', 'Backend health check timed out after 60 seconds.');
  return false;
}

app.on('ready', async () => {
  const isDev = !app.isPackaged;
  appendDesktopLog('INFO', `Desktop runtime booting (packaged=${app.isPackaged})`);
  desktopInstallSecret = loadOrCreateDesktopInstallSecret();
  configureAutoUpdater(isDev);
  createSplashWindow();

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

      const resolvedAppPath = path.resolve(appPath);
      const candidatePaths: string[] = [path.join(appPath, normalized)];
      if (!hasExtension) {
        candidatePaths.push(path.join(appPath, `${normalized}.html`));
        candidatePaths.push(path.join(appPath, normalized, 'index.html'));
      }
      candidatePaths.push(path.join(appPath, 'index.html'));

      for (const candidate of candidatePaths) {
        // Security: reject any resolved path that escapes the app output directory.
        const resolvedCandidate = path.resolve(candidate);
        if (
          resolvedCandidate !== resolvedAppPath &&
          !resolvedCandidate.startsWith(resolvedAppPath + path.sep)
        ) {
          continue;
        }
        try {
          const stats = fs.statSync(resolvedCandidate);
          if (stats.isFile()) {
            return resolvedCandidate;
          }
          if (stats.isDirectory()) {
            const directoryIndex = path.join(resolvedCandidate, 'index.html');
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
      setHeaderValue(requestHeaders, 'X-DataLogic-Desktop', 'true');
    }

    if (
      details.url.startsWith('http://localhost:5000') ||
      details.url.startsWith('http://127.0.0.1:5000')
    ) {
      setHeaderValue(requestHeaders, 'X-DataLogic-Desktop', 'true');
      const timestamp = Math.floor(Date.now() / 1000).toString();
      setHeaderValue(requestHeaders, 'X-Desktop-Auth-Timestamp', timestamp);
      setHeaderValue(
        requestHeaders,
        'X-Desktop-Auth-Request-Signature',
        signDesktopAuthPayload(
          signedDesktopRequestPayload(details.method || 'GET', details.url, timestamp),
        ),
      );

      const nonce = (readHeaderValue(requestHeaders, 'X-Desktop-Auth-Nonce') || '').trim();
      if (nonce && desktopInstallSecret) {
        setHeaderValue(requestHeaders, 'X-Desktop-Auth-Signature', signDesktopAuthNonce(nonce));
      }
    }

    callback({ requestHeaders });
  });

  // Security: Set CSP headers on all responses.
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    const scriptSrc = "'self' 'unsafe-inline' app:";
    const styleSrc = "'self' 'unsafe-inline' app:";

    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self' app:; " +
          `script-src ${scriptSrc}; ` +
          `style-src ${styleSrc}; ` +
          "img-src 'self' data: https: app:; " +
          "connect-src 'self' http://localhost:5000 https://api.openai.com https://api.anthropic.com app:; " +
          "font-src 'self' data: app:;"
        ]
      }
    });
  });

  startBackend();
  await waitForBackendHealth();
  createWindow();
  splashWindow?.close();
});

function startBackend() {
  intentionalBackendShutdown = false;
  console.log('Starting Python backend... v0.1.1');
  appendDesktopLog('INFO', 'Starting backend process.');
  
  const isDev = !app.isPackaged;
  const rootDir = path.join(__dirname, '../../');
  const runtimeDir = isDev ? rootDir : desktopRuntimeDir();
  secureDirectoryBestEffort(runtimeDir);
  secureDirectoryBestEffort(path.join(runtimeDir, 'logs'));
  secureDirectoryBestEffort(path.join(runtimeDir, 'instance'));

  // In production, create a template .env in the runtime directory if none exists.
  // This gives the user a clear, documented location to add API keys.
  if (!isDev) {
    const runtimeEnv = path.join(runtimeDir, '.env');
    if (!fs.existsSync(runtimeEnv)) {
      const template = [
        '# DataLogicEngine Desktop — API Keys',
        '# Place your API keys below. The app will read this file on startup.',
        '#',
        '# OpenAI (GPT-5.5):',
        'OPENAI_API_KEY=',
        '#',
        '# Google Gemini (gemini-3.1-pro):',
        'GOOGLE_API_KEY=',
        '#',
        '# Anthropic (optional):',
        '# ANTHROPIC_API_KEY=',
        '',
      ].join('\n');
      try {
        fs.writeFileSync(runtimeEnv, template, 'utf8');
        appendDesktopLog('INFO', `Created template .env at: ${runtimeEnv}`);
      } catch (err) {
        appendDesktopLog('WARN', `Failed to create template .env: ${String(err)}`);
      }
    }
  }
  
  let pythonPath = 'python'; // Default to system python
  let scriptPath = path.join(rootDir, 'main.py');
  
  if (!isDev) {
    // In production, backend is bundled as an executable
    const exeName = os.platform() === 'win32' ? 'DataLogic_Backend.exe' : 'DataLogic_Backend';
    pythonPath = path.join(process.resourcesPath, 'backend', exeName);
    scriptPath = ''; // Not used when running exe directly
  }

  const args = scriptPath ? [scriptPath] : [];
  const sessionSecretFile = loadOrCreatePlainSecretFile('SESSION_SECRET');
  const encryptionKekSecretFile = loadOrCreatePlainSecretFile('ENCRYPTION_KEK_SECRET');
  const encryptionKekSecret = fs.readFileSync(encryptionKekSecretFile, 'utf8').trim();
  // Read API keys from .env so they reach the backend even when Electron's
  // process.env doesn't carry them (avoids "No active providers found").
  // In production, rootDir points to the packaged resources/ dir (no .env),
  // so we also check runtimeDir (%APPDATA%/DataLogicEngine Desktop/runtime/).
  const dotenvKeys: Record<string, string> = {};
  const dotenvCandidates = [
    path.join(runtimeDir, '.env'),   // User-writable location (preferred in production)
    path.join(rootDir, '.env'),      // Dev location / repo root
  ];
  for (const dotenvPath of dotenvCandidates) {
    if (fs.existsSync(dotenvPath)) {
      appendDesktopLog('INFO', `Loading .env from: ${dotenvPath}`);
      const lines = fs.readFileSync(dotenvPath, 'utf8').split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eqIdx = trimmed.indexOf('=');
        if (eqIdx === -1) continue;
        const k = trimmed.slice(0, eqIdx).trim();
        const v = trimmed.slice(eqIdx + 1).trim();
        // Only set if not already set by a higher-priority source
        if (k && !(k in dotenvKeys)) dotenvKeys[k] = v;
      }
      break;  // Use the first .env found
    }
  }

  const env = {
    ...dotenvKeys,       // .env values first (lowest priority)
    ...process.env,      // Electron inherited env overrides .env
    PORT: '5000', 
    FLASK_ENV: isDev ? 'development' : 'production',
    IS_DESKTOP_APP: 'true',
    SESSION_COOKIE_SECURE: 'false',
    SESSION_COOKIE_SAMESITE: 'Lax',
    CORS_ORIGINS: 'http://localhost:3000,http://127.0.0.1:3000,app://dashboard,app://-',
    DESKTOP_INSTALL_SECRET: desktopInstallSecret,
    SESSION_SECRET_FILE: sessionSecretFile,
    ENCRYPTION_KEK_SECRET: encryptionKekSecret,
    DATABASE_URL: `sqlite:///${path.join(runtimeDir, 'ukg_database.db').replace(/\\/g, '/')}`,
    LOG_FILE: path.join(runtimeDir, 'logs', 'app.log'),
    DATALOGIC_STORAGE_SETTINGS_PATH: path.join(runtimeDir, 'settings.json'),
    AUTO_CREATE_SCHEMA: isDev ? 'False' : 'true',
    LLAMA_INDEX_CACHE_DIR: path.join(runtimeDir, 'cache', 'llama_index'),
    HF_HOME: path.join(runtimeDir, 'cache', 'huggingface'),
    TRANSFORMERS_CACHE: path.join(runtimeDir, 'cache', 'huggingface'),
    NLTK_DATA: path.join(runtimeDir, 'cache', 'nltk_data'),
  };

  appendDesktopLog('INFO', `Backend working directory: ${runtimeDir}`);
  
  // Ensure cache directories exist
  secureDirectoryBestEffort(path.join(runtimeDir, 'cache'));
  secureDirectoryBestEffort(path.join(runtimeDir, 'cache', 'llama_index'));
  secureDirectoryBestEffort(path.join(runtimeDir, 'cache', 'huggingface'));
  secureDirectoryBestEffort(path.join(runtimeDir, 'cache', 'nltk_data'));

  backendProcess = spawn(pythonPath, args, { env, cwd: runtimeDir });

  backendProcess.stdout?.on('data', (data) => {
    const log = data.toString();
    console.log(`[Backend] ${log}`);
    mainWindow?.webContents.send('backend-log', log);
    appendDesktopLog('INFO', `[Backend] ${log}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    const log = data.toString();
    console.error(`[Backend Error] ${log}`);
    mainWindow?.webContents.send('backend-error', log);
    appendDesktopLog('ERROR', `[Backend Error] ${log}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
    appendDesktopLog('WARN', `Backend process exited with code ${String(code)}`);
    if (!intentionalBackendShutdown && backendRestartAttempts < MAX_BACKEND_RESTART_ATTEMPTS) {
      backendRestartAttempts += 1;
      appendDesktopLog(
        'WARN',
        `Restarting backend after unexpected exit (${backendRestartAttempts}/${MAX_BACKEND_RESTART_ATTEMPTS}).`,
      );
      setTimeout(() => startBackend(), 1500);
      return;
    }
    if (!intentionalBackendShutdown && backendRestartAttempts >= MAX_BACKEND_RESTART_ATTEMPTS) {
      mainWindow?.webContents.send(
        'backend-error',
        `Backend exited repeatedly and will not restart automatically. Last exit code: ${String(code)}`,
      );
    }
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
  if (updateCheckTimer) {
    clearInterval(updateCheckTimer);
    updateCheckTimer = null;
  }

  if (backendProcess) {
    console.log('Terminating Python backend...');
    intentionalBackendShutdown = true;
    backendProcess.kill();
    appendDesktopLog('INFO', 'Backend process termination requested.');
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// IPC Handlers
ipcMain.handle('ping', (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'ping', args);
  return 'pong';
});

ipcMain.handle('get-backend-status', (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'get-backend-status', args);
  return backendProcess ? (backendProcess.exitCode === null ? 'running' : 'stopped') : 'not_started';
});

ipcMain.handle('get-db-status', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'get-db-status', args);
  if (!backendProcess || backendProcess.exitCode !== null) {
    return { status: 'offline', chroma_collections: {}, redis_ping_ms: null, object_store_buckets: {}, memory_vertices: 0, memory_edges: 0, last_recall_timestamp: null };
  }

  try {
    const response = await fetch('http://127.0.0.1:5000/health');
    const payload = await responseJson<{
      database?: {
        status?: string;
        chromadb?: { collections?: Record<string, number> };
        redis?: { ping_ms?: number | null };
        object_store?: { buckets?: ObjectStoreBucketStats };
        memory?: StructuredMemoryStats;
      };
    }>(response);
    return {
      status: payload?.database?.status === 'ok' ? 'managed' : 'degraded',
      chroma_collections: payload?.database?.chromadb?.collections ?? {},
      redis_ping_ms: payload?.database?.redis?.ping_ms ?? null,
      object_store_buckets: payload?.database?.object_store?.buckets ?? {},
      memory_vertices: payload?.database?.memory?.memory_vertices ?? 0,
      memory_edges: payload?.database?.memory?.memory_edges ?? 0,
      last_recall_timestamp: payload?.database?.memory?.last_recall_timestamp ?? null,
    };
  } catch {
    return { status: 'managed', chroma_collections: {}, redis_ping_ms: null, object_store_buckets: {}, memory_vertices: 0, memory_edges: 0, last_recall_timestamp: null };
  }
});

ipcMain.handle('quad-analysis-status', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'quad-analysis-status', args);
  if (!backendProcess || backendProcess.exitCode !== null) {
    return { pod_count: 0, collective_confidence: 0, mode: 'offline' };
  }

  try {
    const response = await desktopFetch('http://127.0.0.1:5000/api/v1/gateway/quad-analysis-status');
    const payload = await responseJson<{
      pod_count?: number;
      collective_confidence?: number;
      mode?: string;
    }>(response);
    return {
      pod_count: payload?.pod_count ?? 0,
      collective_confidence: payload?.collective_confidence ?? 0,
      mode: payload?.mode ?? 'unknown',
    };
  } catch {
    return { pod_count: 0, collective_confidence: 0, mode: 'unavailable' };
  }
});

ipcMain.handle('dmrf-status', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'dmrf-status', args);
  if (!backendProcess || backendProcess.exitCode !== null) {
    return { status: 'offline' };
  }

  try {
    const response = await desktopFetch('http://127.0.0.1:5000/api/v1/gateway/dmrf-status');
    const payload = await responseJson<{
      status?: string;
      tier?: string | null;
      frost_depth?: number | null;
      run_id?: string | null;
      tier_counts?: Record<string, number>;
    }>(response);
    return {
      status: payload?.status ?? 'idle',
      tier: payload?.tier ?? null,
      frost_depth: payload?.frost_depth ?? null,
      run_id: payload?.run_id ?? null,
      tier_counts: payload?.tier_counts ?? {},
    };
  } catch {
    return { status: 'unavailable' };
  }
});

ipcMain.handle('dsqp-persona-profiles', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'dsqp-persona-profiles', args);
  if (!backendProcess || backendProcess.exitCode !== null) {
    return { success: false, profiles: [], partial: true, failures: { backend: 'offline' } };
  }

  try {
    const response = await desktopFetch('http://127.0.0.1:5000/api/v1/gateway/dsqp-persona-profiles');
    const payload = await responseJson<{
      success?: boolean;
      profiles?: unknown[];
      partial?: boolean;
      failures?: Record<string, string>;
    }>(response);
    return {
      success: Boolean(payload?.success),
      profiles: Array.isArray(payload?.profiles) ? payload.profiles : [],
      partial: Boolean(payload?.partial),
      failures: payload?.failures ?? {},
    };
  } catch {
    return { success: false, profiles: [], partial: true, failures: { dsqp: 'unavailable' } };
  }
});

ipcMain.handle('network-status', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'network-status', args);
  if (!backendProcess || backendProcess.exitCode !== null) {
    return { state: 'OFFLINE', last_checked: new Date().toISOString(), active_provider: null, details: {} };
  }

  try {
    const response = await desktopFetch('http://127.0.0.1:5000/api/v1/gateway/network-status');
    const payload = await responseJson<{
      state?: string;
      last_checked?: string;
      active_provider?: string | null;
      details?: Record<string, unknown>;
    }>(response);
    return {
      state: payload?.state ?? 'DEGRADED',
      last_checked: payload?.last_checked ?? new Date().toISOString(),
      active_provider: payload?.active_provider ?? null,
      details: payload?.details ?? {},
    };
  } catch {
    return { state: 'DEGRADED', last_checked: new Date().toISOString(), active_provider: null, details: {} };
  }
});

ipcMain.handle('local-model-status', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'local-model-status', args);
  try {
    const response = await fetch('http://127.0.0.1:11434/api/tags');
    if (!response.ok) {
      return { ollama_available: false, models_installed: [], active_model: null };
    }
    const payload = await responseJson<{ models?: Array<{ name?: string }> }>(response);
    const models = Array.isArray(payload?.models)
      ? payload.models.map((model) => model.name).filter((name): name is string => Boolean(name))
      : [];
    return { ollama_available: true, models_installed: models, active_model: models[0] ?? null };
  } catch {
    return { ollama_available: false, models_installed: [], active_model: null };
  }
});

ipcMain.handle('reasoning-layer-progress', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'reasoning-layer-progress', args);
  if (!backendProcess || backendProcess.exitCode !== null) {
    return {
      active_run_id: null,
      status: 'offline',
      current_layer: null,
      layer_name: null,
      kas_running: [],
      confidence_so_far: null,
      persona_confidences: [],
      frost_snapshot_count: 0,
      updated_at: new Date().toISOString(),
    };
  }

  try {
    const response = await desktopFetch('http://127.0.0.1:5000/api/v1/trace/live-progress');
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }
    return await responseJson<Record<string, unknown>>(response);
  } catch {
    return {
      active_run_id: null,
      status: 'unavailable',
      current_layer: null,
      layer_name: null,
      kas_running: [],
      confidence_so_far: null,
      persona_confidences: [],
      frost_snapshot_count: 0,
      updated_at: new Date().toISOString(),
    };
  }
});

ipcMain.handle('ka-execution-feed', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'ka-execution-feed', args);
  if (!backendProcess || backendProcess.exitCode !== null) {
    return { items: [], limit: 20, updated_at: new Date().toISOString() };
  }

  try {
    const response = await desktopFetch('http://127.0.0.1:5000/api/v1/trace/ka-execution-feed?limit=20');
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }
    return await responseJson<Record<string, unknown>>(response);
  } catch {
    return { items: [], limit: 20, updated_at: new Date().toISOString() };
  }
});

ipcMain.handle('get-desktop-storage-metrics', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'get-desktop-storage-metrics', args);
  if (!backendProcess || backendProcess.exitCode !== null) {
    return null;
  }

  const response = await desktopFetch('http://127.0.0.1:5000/api/v1/storage/desktop-metrics');
  const payload = await responseJson<{ data?: unknown }>(response);
  return payload?.data ?? payload;
});

ipcMain.handle('choose-backup-folder', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'choose-backup-folder', args);
  const options: OpenDialogOptions = {
    properties: ['openDirectory', 'createDirectory'],
    title: 'Choose DataLogicEngine backup folder',
  };
  const result = mainWindow
    ? await dialog.showOpenDialog(mainWindow, options)
    : await dialog.showOpenDialog(options);
  return result.canceled ? null : result.filePaths[0] ?? null;
});

ipcMain.handle('run-database-backup', async (event, payload?: unknown, ...args: unknown[]) => {
  assertTrustedIpcSender(event, 'run-database-backup');
  if (args.length > 0) {
    throw new Error('Blocked unexpected IPC payload for channel "run-database-backup"');
  }
  const targetDir =
    payload && typeof payload === 'object' && typeof (payload as { target_dir?: unknown }).target_dir === 'string'
      ? (payload as { target_dir: string }).target_dir
      : undefined;

  const response = await desktopFetch('http://127.0.0.1:5000/api/v1/storage/backup', {
    method: 'POST',
    body: JSON.stringify({ target_dir: targetDir }),
  });
  const result = await responseJson<{ data?: unknown; error?: string }>(response);
  if (!response.ok) {
    throw new Error(result?.error || `Backup failed with status ${response.status}`);
  }
  return result?.data ?? result;
});

ipcMain.handle('get-update-state', (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'get-update-state', args);
  return { ...updateState };
});

ipcMain.handle('check-for-updates', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'check-for-updates', args);
  if (!updateState.enabled) {
    return { ...updateState };
  }

  try {
    updateState.lastCheckAt = new Date().toISOString();
    await autoUpdater.checkForUpdates();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    setUpdateState('error', `Update check failed: ${message}`);
  }
  return { ...updateState };
});

ipcMain.handle('download-update', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'download-update', args);
  if (!updateState.enabled) {
    return { ...updateState };
  }

  if (updateState.status !== 'available') {
    return { ...updateState };
  }

  try {
    await autoUpdater.downloadUpdate();
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    setUpdateState('error', `Update download failed: ${message}`);
  }
  return { ...updateState };
});
