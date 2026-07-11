
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { request, api } from '@/lib/api/index';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock window location
const mockLocation = { href: '' };
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true
});

describe('api module', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockFetch.mockResolvedValue({
            ok: true,
            json: async () => ({ data: 'success' }),
            status: 200
        });
    });

  describe('request helper', () => {
    it('makes a request with default headers', async () => {
        const res = await request('/test');
        expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/test'), expect.any(Object));
        const [, options] = mockFetch.mock.calls[0];
        expect((options.headers as Headers).get('Content-Type')).toBe('application/json');
        expect(res).toBe('success');
    });

    it('handles absolute URLs', async () => {
        await request('http://external.api/test');
        expect(mockFetch).toHaveBeenCalledWith('http://external.api/test', expect.any(Object));
    });

    it('handles 401/403 errors and redirects', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 401
        });
        
        await expect(request('/protected')).rejects.toThrow(/Session expired/);
        expect(mockLocation.href).toContain('/login');
    });

    it('handles generic API errors', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: false,
            status: 500,
            json: async () => ({ message: 'Server exploded' })
        });

        await expect(request('/fail')).rejects.toThrow('Server exploded');
    });

    it('handles network errors', async () => {
        const error = new Error('Network Error');
        mockFetch.mockRejectedValueOnce(error);
        await expect(request('/fail')).rejects.toThrow('Network Error');
    });
  });

  describe('api analytics object', () => {
      it('summary makes correct request', async () => {
          await api.analytics.summary();
          expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/analytics/overview'), expect.any(Object));
      });

      it('trends makes correct request with defaults', async () => {
          await api.analytics.trends('visitors');
          expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('metric=visitors&days=7'), expect.any(Object));
      });

      it('overview makes correct request', async () => {
          await api.analytics.overview();
          expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/analytics/overview'), expect.any(Object));
      });

      it('activity makes correct request', async () => {
          await api.analytics.activity();
          expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/analytics/activity'), expect.any(Object));
      });

      it('mcp makes correct request', async () => {
          await api.analytics.mcp();
           expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/analytics/mcp'), expect.any(Object));
      });
  });
  
  describe('api system object', () => {
      it('health returns operational', async () => {
          mockFetch.mockResolvedValueOnce({
              ok: true,
              json: async () => ({ status: 'ok' }),
              status: 200
          });
          const status = await api.system.health();
          expect(status).toBe('ok');
      });
  });
  
  describe('api get helper', () => {
      it('makes a GET request', async () => {
          await api.get('/test');
          expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/test'), expect.objectContaining({ method: 'GET' }));
      });
  });
});
