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

  it('login should post credentials with email', async () => {
    const creds = { email: 'test@example.com', password: 'password123' };
    const response = { user: { id: 1, email: 'test@example.com' }, token: 'abc123' };
    (request as Mock).mockResolvedValue(response);
    const result = await auth.login(creds);
    expect(request).toHaveBeenCalledWith('/auth/login', {
      method: 'POST',
      body: JSON.stringify(creds),
    });
    expect(result).toEqual(response);
  });

  it('login should post credentials with username', async () => {
    const creds = { username: 'testuser', password: 'password123' };
    const response = { user: { id: 1, username: 'testuser' } };
    (request as Mock).mockResolvedValue(response);
    await auth.login(creds);
    expect(request).toHaveBeenCalledWith('/auth/login', {
      method: 'POST',
      body: JSON.stringify(creds),
    });
  });

  it('login should handle MFA required response', async () => {
    const creds = { email: 'test@example.com', password: 'password123' };
    const response = { mfa_required: true, session_id: 'sess_123' };
    (request as Mock).mockResolvedValue(response);
    const result = await auth.login(creds);
    expect(result).toEqual(response);
    expect(result.mfa_required).toBe(true);
  });

  it('login should return user and token on success', async () => {
    const creds = { email: 'test@example.com', password: 'password123' };
    const response = {
      user: {
        id: '123',
        email: 'test@example.com',
        username: 'testuser',
      },
      token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    };
    (request as Mock).mockResolvedValue(response);
    const result = await auth.login(creds);
    expect(result.user).toBeDefined();
    expect(result.token).toBeDefined();
    expect(result.user?.id).toBe('123');
  });

  it('logout should call logout endpoint', async () => {
    (request as Mock).mockResolvedValue({});
    await auth.logout();
    expect(request).toHaveBeenCalledWith('/auth/logout', { method: 'POST' });
  });

  it('logout should handle network errors gracefully', async () => {
    (request as Mock).mockRejectedValue(new Error('Network error'));
    await expect(auth.logout()).resolves.not.toThrow();
  });

  it('logout should clear user session on success', async () => {
    (request as Mock).mockResolvedValue(undefined);
    const result = await auth.logout();
    expect(result).toBeUndefined();
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

  describe('credential handling', () => {
    it('should accept email as credential identifier', async () => {
      const creds = {
        email: 'user@example.com',
        password: 'secure_password',
      };
      (request as Mock).mockResolvedValue({ user: { id: '1' } });
      await auth.login(creds);
      expect(request).toHaveBeenCalledWith(
        '/auth/login',
        expect.objectContaining({
          body: expect.stringContaining('user@example.com'),
        })
      );
    });

    it('should accept username as credential identifier', async () => {
      const creds = {
        username: 'john_doe',
        password: 'secure_password',
      };
      (request as Mock).mockResolvedValue({ user: { id: '1' } });
      await auth.login(creds);
      expect(request).toHaveBeenCalledWith(
        '/auth/login',
        expect.objectContaining({
          body: expect.stringContaining('john_doe'),
        })
      );
    });

    it('should always include password in credentials', async () => {
      const creds = { email: 'test@example.com', password: 'pass' };
      (request as Mock).mockResolvedValue({ user: { id: '1' } });
      await auth.login(creds);
      const callArgs = (request as Mock).mock.calls[0];
      const body = JSON.parse(callArgs[1].body);
      expect(body.password).toBe('pass');
    });
  });
});
