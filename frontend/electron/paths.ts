/**
 * Desktop filesystem path helpers (Phase 5 extraction from main.ts).
 */
import { app } from 'electron';
import * as path from 'path';

export function desktopSecretFilePath(): string {
  return path.join(app.getPath('userData'), 'desktop-install-secret');
}

export function desktopLogFilePath(): string {
  return path.join(app.getPath('userData'), 'logs', 'desktop-runtime.log');
}

export function desktopRuntimeDir(): string {
  return path.join(app.getPath('userData'), 'runtime');
}

export function desktopSecretVaultDir(): string {
  return path.join(app.getPath('userData'), 'secrets');
}
