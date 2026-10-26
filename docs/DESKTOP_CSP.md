# Desktop Content-Security-Policy residual risk

| Field | Value |
|---|---|
| Date | 2026-09-27 |
| Code | `frontend/electron/main.ts` (`onHeadersReceived`) |

## Current policy (packaged renderer)

- `default-src 'self' app:`
- `script-src 'self' 'unsafe-inline' app:`
- `style-src 'self' 'unsafe-inline' app:`
- `connect-src` limited to self + loopback API (`localhost:5000` / `127.0.0.1:5000`) + `app:`
- `img-src 'self' data: https: app:` currently permits remote HTTPS image
  loads in the packaged renderer. This is a residual exposure, not proof that
  outbound egress is restricted to owner-configured model endpoints.

## Why `'unsafe-inline'` remains

Next.js static export used for the packaged UI injects inline script/style assets
that are difficult to nonce without a larger packaging redesign.

## Mitigations already in place

- `nodeIntegration: false`
- `contextIsolation: true`
- `sandbox: true`
- Navigation lock to `app:` / dev origin
- Window-open denied
- IPC channel allowlist + sender origin checks
- Desktop HMAC on loopback API calls

## Future harden path

Prefer nonces/hashes for script-src when the static export pipeline can emit them
without regressing Electron packaging.

CR-B must verify and disposition the effective packaged egress boundary,
including image loads, before an enforceable no-unapproved-egress claim can be
made. No outbound destination is approved by this document.
