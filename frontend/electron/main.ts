import { app, BrowserWindow, dialog, ipcMain, powerMonitor, protocol, safeStorage, session } from 'electron';
import type { IpcMainInvokeEvent, OpenDialogOptions } from 'electron';
import { autoUpdater } from 'electron-updater';
import * as path from 'path';
import { spawn, spawnSync, ChildProcess } from 'child_process';
import * as os from 'os';
import * as fs from 'fs';
import * as crypto from 'crypto';
import { runBoundedShutdown } from './lifecycle';

let mainWindow: BrowserWindow | null = null;
let splashWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;
let desktopInstallSecret = '';
let updateCheckTimer: NodeJS.Timeout | null = null;
let intentionalBackendShutdown = false;
let backendRestartAttempts = 0;
let gracefulQuitStarted = false;
let clockDriftTimer: NodeJS.Timeout | null = null;

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

type PathCapability = {
  path: string;
  purpose: 'backup' | 'ingestion';
  expiresAt: number;
};

type JsonRecord = Record<string, unknown>;

const ALLOWED_IPC_WEB_ORIGINS = new Set(['http://localhost:3000', 'http://127.0.0.1:3000']);
const ALLOWED_IPC_APP_HOSTS = new Set(['-', 'dashboard']);
const DESKTOP_SECRET_PREFIX = 'enc:v1:';
const MAX_DESKTOP_LOG_FILE_BYTES = 5 * 1024 * 1024;
const AUTO_UPDATE_CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000;
const BACKEND_HEALTH_TIMEOUT_MS = 60 * 1000;
const MAX_BACKEND_RESTART_ATTEMPTS = 3;
const DESKTOP_SECRET_ROTATION_DAYS = 180;
const PATH_CAPABILITY_TTL_MS = 5 * 60 * 1000;
const pathCapabilities = new Map<string, PathCapability>();
const activeDesktopOperations = new Map<string, AbortController>();

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

function redactSecretsForLog(raw: string): string {
  return raw
    .replace(/\b(bearer\s+)[A-Za-z0-9._~+/=-]{8,}/gi, '$1[REDACTED_SECRET]')
    .replace(
      /\b((?:api[_-]?key|token|secret|password|authorization)\s*[:=]\s*)[^\s,;]+/gi,
      '$1[REDACTED_SECRET]',
    )
    .replace(/\bsk-[A-Za-z0-9_-]{16,}\b/g, '[REDACTED_SECRET]')
    .replace(/\bAIza[A-Za-z0-9_-]{20,}\b/g, '[REDACTED_SECRET]')
    .replace(/\bukg_[A-Za-z0-9_-]{16,}\b/g, '[REDACTED_SECRET]');
}

function safeDesktopLogMessage(raw: string): string {
  return redactSecretsForLog(normalizeLogLine(raw));
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
  const message = safeDesktopLogMessage(rawMessage);
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
  if (!useSafeStorage && app.isPackaged) {
    throw new Error('Windows protected storage is required for packaged desktop secrets');
  }
  const payload = useSafeStorage
    ? `${DESKTOP_SECRET_PREFIX}${safeStorage.encryptString(secret).toString('base64')}`
    : secret;

  secureDirectoryBestEffort(path.dirname(secretPath));
  fs.writeFileSync(secretPath, payload, { encoding: 'utf8', mode: 0o600 });
  secureWindowsAclBestEffort(secretPath);
}

function loadOrCreateProtectedSecret(secretName: string): string {
  const normalizedName = secretName.toLowerCase();
  const secretPath = path.join(desktopSecretVaultDir(), `${normalizedName}.safe-storage`);
  const legacyPlaintextPath = path.join(desktopSecretVaultDir(), `${normalizedName}.secret`);

  try {
    const existing = readStoredDesktopSecret(secretPath);
    if (existing) {
      secureWindowsAclBestEffort(secretPath);
      return existing;
    }
    if (fs.existsSync(legacyPlaintextPath)) {
      const legacySecret = fs.readFileSync(legacyPlaintextPath, 'utf8').trim();
      if (legacySecret) {
        persistDesktopSecret(secretPath, legacySecret);
        fs.rmSync(legacyPlaintextPath, { force: true });
        return legacySecret;
      }
    }
  } catch {
    appendDesktopLog('WARN', `Failed to read ${secretName} secret file; rotating desktop-managed secret.`);
  }

  const generated = crypto.randomBytes(32).toString('hex');
  persistDesktopSecret(secretPath, generated);
  return generated;
}

