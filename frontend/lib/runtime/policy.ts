export type RuntimeMode = 'local' | 'cloud' | 'hybrid';

const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '::1']);

function normalizeRuntimeMode(rawValue?: string | null): RuntimeMode {
  const normalized = (rawValue || '').trim().toLowerCase();
  if (normalized === 'local' || normalized === 'desktop') {
    return 'local';
  }
  if (normalized === 'hybrid') {
    return 'hybrid';
  }
  if (normalized === 'cloud') {
    return 'cloud';
  }

  return process.env.NODE_ENV === 'development' ? 'local' : 'cloud';
}

export function getRuntimeMode(): RuntimeMode {
  return normalizeRuntimeMode(process.env.NEXT_PUBLIC_APP_RUNTIME_MODE);
}

export function runtimeAllowsDesktopAuth(mode: RuntimeMode = getRuntimeMode()): boolean {
  return mode !== 'cloud';
}

export function isLoopbackHost(rawHost: string | null | undefined): boolean {
  const host = (rawHost || '').trim().toLowerCase();
  if (!host) {
    return false;
  }

  if (host.startsWith('[')) {
    const closingBracket = host.indexOf(']');
    const ipv6Host = closingBracket > 0 ? host.slice(1, closingBracket) : host.slice(1);
    return LOOPBACK_HOSTS.has(ipv6Host);
  }

  return LOOPBACK_HOSTS.has(host.split(':')[0]);
}

export function isDesktopRendererRuntime(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  const runtimeWindow = window as typeof window & { electronAPI?: unknown };
  return Boolean(runtimeWindow.electronAPI || window.navigator.userAgent.includes('Electron'));
}

export function shouldUseDesktopSessionFlow(): boolean {
  return runtimeAllowsDesktopAuth() && isDesktopRendererRuntime();
}

interface DesktopRequestAuthorizationInput {
  host: string | null | undefined;
  desktopHeader: string | null | undefined;
  userAgent: string | null | undefined;
  mode?: RuntimeMode;
  forceBypass?: boolean;
}

export function isDesktopRequestAuthorized({
  host,
  desktopHeader,
  userAgent,
  mode = getRuntimeMode(),
  forceBypass = false,
}: DesktopRequestAuthorizationInput): boolean {
  if (!runtimeAllowsDesktopAuth(mode)) {
    return false;
  }

  if (forceBypass) {
    return true;
  }

  if (!isLoopbackHost(host)) {
    return false;
  }

  const normalizedHeader = (desktopHeader || '').trim().toLowerCase();
  if (normalizedHeader === 'true' || normalizedHeader === '1') {
    return true;
  }

  return (userAgent || '').includes('Electron');
}
