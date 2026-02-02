import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const requestId = crypto.randomUUID();

  try {
    // 1. Session Validation
    // Check for both standard session cookie and fallback
    const sessionToken = request.cookies.get('session')?.value || request.cookies.get('session_id')?.value;
    
    // Allow public paths that might have slipped through matcher (just in case), though matcher should handle most
    const isLoginPage = pathname === '/login' || pathname === '/register';

    if (!sessionToken && !isLoginPage) {
      console.warn(`[Middleware] [${requestId}] Unauthorized access attempt to ${pathname}`);
      const url = request.nextUrl.clone();
      url.pathname = '/login';
      url.searchParams.set('callbackUrl', encodeURI(pathname));
      return NextResponse.redirect(url);
    }

    // 2. Security Header Injection
    const response = NextResponse.next();
    
    // Strict Content Security Policy
    const cspHeader = `
      default-src 'self';
      script-src 'self' 'unsafe-inline' 'unsafe-eval';
      style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
      img-src 'self' blob: data: https://images.unsplash.com;
      font-src 'self' https://fonts.gstatic.com;
      connect-src 'self' ws: wss:;
      frame-src 'none';
      object-src 'none';
      base-uri 'self';
      form-action 'self';
      frame-ancestors 'none';
      upgrade-insecure-requests;
    `.replace(/\s{2,}/g, ' ').trim();

    response.headers.set('Content-Security-Policy', cspHeader);
    response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload');
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    response.headers.set('X-XSS-Protection', '1; mode=block');
    response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), interest-cohort=()');
    response.headers.set('X-Request-ID', requestId);

    return response;

  } catch (error) {
    console.error(`[Middleware Error] [${requestId}]`, error);
    // On catastrophic middleware failure, fail open to landing page or error page
    return NextResponse.redirect(new URL('/', request.url));
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - login (public auth page)
     * - register (public auth page)
     * - / (landing page)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|login|register|$).*)',
  ],
};
