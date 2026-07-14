# DataLogicEngine Local-First Threat Model

## Document metadata

| Field | Value |
|---|---|
| Document version | v1.1.0 |
| Last updated | 2026-07-13 |
| Status | Active production-completion baseline |
| Owner | Security Engineering |
| Scope | Windows 11 Electron desktop, loopback Flask backend, same-host API gateway, local data services, configured providers and MCP connectors |

## Security objective

Protect the Windows user's credentials, governed requests, local knowledge,
traces, databases, and administrative controls while permitting the packaged
Electron shell and explicitly approved same-host gateway clients to use only
their intended capabilities.

This is a local-first product, not an anonymous public service. Before Phase 8,
all inbound listeners are loopback-only. Private-network exposure, TLS/mTLS,
certificate policy, and firewall qualification are not enabled by Phase 1.

## Trust boundaries

1. **Windows user to Electron main process.** The signed desktop shell owns
   local file pickers, protected secret storage, backend lifecycle, and the
   narrow preload bridge.
2. **Renderer to Electron main process.** The renderer is untrusted. It receives
   typed IPC methods and opaque, single-use, expiring path tokens; it never
   receives selected filesystem paths or secret material.
3. **Electron main process to Flask.** Requests are loopback-only and signed
   with the per-install secret, timestamp, and one-time request nonce. Path
   operations also carry a purpose-bound main-process IPC signature.
4. **Same-host client to API gateway.** External client keys are limited to
   explicitly exposed gateway operations and key policy. They cannot satisfy
   owner/admin decorators or obtain provider credentials.
5. **Flask to local data services.** PostgreSQL, Redis, Neo4j, ChromaDB, and
   object storage are internal capabilities. Phase 1 does not authorize a
   private listener for them.
6. **Flask to providers and MCP connectors.** Provider and connector responses
   are untrusted input. Credentials remain backend-owned and are never returned
   through API, GraphQL, MCP, IPC, log, or backup contracts.
7. **Runtime data to backup/export destinations.** Backups may contain governed
   user data, but runtime secret files, settings files, `.env`, logs, and
   machine-bound key material are excluded.

The generated live inventory at
`reports/production-readiness/2026/phase-01/runtime/route-manifest.json` covers
Flask routes, GraphQL operations, IPC channels, MCP methods, file capabilities,
and network surfaces.

## Protected assets

- desktop install/HMAC secret, session secret, KEK/DEK material, provider keys,
  internal-service credentials, connector credentials, and gateway keys;
- Windows identity, authenticated principal, roles/scopes, tenant context, and
  CSRF state;
- prompts, uploaded/ingested documents, knowledge graph content, model output,
  traces, audit records, simulations, and local databases;
- installer/update artifacts, packaged renderer files, and policy/configuration;
- encrypted backup archives, owner recovery secrets, manifests, restored roots,
  and prior roots retained for rollback.

## Threats, controls, and residual risk