function migrateAndLoadPackagedDotenvSecrets(runtimeDir: string): Record<string, string> {
  const dotenvPath = path.join(runtimeDir, '.env');
  const result: Record<string, string> = {};
  const vaultDir = desktopSecretVaultDir();
  secureDirectoryBestEffort(vaultDir);

  if (fs.existsSync(dotenvPath)) {
    const rewritten: string[] = [];
    let migratedCount = 0;
    for (const line of fs.readFileSync(dotenvPath, 'utf8').split(/\r?\n/)) {
      const trimmed = line.trim();
      const eqIdx = trimmed.indexOf('=');
      if (!trimmed || trimmed.startsWith('#') || eqIdx <= 0) {
        rewritten.push(line);
        continue;
      }
      const key = trimmed.slice(0, eqIdx).trim();
      const value = trimmed.slice(eqIdx + 1).trim();
      const secretLike = /^[A-Z][A-Z0-9_]*$/.test(key) && /(KEY|SECRET|TOKEN|PASSWORD)/.test(key);
      if (secretLike && value) {
        persistDesktopSecret(path.join(vaultDir, `dotenv-${key}.safe-storage`), value);
        result[key] = value;
        rewritten.push(`${key}=`);
        migratedCount += 1;
      } else {
        rewritten.push(line);
      }
    }
    if (migratedCount > 0) {
      fs.writeFileSync(dotenvPath, rewritten.join('\n'), { encoding: 'utf8', mode: 0o600 });
      secureWindowsAclBestEffort(dotenvPath);
      appendDesktopLog('INFO', `Migrated ${migratedCount} plaintext runtime secret value(s) into Windows protected storage.`);
    }
  }

  if (fs.existsSync(vaultDir)) {
    for (const filename of fs.readdirSync(vaultDir)) {
      const match = /^dotenv-([A-Z][A-Z0-9_]*)\.safe-storage$/.exec(filename);
      if (!match) {
        continue;
      }
      const value = readStoredDesktopSecret(path.join(vaultDir, filename));
      if (value) {
        result[match[1]] = value;
      }
    }
  }
  return result;
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
      const ageMs = Math.max(0, Date.now() - fs.statSync(secretPath).mtimeMs);
      if (ageMs >= DESKTOP_SECRET_ROTATION_DAYS * 24 * 60 * 60 * 1000) {
        const rotated = crypto.randomBytes(32).toString('hex');
        persistDesktopSecret(secretPath, rotated);
        appendDesktopLog('INFO', 'Rotated the desktop install secret after its configured lifetime.');
        return rotated;
      }
      // Migrate plaintext to safeStorage-protected payload when available.
      const existingRaw = fs.readFileSync(secretPath, 'utf8').trim();
      if (
        safeStorage.isEncryptionAvailable() &&
        existingRaw &&
        !existingRaw.startsWith(DESKTOP_SECRET_PREFIX)
      ) {
        persistDesktopSecret(secretPath, existing);
      }
      secureWindowsAclBestEffort(secretPath);
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

function secureWindowsAclBestEffort(targetPath: string): void {
  if (os.platform() !== 'win32' || !fs.existsSync(targetPath)) {
    return;
  }
  try {
    const account = os.userInfo().username;
    const inheritance = fs.statSync(targetPath).isDirectory() ? '(OI)(CI)' : '';
    const result = spawnSync(
      'icacls',
      [
        targetPath,
        '/inheritance:r',
        '/grant:r',
        `${account}:${inheritance}F`,
        '/grant:r',
        `*S-1-5-18:${inheritance}F`,
      ],
      { encoding: 'utf8', windowsHide: true },
    );
    if (result.status !== 0) {
      throw new Error('icacls returned a non-zero status');
    }
  } catch {
    if (app.isPackaged) {
      throw new Error('Unable to apply the required per-user ACL');
    }
  }
}

function issuePathCapability(selectedPath: string, purpose: PathCapability['purpose']) {
  const canonicalPath = fs.realpathSync(selectedPath);
  const token = crypto.randomBytes(32).toString('base64url');
  const expiresAt = Date.now() + PATH_CAPABILITY_TTL_MS;
  pathCapabilities.set(token, { path: canonicalPath, purpose, expiresAt });
  return {
    token,
    display_name: path.basename(canonicalPath),
    expires_at: new Date(expiresAt).toISOString(),
  };
}

function consumePathCapability(token: string, purpose: PathCapability['purpose']): string {
  const capability = pathCapabilities.get(token);
  pathCapabilities.delete(token);
  if (!capability || capability.purpose !== purpose || capability.expiresAt <= Date.now()) {
    throw new Error('Selected path capability is invalid or expired');
  }
  return capability.path;
}

function requireJsonRecord(value: unknown, channel: string): JsonRecord {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`Blocked invalid IPC payload for channel "${channel}"`);
  }
  return value as JsonRecord;
}

