import { describe, it, expect, vi, beforeEach } from 'vitest';
import { auth } from './auth';
import { request } from './index';

// Mock the request function
vi.mock('./index', () => ({
  request: vi.fn(),
}));

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('check should call request with correect endpoint', async () => {
    (request as any).mockResolvedValue({ authenticated: true });
    const res = await auth.check();
    expect(request).toHaveBeenCalledWith('/auth/check');
    expect(res).toEqual({ authenticated: true });
  });

  it('login should post credentials', async () => {
    const creds = { email: 'test@example.com', password: 'password' };
    (request as any).mockResolvedValue({ user: { id: 1 } });
    await auth.login(creds);
    expect(request).toHaveBeenCalledWith('/auth/login', {
      method: 'POST',
      body: JSON.stringify(creds),
    });
  });

  it('logout should call logout endpoint', async () => {
    (request as any).mockResolvedValue({});
    await auth.logout();
    expect(request).toHaveBeenCalledWith('/auth/logout', { method: 'POST' });
  });
});
