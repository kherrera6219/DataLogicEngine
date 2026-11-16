/** Match a desktop service by its parsed origin, never by a URL prefix. */
export function isLocalServiceRequest(requestUrl: string, port: number): boolean {
  let url: URL;
  try {
    url = new URL(requestUrl);
  } catch {
    return false;
  }

  return url.protocol === 'http:' &&
    (url.hostname === 'localhost' || url.hostname === '127.0.0.1') &&
    url.port === String(port) &&
    url.username === '' && url.password === '';
}