function rejectUnknownKeys(payload: JsonRecord, allowedKeys: readonly string[], channel: string): void {
  const unknownKeys = Object.keys(payload).filter((key) => !allowedKeys.includes(key));
  if (unknownKeys.length > 0) {
    throw new Error(`Blocked unknown IPC fields for channel "${channel}"`);
  }
}

function optionalBoundedString(
  payload: JsonRecord,
  key: string,
  channel: string,
  maxLength: number,
): string | undefined {
  const value = payload[key];
  if (value === undefined) {
    return undefined;
  }
  if (typeof value !== 'string' || value.length === 0 || value.length > maxLength) {
    throw new Error(`Blocked invalid ${key} for channel "${channel}"`);
  }
  return value;
}

function optionalBoolean(payload: JsonRecord, key: string, channel: string, fallback: boolean): boolean {
  const value = payload[key];
  if (value === undefined) {
    return fallback;
  }
  if (typeof value !== 'boolean') {
    throw new Error(`Blocked invalid ${key} for channel "${channel}"`);
  }
  return value;
}

function optionalBoundedInteger(
  payload: JsonRecord,
  key: string,
  channel: string,
  fallback: number,
  minimum: number,
  maximum: number,
): number {
  const value = payload[key];
  if (value === undefined) {
    return fallback;
  }
  if (!Number.isInteger(value) || (value as number) < minimum || (value as number) > maximum) {
    throw new Error(`Blocked invalid ${key} for channel "${channel}"`);
  }
  return value as number;
}

function requiredOperationId(payload: JsonRecord, channel: string): string {
  const operationId = optionalBoundedString(payload, 'operation_id', channel, 80);
  if (!operationId || !/^[A-Za-z0-9_-]{16,80}$/.test(operationId)) {
    throw new Error(`Blocked invalid operation_id for channel "${channel}"`);
  }
  return operationId;
}

async function withCancellableDesktopOperation<T>(
  operationId: string,
  operation: (signal: AbortSignal) => Promise<T>,
): Promise<T> {
  if (activeDesktopOperations.has(operationId)) {
    throw new Error('Desktop operation identifier is already active');
  }
  const controller = new AbortController();
  activeDesktopOperations.set(operationId, controller);
  try {
    return await operation(controller.signal);
  } finally {
    activeDesktopOperations.delete(operationId);
  }
}

