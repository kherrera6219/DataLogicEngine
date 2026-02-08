import { describe, it, expect, vi, beforeEach } from 'vitest';
import { proxy } from '../../proxy';
import { NextRequest, NextResponse } from 'next/server';

// Mock NextResponse
vi.mock('next/server', () => {
    const nextFn = vi.fn((init) => ({
      cookies: { set: vi.fn() },
      headers: new Headers(init?.headers),
      status: 200, 
    }));
    
    const redirectFn = vi.fn((url) => ({
        headers: new Headers({ Location: url.toString() }),
        status: 307
    }));

    return {
        NextResponse: {
            next: nextFn,
            redirect: redirectFn,
        },
        NextRequest: vi.fn()
    };
});

describe('Proxy', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    const createRequest = (pathname: string, cookies: Record<string, string> = {}) => {
        const url = new URL(`http://localhost${pathname}`);
        // Add clone to the URL object to mimic NextURL
        (url as any).clone = () => new URL(url.toString());
        
        return {
            nextUrl: url,
            url: url.toString(),
            cookies: {
                get: (name: string) => cookies[name] ? { value: cookies[name] } : undefined
            },
            headers: new Headers(),
        } as unknown as NextRequest;
    };

    it('should redirect to login if session is missing on protected route', () => {
        const req = createRequest('/dashboard');
        proxy(req);
        expect(NextResponse.redirect).toHaveBeenCalled();
        const redirectUrl = vi.mocked(NextResponse.redirect).mock.calls[0][0] as URL;
        expect(redirectUrl.pathname).toBe('/login');
    });

    it('should allow access if session cookie is present', () => {
        const req = createRequest('/dashboard', { session: 'valid-token' });
        proxy(req);
        // Should call next()
        expect(NextResponse.next).toHaveBeenCalled();
    });
    
    it('should allow access if session_id cookie is present', () => {
        const req = createRequest('/dashboard', { session_id: 'valid-token' });
        proxy(req);
        expect(NextResponse.next).toHaveBeenCalled();
    });

    it('should set security headers on successful response', () => {
         const req = createRequest('/dashboard', { session: 'valid-token' });
         // We need to capture the response object returned by next()
         // In our mock, next returns an object with headers.
         // However, the real middleware modifies that object. 
         // Let's Spy on the response object returned by our mock next()
         
         const mockResHeaderSet = vi.fn();
         const mockResponse = {
             headers: {
                 set: mockResHeaderSet
             }
         };
         
         vi.mocked(NextResponse.next).mockReturnValue(mockResponse as any);

         proxy(req);

         expect(mockResHeaderSet).toHaveBeenCalledWith('X-Frame-Options', 'DENY');
         expect(mockResHeaderSet).toHaveBeenCalledWith('X-Content-Type-Options', 'nosniff');
         expect(mockResHeaderSet).toHaveBeenCalledWith('Content-Security-Policy', expect.stringContaining("default-src 'self'"));
    });

    it('should fail open (redirect to /) on internal error', () => {
        // Force an error
        const req = createRequest('/dashboard');

        req.cookies.get = () => { throw new Error('Simulation Error'); };
        
        proxy(req);
        expect(NextResponse.redirect).toHaveBeenCalled();
        const redirectCall = vi.mocked(NextResponse.redirect).mock.calls[0];
        // It might be the first or second call depending on logic flow, 
        // but here it crashes immediately, so first call is the error handler redirect
        const redirectUrl = redirectCall[0] as URL;
        expect(redirectUrl.pathname).toBe('/'); 
    });
});
