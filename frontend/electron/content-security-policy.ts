/** Renderer resource policy for the installed desktop application. */
export function desktopContentSecurityPolicy(): string {
  return "default-src 'self' app:; " +
    "script-src 'self' 'unsafe-inline' app:; " +
    "style-src 'self' 'unsafe-inline' app:; " +
    "img-src 'self' data: app:; " +
    "connect-src 'self' http://localhost:5000 http://127.0.0.1:5000 app:; " +
    "font-src 'self' data: app:;";
}
