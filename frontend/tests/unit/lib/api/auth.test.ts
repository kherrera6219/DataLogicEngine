import { describe, it, expect, vi, beforeEach, Mock } from 'vitest';
import { auth } from '@/lib/api/auth';
import { request } from '@/lib/api/index';

// Mock the request function
vi.mock('@/lib/api/index', () => ({
  request: vi.fn(),
}));

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('check should call request with correect endpoint', async () => {
    (request as Mock).mockResolvedValue({ authenticated: true });
    const res = await auth.check();
    expect(request).toHaveBeenCalledWith('/auth/check');
    expect(res).toEqual({ authenticated: true });
  });

  it('login should post credentials', async () => {
    const creds = { email: 'test@example.com', password: 'password' };
    (request as Mock).mockResolvedValue({ user: { id: 1 } });
    await auth.login(creds);
    expect(request).toHaveBeenCalledWith('/auth/login', {
      method: 'POST',
      body: JSON.stringify(creds),
    });
  });

  it('logout should call logout endpoint', async () => {
    (request as Mock).mockResolvedValue({});
    await auth.logout();
    expect(request).toHaveBeenCalledWith('/auth/logout', { method: 'POST' });
  });
});
