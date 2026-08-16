/** Shared env flag parser for Electron main process. */

export function envFlag(name: string, defaultValue: boolean): boolean {
  const raw = (process.env[name] || '').trim().toLowerCase();
  if (!raw) {
    return defaultValue;
  }
  return raw === '1' || raw === 'true' || raw === 'yes' || raw === 'on';
}
