import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getRuntimeMode, isDesktopRequestAuthorized } from '@/lib/runtime/policy';

function isDesktopRequest(request: NextRequest): boolean {
  const forceBypass =
    process.env.NODE_ENV !== 'production' &&
    process.env.NEXT_PUBLIC_DESKTOP_AUTH_BYPASS === 'true';

  return isDesktopRequestAuthorized({
    host: request.headers.get('host') || request.nextUrl.host,
    desktopHeader: request.headers.get('x-datalogic-desktop'),
    userAgent: request.headers.get('user-agent') || '',
    mode: getRuntimeMode(),
    forceBypass,
  });
}

function buildCsp(nonce: string): string {
  const isDevelopment = process.env.NODE_ENV !== 'production';

  const scriptSrc = [`'self'`, `'nonce-${nonce}'`];
  if (isDevelopment) {
    scriptSrc.push("'unsafe-inline'");
    scriptSrc.push("'unsafe-eval'");
  }

  const styleSrc = [`'self'`, 'https://fonts.googleapis.com'];
  if (isDevelopment) {
    styleSrc.push("'unsafe-inline'");
  } else {
    styleSrc.push(`'nonce-${nonce}'`);
  }

  const connectSrc = [`'self'`, 'https:', 'ws:', 'wss:'];
  if (isDevelopment) {
    connectSrc.push('http://localhost:*', 'http://127.0.0.1:*');
  }

  const cspHeader = `
      default-src 'self';
      script-src ${scriptSrc.join(' ')};
      style-src ${styleSrc.join(' ')};
      img-src 'self' blob: data: https://images.unsplash.com;
      font-src 'self' https://fonts.gstatic.com;
      connect-src ${connectSrc.join(' ')};
      frame-src 'none';
      object-src 'none';
      base-uri 'self';
      form-action 'self';
      frame-ancestors 'none';
      upgrade-insecure-requests;
    `
    .replace(/\s{2,}/g, ' ')
    .trim();

  return cspHeader;
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const requestId = crypto.randomUUID();
  const publicPrefixes = ['/', '/login', '/register', '/about', '/legal/privacy'];
  const isPublicPath = publicPrefixes.some((prefix) => {
    if (prefix === '/') {
      return pathname === '/';
    }
    return pathname === prefix || pathname.startsWith(`${prefix}/`);
  });

  try {
    // 1. Session Validation
    // Check for both standard session cookie and fallback
    const sessionToken = request.cookies.get('session')?.value || request.cookies.get('session_id')?.value;
    const desktopRequest = isDesktopRequest(request);
    
    if (!sessionToken && !isPublicPath && !desktopRequest) {
      console.warn(`[Proxy] [${requestId}] Unauthorized access attempt to ${pathname}`);
      const url = request.nextUrl.clone();
      url.pathname = '/login';
      url.searchParams.set('callbackUrl', encodeURI(pathname));
      return NextResponse.redirect(url);
    }

    // 2. Security Header Injection
    const response = NextResponse.next();

    const nonce = crypto.randomUUID().replace(/-/g, '');
    const cspHeader = buildCsp(nonce);

    response.headers.set('Content-Security-Policy', cspHeader);
    response.headers.set('x-nonce', nonce);
    response.headers.set('Strict-Transport-Security', 'max-age=63072000; includeSubDomains; preload');
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    response.headers.set('X-XSS-Protection', '1; mode=block');
    response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), interest-cohort=()');
    response.headers.set('X-Request-ID', requestId);

    return response;

  } catch (error) {
    console.error(`[Proxy Error] [${requestId}]`, error);
    // Fail closed for protected routes when middleware cannot validate request state.
    return NextResponse.json(
      {
        error: 'Request validation failed',
        request_id: requestId,
      },
      { status: 503 },
    );
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
