import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { auth } from '@/lib/api/auth';
import { request } from '@/lib/api/client';

// Mock the request function
vi.mock('@/lib/api/client', () => ({
  request: vi.fn(),
}));

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('check should call request with correct endpoint', async () => {
    (request as Mock).mockResolvedValue({ authenticated: true });
    const res = await auth.check();
    expect(request).toHaveBeenCalledWith('/auth/check');
    expect(res).toEqual({ authenticated: true });
  });

  it('check should handle failure by returning unauthenticated', async () => {
    (request as Mock).mockRejectedValue(new Error('Network error'));
    const res = await auth.check();
    expect(res).toEqual({ authenticated: false });
  });

  it('desktopAutoLogin should post to correct endpoint', async () => {
    const response = { user: { id: '123' }, token: 'token_123' };
    (request as Mock).mockResolvedValue(response);
    const result = await auth.desktopAutoLogin();
    expect(request).toHaveBeenCalledWith('/auth/desktop/auto-login', {
      method: 'POST',
    });
    expect(result).toEqual(response);
  });

  it('desktopAutoLogin should return login response on success', async () => {
    const response = {
      user: { id: '123', email: 'desktop@example.com' },
      token: 'desktop_token',
    };
    (request as Mock).mockResolvedValue(response);
    const result = await auth.desktopAutoLogin();
    expect(result.user?.id).toBe('123');
    expect(result.token).toBe('desktop_token');
  });

  describe('session validation', () => {
    it('should return authenticated user on successful check', async () => {
      const user = { id: '123', email: 'user@example.com', username: 'testuser' };
      (request as Mock).mockResolvedValue({ authenticated: true, user });
      const res = await auth.check();
      expect(res.authenticated).toBe(true);
      expect(res.user).toEqual(user);
    });

    it('should handle session expiration', async () => {
      (request as Mock).mockRejectedValue(new Error('Session expired'));
      const res = await auth.check();
      expect(res.authenticated).toBe(false);
    });
  });

  // Single-mode: the multi-user web `login`/`logout` methods (and their
  // `/auth/login` + `/auth/logout` endpoints) were removed. Auth is OS-level;
  // only `check` and the desktop auto-login handshake remain (covered above).
  it('does not expose web login/logout methods', () => {
    expect((auth as Record<string, unknown>).login).toBeUndefined();
    expect((auth as Record<string, unknown>).logout).toBeUndefined();
  });
});
