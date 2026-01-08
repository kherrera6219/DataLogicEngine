import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Paths that do not require authentication
const publicPaths = ['/login', '/register', '/', '/about'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check if path is public
  if (publicPaths.some(path => pathname === path || pathname.startsWith('/_next') || pathname.startsWith('/api') || pathname.startsWith('/static'))) {
    return NextResponse.next();
  }

  // TODO: Real token verification logic
  // For now, we simulate a check. In a real app, verify JWT or Session Cookie.
  // const token = request.cookies.get('session_token');
  // if (!token) {
  //   const url = request.nextUrl.clone();
  //   url.pathname = '/login';
  //   url.searchParams.set('callbackUrl', encodeURI(pathname));
  //   return NextResponse.redirect(url);
  // }

  // Add security headers
  const response = NextResponse.next();
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  
  return response;
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