function responseDataRecord(payload: unknown, channel: string): JsonRecord {
  const envelope = requireJsonRecord(payload, channel);
  const value = envelope.data ?? envelope;
  return requireJsonRecord(value, channel);
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

function signedDesktopRequestPayload(
  method: string,
  requestUrl: string,
  timestamp: string,
  requestNonce = '',
): string {
  const parsedUrl = new URL(requestUrl);
  const base = `${method.toUpperCase()}\n${parsedUrl.pathname}${parsedUrl.search}\n${timestamp}`;
  return requestNonce ? `${base}\n${requestNonce}` : base;
}

function isTrustedIpcSender(event: IpcMainInvokeEvent): boolean {
  const senderUrl = event.senderFrame?.url || event.sender.getURL();
  try {
    const parsed = new URL(senderUrl);
    if (parsed.protocol === 'app:') {
      return ALLOWED_IPC_APP_HOSTS.has(parsed.hostname);
    }
    return ALLOWED_IPC_WEB_ORIGINS.has(parsed.origin);
  } catch {
    return false;
  }
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
      webSecurity: true,
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
  mainWindow.on('query-session-end', (event) => {
    const lifecycleEvent = event.reasons.includes('logoff') ? 'logoff' : 'shutdown';
    void notifyBackendLifecycleEvent(lifecycleEvent);
  });
}

function assertTrustedIpcSender(event: IpcMainInvokeEvent, channel: string): void {
  if (!isTrustedIpcSender(event)) {
    throw new Error(`Blocked untrusted IPC sender for channel "${channel}"`);
  }
}

function desktopRequestHeaders(method: string, requestUrl: string): Record<string, string> {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const requestNonce = crypto.randomBytes(24).toString('base64url');
  return {
    'Content-Type': 'application/json',
    'X-DataLogic-Desktop': 'true',
    'X-Desktop-Auth-Timestamp': timestamp,
    'X-Desktop-Auth-Request-Nonce': requestNonce,
    'X-Desktop-Auth-Request-Signature': signDesktopAuthPayload(
      signedDesktopRequestPayload(method, requestUrl, timestamp, requestNonce),
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

async function notifyBackendLifecycleEvent(
  event: 'suspend' | 'hibernate' | 'resume' | 'logoff' | 'shutdown' | 'time_changed' | 'forced_termination',
  timeoutMs = 3000,
): Promise<boolean> {
  if (!backendProcess || backendProcess.exitCode !== null) {
    return false;
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await desktopFetch(
      'http://127.0.0.1:5000/api/v1/system/lifecycle/event',
      {
        method: 'POST',
        body: JSON.stringify({ event }),
        signal: controller.signal,
      },
    );
    appendDesktopLog(response.ok ? 'INFO' : 'WARN', `Backend lifecycle event ${event}: ${response.status}`);
    return response.ok;
  } catch {
    appendDesktopLog('WARN', `Backend lifecycle event ${event} could not be delivered.`);
    return false;
  } finally {
    clearTimeout(timeout);
  }
}

function desktopIpcFetch(
  requestUrl: string,
  capability: 'backup' | 'ingestion',
  init: RequestInit = {},
): Promise<Response> {
  const method = (init.method || 'GET').toString().toUpperCase();
  const headers = desktopRequestHeaders(method, requestUrl);
  const timestamp = headers['X-Desktop-Auth-Timestamp'];
  const requestNonce = headers['X-Desktop-Auth-Request-Nonce'];
  headers['X-Desktop-IPC-Capability'] = capability;
  headers['X-Desktop-IPC-Signature'] = signDesktopAuthPayload(
    `${signedDesktopRequestPayload(method, requestUrl, timestamp, requestNonce)}\nipc:${capability}`,
  );
  return fetch(requestUrl, {
    ...init,
    method,
    headers: {
      ...(init.headers as Record<string, string> | undefined),
      ...headers,
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
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
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

async function waitForBackendReady(timeoutMs = BACKEND_HEALTH_TIMEOUT_MS): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (!backendProcess || backendProcess.exitCode !== null) {
      return false;
    }
    try {
      const response = await fetch('http://127.0.0.1:5000/ready');
      if (response.ok) {
        backendRestartAttempts = 0;
        appendDesktopLog('INFO', 'Backend core readiness check passed.');
        return true;
      }
    } catch {
      // Backend is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  appendDesktopLog('WARN', 'Backend core readiness check timed out after 60 seconds.');
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
      const requestNonce = crypto.randomBytes(24).toString('base64url');
      setHeaderValue(requestHeaders, 'X-Desktop-Auth-Timestamp', timestamp);
      setHeaderValue(requestHeaders, 'X-Desktop-Auth-Request-Nonce', requestNonce);
      setHeaderValue(
        requestHeaders,
        'X-Desktop-Auth-Request-Signature',
        signDesktopAuthPayload(
          signedDesktopRequestPayload(details.method || 'GET', details.url, timestamp, requestNonce),
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
          "connect-src 'self' http://localhost:5000 http://127.0.0.1:5000 app:; " +
          "font-src 'self' data: app:;"
        ]
      }
    });
  });

  startBackend();
  const backendReady = await waitForBackendReady();
  if (!backendReady) {
    splashWindow?.close();
    dialog.showErrorBox(
      'DataLogicEngine could not start',
      'Core services did not become ready. Open the desktop runtime log for the safe failure reason.',
    );
    app.quit();
    return;
  }

  powerMonitor.on('suspend', () => {
    void notifyBackendLifecycleEvent('suspend');
  });
  powerMonitor.on('resume', () => {
    void notifyBackendLifecycleEvent('resume');
  });
  let lastWallClock = Date.now();
  let lastUptime = process.uptime() * 1000;
  clockDriftTimer = setInterval(() => {
    const wallClock = Date.now();
    const uptime = process.uptime() * 1000;
    const drift = Math.abs((wallClock - lastWallClock) - (uptime - lastUptime));
    lastWallClock = wallClock;
    lastUptime = uptime;
    if (drift > 5000) {
      void notifyBackendLifecycleEvent('time_changed');
    }
  }, 30000);
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

  let pythonPath = 'python'; // Default to system python
  let scriptPath = path.join(rootDir, 'main.py');
  
  if (!isDev) {
    // In production, backend is bundled as an executable
    const exeName = os.platform() === 'win32' ? 'DataLogic_Backend.exe' : 'DataLogic_Backend';
    pythonPath = path.join(process.resourcesPath, 'backend', exeName);
    scriptPath = ''; // Not used when running exe directly
  }

  const args = scriptPath ? [scriptPath] : [];
  const sessionSecret = loadOrCreateProtectedSecret('SESSION_SECRET');
  const encryptionKekSecret = loadOrCreateProtectedSecret('ENCRYPTION_KEK_SECRET');
  const dotenvKeys: Record<string, string> = isDev
    ? {}
    : migrateAndLoadPackagedDotenvSecrets(runtimeDir);
  const dotenvCandidates = isDev ? [path.join(rootDir, '.env')] : [];
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

  const env: NodeJS.ProcessEnv = {
    ...dotenvKeys,       // .env values first (lowest priority)
    ...process.env,      // Electron inherited env overrides .env
    PORT: '5000', 
    FLASK_ENV: isDev ? 'development' : 'production',
    IS_DESKTOP_APP: 'true',
    SESSION_COOKIE_SECURE: 'false',
    SESSION_COOKIE_SAMESITE: 'Lax',
    CORS_ORIGINS: 'http://localhost:3000,http://127.0.0.1:3000,app://dashboard,app://-',
    DESKTOP_INSTALL_SECRET: desktopInstallSecret,
    DLE_DESKTOP_SECRET_HANDOFF: 'true',
    SESSION_SECRET: sessionSecret,
    ENCRYPTION_KEK_SECRET: encryptionKekSecret,
    DLE_RUNTIME_ROOT: runtimeDir,
    LOG_FILE: path.join(runtimeDir, 'logs', 'app.log'),
    DATALOGIC_STORAGE_SETTINGS_PATH: path.join(runtimeDir, 'settings.json'),
    AUTO_CREATE_SCHEMA: 'False',
    LLAMA_INDEX_CACHE_DIR: path.join(runtimeDir, 'cache', 'llama_index'),
    HF_HOME: path.join(runtimeDir, 'cache', 'huggingface'),
    TRANSFORMERS_CACHE: path.join(runtimeDir, 'cache', 'huggingface'),
    NLTK_DATA: path.join(runtimeDir, 'cache', 'nltk_data'),
  };
  if (isDev) {
    env.DATABASE_URL = `sqlite:///${path.join(runtimeDir, 'ukg_database.db').replace(/\\/g, '/')}`;
  }

  appendDesktopLog('INFO', `Backend working directory: ${runtimeDir}`);
  
  // Ensure cache directories exist
  secureDirectoryBestEffort(path.join(runtimeDir, 'cache'));
  secureDirectoryBestEffort(path.join(runtimeDir, 'cache', 'llama_index'));
  secureDirectoryBestEffort(path.join(runtimeDir, 'cache', 'huggingface'));
  secureDirectoryBestEffort(path.join(runtimeDir, 'cache', 'nltk_data'));

  backendProcess = spawn(pythonPath, args, { env, cwd: runtimeDir });

  backendProcess.stdout?.on('data', (data) => {
    const log = safeDesktopLogMessage(data.toString());
    console.log(`[Backend] ${log}`);
    mainWindow?.webContents.send('backend-log', log);
    appendDesktopLog('INFO', `[Backend] ${log}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    const log = safeDesktopLogMessage(data.toString());
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

app.on('before-quit', (event) => {
  if (gracefulQuitStarted || !backendProcess || backendProcess.exitCode !== null) {
    return;
  }
  event.preventDefault();
  gracefulQuitStarted = true;
  void runBoundedShutdown(
    () => notifyBackendLifecycleEvent('shutdown'),
    () => {
      intentionalBackendShutdown = true;
      backendProcess?.kill();
    },
  ).finally(() => app.quit());
});

app.on('quit', () => {
  if (updateCheckTimer) {
    clearInterval(updateCheckTimer);
    updateCheckTimer = null;
  }
  if (clockDriftTimer) {
    clearInterval(clockDriftTimer);
    clockDriftTimer = null;
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
    return { status: 'offline', phase: 'stopped', services: {}, chroma_collections: {}, redis_ping_ms: null, object_store_buckets: {}, memory_vertices: 0, memory_edges: 0, last_recall_timestamp: null };
  }

  try {
    const response = await desktopFetch('http://127.0.0.1:5000/api/v1/system/diagnostics/health');
    const payload = await responseJson<{
      runtime?: {
        phase?: string;
        ready?: boolean;
        services?: Record<string, { state?: string; safe_reason?: string | null }>;
      };
      database?: {
        status?: string;
        chromadb?: { collections?: Record<string, number> };
        redis?: { ping_ms?: number | null };
        object_store?: { buckets?: ObjectStoreBucketStats };
        memory?: StructuredMemoryStats;
      };
    }>(response);
    return {
      status: payload?.runtime?.ready && payload?.database?.status === 'ok' ? 'managed' : 'degraded',
      phase: payload?.runtime?.phase ?? 'unknown',
      services: payload?.runtime?.services ?? {},
      chroma_collections: payload?.database?.chromadb?.collections ?? {},
      redis_ping_ms: payload?.database?.redis?.ping_ms ?? null,
      object_store_buckets: payload?.database?.object_store?.buckets ?? {},
      memory_vertices: payload?.database?.memory?.memory_vertices ?? 0,
      memory_edges: payload?.database?.memory?.memory_edges ?? 0,
      last_recall_timestamp: payload?.database?.memory?.last_recall_timestamp ?? null,
    };
  } catch {
    return { status: 'unavailable', phase: 'unknown', services: {}, chroma_collections: {}, redis_ping_ms: null, object_store_buckets: {}, memory_vertices: 0, memory_edges: 0, last_recall_timestamp: null };
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
  const selectedPath = result.filePaths[0];
  return result.canceled || !selectedPath
    ? null
    : issuePathCapability(selectedPath, 'backup');
});

ipcMain.handle('choose-ingestion-source', async (event, ...args: unknown[]) => {
  assertTrustedIpcInvoke(event, 'choose-ingestion-source', args);
  const options: OpenDialogOptions = {
    properties: ['openFile', 'openDirectory'],
    title: 'Choose a knowledge file or folder',
  };
  const result = mainWindow
    ? await dialog.showOpenDialog(mainWindow, options)
    : await dialog.showOpenDialog(options);
  const selectedPath = result.filePaths[0];
  return result.canceled || !selectedPath
    ? null
    : issuePathCapability(selectedPath, 'ingestion');
});

ipcMain.handle('run-database-backup', async (event, payload?: unknown, ...args: unknown[]) => {
  assertTrustedIpcSender(event, 'run-database-backup');
  if (args.length > 0) {
    throw new Error('Blocked unexpected IPC payload for channel "run-database-backup"');
  }
  const parsedPayload = payload === undefined ? {} : requireJsonRecord(payload, 'run-database-backup');
  rejectUnknownKeys(parsedPayload, ['target_capability', 'operation_id'], 'run-database-backup');
  const operationId = requiredOperationId(parsedPayload, 'run-database-backup');
  const targetCapability = optionalBoundedString(
    parsedPayload,
    'target_capability',
    'run-database-backup',
    128,
  );
  const targetDir = targetCapability
    ? consumePathCapability(targetCapability, 'backup')
    : undefined;

  const response = await withCancellableDesktopOperation(operationId, (signal) =>
    desktopIpcFetch('http://127.0.0.1:5000/api/v1/storage/backup', 'backup', {
      method: 'POST',
      body: JSON.stringify({ target_dir: targetDir }),
      signal,
    }),
  );
  const result = await responseJson<unknown>(response);
  if (!response.ok) {
    throw new Error(`Backup failed with status ${response.status}`);
  }
  const data = responseDataRecord(result, 'run-database-backup');
  if (
    typeof data.artifact_path !== 'string' ||
    typeof data.size_bytes !== 'number' ||
    !data.manifest ||
    typeof data.manifest !== 'object' ||
    Array.isArray(data.manifest)
  ) {
    throw new Error('Backup returned an invalid response contract');
  }
  return data;
});

ipcMain.handle('run-local-ingestion', async (event, payload?: unknown, ...args: unknown[]) => {
  assertTrustedIpcSender(event, 'run-local-ingestion');
  if (args.length > 0) {
    throw new Error('Blocked unexpected IPC payload for channel "run-local-ingestion"');
  }
  const parsedPayload = requireJsonRecord(payload, 'run-local-ingestion');
  rejectUnknownKeys(
    parsedPayload,
    [
      'source_capability',
      'recursive',
      'chunk_size',
      'max_file_bytes',
      'source_label',
      'async_mode',
      'sync_neo4j',
      'operation_id',
    ],
    'run-local-ingestion',
  );
  const operationId = requiredOperationId(parsedPayload, 'run-local-ingestion');
  const sourceCapability = optionalBoundedString(
    parsedPayload,
    'source_capability',
    'run-local-ingestion',
    128,
  );
  if (!sourceCapability) {
    throw new Error('A selected ingestion source capability is required');
  }
  const sourcePath = consumePathCapability(sourceCapability, 'ingestion');
  const asyncMode = optionalBoolean(parsedPayload, 'async_mode', 'run-local-ingestion', false);
  const requestPayload = {
    path: sourcePath,
    recursive: optionalBoolean(parsedPayload, 'recursive', 'run-local-ingestion', true),
    chunk_size: optionalBoundedInteger(parsedPayload, 'chunk_size', 'run-local-ingestion', 1200, 100, 100_000),
    max_file_bytes: optionalBoundedInteger(
      parsedPayload,
      'max_file_bytes',
      'run-local-ingestion',
      10 * 1024 * 1024,
      1,
      500 * 1024 * 1024,
    ),
    source_label: optionalBoundedString(parsedPayload, 'source_label', 'run-local-ingestion', 200),
    ...(asyncMode
      ? { sync_neo4j: optionalBoolean(parsedPayload, 'sync_neo4j', 'run-local-ingestion', false) }
      : {}),
  };
  const endpoint = asyncMode
    ? 'http://127.0.0.1:5000/api/v1/ingestion/local/async'
    : 'http://127.0.0.1:5000/api/v1/ingestion/local';
  const response = await withCancellableDesktopOperation(operationId, (signal) =>
    desktopIpcFetch(endpoint, 'ingestion', {
      method: 'POST',
      body: JSON.stringify(requestPayload),
      signal,
    }),
  );
  const result = await responseJson<unknown>(response);
  if (!response.ok) {
    throw new Error(`Local ingestion failed with status ${response.status}`);
  }
  const data = responseDataRecord(result, 'run-local-ingestion');
  if (typeof data.ingestion_id !== 'string') {
    throw new Error('Local ingestion returned an invalid response contract');
  }
  if (asyncMode) {
    if (typeof data.status !== 'string') {
      throw new Error('Async ingestion returned an invalid response contract');
    }
  } else {
    for (const key of ['files_ingested', 'files_rejected', 'chunks_created', 'chunks_indexed']) {
      if (typeof data[key] !== 'number') {
        throw new Error('Local ingestion returned an invalid response contract');
      }
    }
  }
  return data;
});

ipcMain.handle('cancel-desktop-operation', (event, payload?: unknown, ...args: unknown[]) => {
  assertTrustedIpcSender(event, 'cancel-desktop-operation');
  if (args.length > 0) {
    throw new Error('Blocked unexpected IPC payload for channel "cancel-desktop-operation"');
  }
  const parsedPayload = requireJsonRecord(payload, 'cancel-desktop-operation');
  rejectUnknownKeys(parsedPayload, ['operation_id'], 'cancel-desktop-operation');
  const operationId = requiredOperationId(parsedPayload, 'cancel-desktop-operation');
  const controller = activeDesktopOperations.get(operationId);
  if (!controller) {
    return { cancelled: false };
  }
  controller.abort();
  return { cancelled: true };
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
