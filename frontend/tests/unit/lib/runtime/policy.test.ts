import { afterEach, describe, expect, it } from 'vitest';
import {
  getRuntimeMode,
  isDesktopRequestAuthorized,
  isLoopbackHost,
  runtimeAllowsDesktopAuth,
} from '@/lib/runtime/policy';

describe('runtime policy', () => {
  const originalRuntimeMode = process.env.NEXT_PUBLIC_APP_RUNTIME_MODE;

  afterEach(() => {
    process.env.NEXT_PUBLIC_APP_RUNTIME_MODE = originalRuntimeMode;
  });

  it('uses explicit runtime mode from environment', () => {
    process.env.NEXT_PUBLIC_APP_RUNTIME_MODE = 'hybrid';
    expect(getRuntimeMode()).toBe('hybrid');
  });

  it('normalizes desktop alias to local runtime mode', () => {
    process.env.NEXT_PUBLIC_APP_RUNTIME_MODE = 'desktop';
    expect(getRuntimeMode()).toBe('local');
  });

  it('enforces desktop auth gating by runtime mode', () => {
    expect(runtimeAllowsDesktopAuth('local')).toBe(true);
    expect(runtimeAllowsDesktopAuth('hybrid')).toBe(true);
    expect(runtimeAllowsDesktopAuth('cloud')).toBe(false);
  });

  it('detects loopback hosts including bracketed IPv6', () => {
    expect(isLoopbackHost('localhost:3000')).toBe(true);
    expect(isLoopbackHost('127.0.0.1:3000')).toBe(true);
    expect(isLoopbackHost('[::1]:3000')).toBe(true);
    expect(isLoopbackHost('example.com')).toBe(false);
  });

  it('authorizes desktop requests only when loopback and trusted signal is present', () => {
    expect(
      isDesktopRequestAuthorized({
        host: 'localhost:3000',
        desktopHeader: 'true',
        userAgent: '',
        mode: 'local',
      }),
    ).toBe(true);

    expect(
      isDesktopRequestAuthorized({
        host: 'localhost:3000',
        desktopHeader: '',
        userAgent: 'Mozilla/5.0 Electron/26.0.0',
        mode: 'local',
      }),
    ).toBe(true);

    expect(
      isDesktopRequestAuthorized({
        host: 'example.com',
        desktopHeader: 'true',
        userAgent: 'Electron',
        mode: 'local',
      }),
    ).toBe(false);

    expect(
      isDesktopRequestAuthorized({
        host: 'localhost:3000',
        desktopHeader: 'true',
        userAgent: 'Electron',
        mode: 'cloud',
      }),
    ).toBe(false);
  });
});
