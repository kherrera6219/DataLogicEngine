# Auth surface matrix (desktop product)

| Field | Value |
|---|---|
| Date | 2026-08-12 |
| Product | Single-owner Windows desktop |
| Status | Authoritative for Phase 4 remediation |

## Principals

| Principal | How established | Used for |
|---|---|---|
| Desktop session user | Windows identity + install-secret HMAC challenge/auto-login + Flask-Login session | Control plane UI, settings mutations |
| Desktop request signature | Electron main rewrites loopback headers with HMAC | All renderer → backend calls on `:5000` |
| Client key (`ukg_…`) | Owner creates copy-once key in Settings → Client Gateway | External apps / SDK / OpenAI-compat clients |
| CSRF token | Session cookie + `X-CSRF-Token` on mutations | Browser/session POSTs (not desktop challenge endpoints) |

## Surfaces

| Surface | Auth | Notes |
|---|---|---|
| `/api/v1/auth/desktop/*` | Loopback + desktop header + challenge | CSRF exempt for challenge/auto-login |
| `/api/v1/gateway/*` | Session **or** client key (scoped) | Product generative boundary |
| `/api/v1/admin/*` (ops) | Session (owner) | Cache/health |
| `/api/v1/admin/gateway/*` | Session (owner) | Keys, providers, gateway status |
| `/api/v1/ka/*`, `/trace/*`, `/memory/*`, … | Session / login required per route | Control center |
| `/v1/*` OpenAI-compat | Client key | External integrators |
| `/graphql` | Session login required | No GraphiQL IDE |

## Explicitly not product auth

- Multi-user password login / MFA / SSO (retired)
- Replit auth (opt-in env only, not desktop default)
- Provider API keys never appear on client-key responses (`provider_credentials_exposed: false`)
