import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Paths that do not require authentication
const publicPaths = ['/login', '/register', '/', '/about'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const requestId = crypto.randomUUID();

  try {
    // 1. Path Whitelisting
    const isPublicPath = publicPaths.some(path => 
      pathname === path || 
      pathname.startsWith('/_next') || 
      pathname.startsWith('/api') || 
      pathname.startsWith('/static') ||
      pathname === '/favicon.ico'
    );

    if (isPublicPath) {
      return NextResponse.next();
    }

    // 2. Session Validation
    const sessionToken = request.cookies.get('session')?.value || request.cookies.get('session_id')?.value;
    
    if (!sessionToken) {
      console.warn(`[Middleware] [${requestId}] Unauthorized access attempt to ${pathname}`);
      const url = request.nextUrl.clone();
      url.pathname = '/login';
      url.searchParams.set('callbackUrl', encodeURI(pathname));
      return NextResponse.redirect(url);
    }

    // 3. Security Header Injection
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
    // On catastrophic middleware failure, redirect to a safe error page or landing
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
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};