| Threat | Phase 1 controls | Residual risk and next owner |
|---|---|---|
| Malicious local process | Loopback is not treated as identity; every protected route requires session, scoped client key, or signed desktop authentication. Desktop signatures have timestamp and one-time request-nonce replay checks. Host and Origin are validated. | A process running as the same Windows user can still attack process memory or UI automation. Code signing, installer/update trust, and OS-hardening evidence continue in Phases 14-16. |
| Compromised renderer or XSS | `nodeIntegration=false`, context isolation, sandbox, web security, exact IPC origin parsing, navigation/window denial, backend-only provider egress CSP, typed preload methods, schema validation, timeouts, and cancellation. File paths stay in main-process memory behind expiring tokens. | A renderer compromise can invoke approved capabilities as the user. Capability minimization and real packaged E2E remain mandatory at every release checkpoint. |
| Hostile document or ingestion source | The user selects the source with the OS picker. Main consumes a single-use token, validates bounded options, and uses a purpose-bound IPC signature. Backend file type, size, recursion, and parsing limits remain authoritative. | Parser-library defects and decompression/resource bombs remain possible. Dependency scanning and later ingestion budgets/soak tests remain required. |
| Malicious MCP server or connector | REST and JSON-RPC execution context is server-owned. Caller identity/tenant/role/scope fields are rejected. Missing scope context fails closed and external keys receive only explicit connector scopes. Public exceptions are normalized. | A permitted connector can return hostile or misleading content. Outputs remain untrusted and must pass governed reasoning/tool-result controls in later phases. |
| Compromised AI provider | Provider calls originate in the backend, provider secrets are not serialized, renderer CSP blocks direct provider egress, and provider failures are normalized. | A provider sees the content intentionally sent to it and can return malicious output. Provider minimization, disclosure, and governed-output validation remain continuous controls. |
| Malicious or compromised gateway client | Gateway key policy constrains permitted provider/model/token use. Owner/admin, provider-key management, storage lifecycle, MCP configuration, and internal diagnostics require the desktop owner/session principal. | Abuse within granted gateway scope remains possible. Per-client concurrency, budget, async, and installed interoperability controls continue in Phases 7-8. |
| Credential or key theft at rest | Desktop secrets use Electron `safeStorage`; backend install/provider/internal-service credentials use DPAPI; files receive restrictive current-user/System ACLs. Plaintext runtime `.env` secrets migrate into protected storage. | DPAPI and ACLs do not protect against compromise of the logged-in Windows user. Memory/process inspection remains a same-user residual risk. |
| Replay | Desktop auto-login challenge nonces are single-use. Every signed desktop request carries a unique nonce retained through the timestamp window. IPC file-operation signatures bind method, path, timestamp, nonce, and capability purpose. | Replay state is process-local by design because Phase 1 supports one desktop backend process. Multi-process/private gateway replay storage belongs to Phase 8. |
| Concurrency or limit abuse | HTTP request limits, rate limiting, bounded GraphQL depth/field counts, IPC timeouts/cancellation, file-size limits, and MCP scope checks fail closed. | Complete per-client admission budgets, async cancellation, and performance/soak qualification continue in Phases 7, 12, and 13. |
| Private-listener exposure | `main.py`, `app.py`, and `wsgi.py` use a shared fail-closed listener policy accepting only localhost/loopback. `0.0.0.0`, private addresses, public addresses, hostnames, and proxy Host overrides are rejected before Phase 8. | No private-network use is supported yet. Any future enablement requires the Phase 8 TLS/mTLS, certificate, firewall, and two-machine qualification gate. |
| Certificate or firewall failure | Private listener is disabled, so certificates and firewall rules are not accepted as Phase 1 compensating controls. | Becomes applicable only if Phase 8 enables a qualified private profile. |
| Update tampering | Auto-update remains disabled unless separately qualified; new windows and remote renderer navigation are denied. | Signing, provenance, anti-rollback, and updater failure testing are Phase 14 release gates. |
| Database theft | Provider credentials stored in the database are DPAPI-protected and cannot be decrypted under a different Windows user. Production requires BitLocker/device encryption and restricted runtime-root ACLs, verified at startup. | The current development machine did not prove the supported installed protected-volume/ACL matrix. Same-user live compromise and offline copies made before encryption remain residual risks. |
| Backup theft or tampering | Portable backups use scrypt-derived AES-256-GCM encryption plus a signed/hash-verified manifest; machine-bound secret vaults, `.env`, settings, and logs are excluded. The recovery secret is not stored. | Loss of the recovery secret makes the archive unrecoverable. Owner-selected destinations, copied archives, and retained prior roots require their own access/retention controls until the signed installed recovery matrix passes. |
| Partial cross-store restore or delete | Restore occurs in an isolated clean root and activates atomically only after per-store and cross-store verification. Deletion retains a non-PII tombstone and fails visibly if any store has unapproved remnants. | Signed clean-machine recovery, 0.1.1 retained-data upgrade, disk/capacity failure, and the full installed deletion matrix remain release gates. |
| Raw exception or secret disclosure | Repository-wide route scanning, sentinel response tests, stable public errors, GraphQL normalization, log redaction, provider serialization restrictions, and secret gates prevent known sinks. | New routes/sinks can regress; the mandatory gates must run at every security/API checkpoint. |

## Trust decisions

- Loopback address, Host, Origin, and possession of a route URL are never
  sufficient authentication.
- External API keys are client principals, not desktop owner principals.
- Renderer values are untrusted even when the renderer is packaged.
- Caller-supplied MCP identity/scope context is always discarded or rejected.
- DPAPI protects data at rest for the current Windows user; it is not a sandbox
  against that same user while the application is running.
- No private-network listener is supported before Phase 8.

## Required verification

Phase 1 is not closed unless the following remain green:

```text
scripts/verify_route_manifest.py --fail-unclassified
scripts/verify_public_error_contracts.py
scripts/verify_electron_security.py --require-packaged-renderer
scripts/verify_secret_storage.py
tests/security
tests/integration_routes
```

Any new Flask route, GraphQL operation, IPC channel, MCP method, file
capability, or listener must be classified before merge. Any change that
weakens a trust decision above reopens Phase 1.
