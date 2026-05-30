# HTTPS/TLS Configuration Guide

## Document metadata

| Field | Value |
|---|---|
| Document version | v2.6.0 |
| Last updated | 2026-05-30 |
| Status | Active |
| Owner | Security Engineering + Platform Operations |
| Review cadence | Every 60 days |

## Purpose

Define HTTPS/TLS requirements for DataLogicEngine web/cloud deployments and clarify how those requirements differ from local-first Windows desktop loopback operation.

## Deployment-mode summary

| Mode | TLS requirement | Notes |
|---|---|---|
| Local-first Windows desktop | Not required for loopback-only desktop traffic. | Desktop trust relies on local/Electron/loopback checks, install secret, nonce, HMAC, timestamp skew, and local OS protections. |
| Windows VM | Depends on exposure. | If only accessed locally inside the VM, loopback/internal rules may apply. If exposed to users/network, use HTTPS/TLS. |
| Web/cloud production | Required. | Public or shared deployments must enforce HTTPS, secure cookies, trusted hosts, CORS restrictions, and production secrets. |
| API behind reverse proxy | Required at public edge. | Terminate TLS at trusted proxy/load balancer and forward only to trusted backend network. |

---

## Production HTTPS requirements

For web/cloud production deployments, DataLogicEngine requires HTTPS/TLS for:

1. secure cookie transmission;
2. session protection;
3. OAuth/OIDC/SSO redirect safety;
4. API confidentiality and integrity;
5. CSRF/CORS/trusted-host enforcement;
6. compliance and audit posture;
7. provider/connector callback protection where configured.

Mandatory production controls:

1. valid CA-issued certificate, not self-signed;
2. TLS 1.2 minimum;
3. TLS 1.3 preferred;
4. HTTP-to-HTTPS redirect;
5. HSTS enabled after validation;
6. secure cookies enabled;
7. certificate renewal monitoring;
8. no production wildcard CORS;
9. trusted hosts explicitly configured.

Recommended controls:

1. OCSP stapling where supported;
2. CAA DNS records;
3. Certificate Transparency monitoring;
4. automated certificate renewal;
5. staged certificate-rotation drills;
6. external TLS posture scan before production release.

---

## Certificate options

| Option | Best for | Notes |
|---|---|---|
| Let's Encrypt / ACME | most public web deployments | free, automated renewal, 90-day lifecycle. |
| Commercial CA | enterprise/customer-controlled domains | paid, support and org validation options. |
| Cloud provider certificate manager | cloud load balancers/CDNs | easy renewal, tied to cloud provider. |
| Internal enterprise CA | private enterprise networks | requires internal trust distribution and policy. |

Do not use self-signed certificates for public production.

---

## Example Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

Adjust backend/frontend proxying for the actual deployment topology.

---

## Application configuration checklist

For production web/cloud mode:

1. [ ] `FLASK_ENV=production` or equivalent production profile.
2. [ ] `SESSION_COOKIE_SECURE=true`.
3. [ ] `SESSION_COOKIE_HTTPONLY=true`.
4. [ ] `SESSION_COOKIE_SAMESITE` set appropriately.
5. [ ] trusted hosts configured.
6. [ ] CORS allowlist configured with no wildcard for production.
7. [ ] CSRF origin/token behavior validated.
8. [ ] rate limiting enabled.
9. [ ] production secrets sourced securely.
10. [ ] `AUTO_CREATE_SCHEMA` disabled.
11. [ ] `/health`, `/live`, `/ready`, `/metrics` validated behind HTTPS where exposed.

---

## Local-first desktop note

Do not confuse desktop loopback security with web/cloud TLS.

Desktop local mode uses a local trust boundary:

1. Electron/loopback runtime detection;
2. per-install secret;
3. nonce challenge;
4. HMAC signatures;
5. timestamp skew validation;
6. constant-time comparison;
7. DPAPI helper where available.

These controls are valid only for local/Electron/loopback contexts. They must not be treated as a public web/cloud authentication boundary.

---

## Validation

Recommended validation commands and checks:

```powershell
python scripts/runtime_precheck.py --strict --skip-ports --allow-env-from-process
python scripts/verify_environment_parity.py --strict
python scripts/verify_docs_references.py
```

For public endpoints, also perform:

1. browser HTTPS validation;
2. certificate chain validation;
3. redirect validation from HTTP to HTTPS;
4. cookie security flag inspection;
5. HSTS header inspection after rollout decision;
6. CORS and CSRF negative tests;
7. external TLS scan where appropriate.

---

## Release gates

Before public web/cloud release:

1. [ ] certificate installed and trusted;
2. [ ] automatic renewal tested;
3. [ ] HTTPS redirect tested;
4. [ ] secure cookies verified;
5. [ ] trusted hosts verified;
6. [ ] CORS allowlist verified;
7. [ ] CSRF behavior verified;
8. [ ] OAuth/OIDC redirect URLs use HTTPS;
9. [ ] rollback plan documented;
10. [ ] TLS/certificate evidence attached to release record.

## Change notes for v2.6.0

1. Added document metadata with explicit version and update date.
2. Renamed focus from SSL to HTTPS/TLS.
3. Distinguished local-first desktop loopback mode from web/cloud production TLS requirements.
4. Added deployment-mode matrix, app configuration checklist, validation checks, and release gates.
5. Removed cloud-only assumptions from the prior guidance.
