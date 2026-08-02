# DataLogicEngine security architecture and threat model

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ENG-004 |
| Title | Security architecture and threat model |
| Document version | v1.2.0 |
| Product version | 4.3.0 |
| Status | release_blocked |
| Audience | Security/privacy engineers, architecture, platform operations, quality, incident responders, and independent reviewers |
| Owner | Security Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Implemented trust boundaries, threat controls, security tests, release policy, and evidence |
| Confidentiality | Public |
| Last reviewed | 2026-08-01 |
| Next-review trigger | Trust boundary, identity, network, provider, connector, data protection, dependency, incident, or release-policy change |
| Requirements and evidence | Product requirements, source controls, threat tests, security workflows, SBOMs, and Phase 1/3/7/8/11/13/14 evidence |

## Security objective

Protect owner authority, credentials, private content, governed execution,
causal traces, app-owned data, release identity, and recovery paths while failing
closed when a required trust or readiness fact cannot be proved. The product is
single-owner and local-first, not trustless, air-gapped, multi-tenant, or
certified by default.

## Trust boundaries

1. Windows owner and protected installation/runtime root.
2. Electron main/preload versus the untrusted renderer surface.
3. Loopback backend authentication and versioned API envelope.
4. App-owned PostgreSQL, Redis, Neo4j, ChromaDB, and app-owned S3-compatible object store service identities.
5. Owner-configured OpenAI or Google provider egress.
6. Same-host Client Gateway applications and copy-once scoped keys.
7. Owner-approved MCP child processes, file roots, scopes, and credentials.
8. Exports, backups, support bundles, logs, update/release artifacts, and any
   media that leaves the protected runtime boundary.
9. Disabled private Windows gateway boundary pending TLS/firewall qualification.

The renderer, clients, providers, connectors, retrieved content, imported files,
tool results, and external networks do not become trusted merely because the
owner invoked them.

## Protected assets

- Installation secret, provider/connector/internal-service credentials,
  certificate private keys, backup passphrases, and update/signing authority.
- Prompts, messages, documents, chunks, evidence, tool inputs/results, AI output,
  sessions, knowledge, graph/vector/object data, memory, and exports.
- Policy, route, scope, budget, consent, migration, deletion, and release state.
- Causal run/trace identity, executed stages, claims, citations, hashes,
  signatures, audit, diagnostics, and incident evidence.
- App and service binaries, exact dependency locks, SBOMs, manifests,
  attestations, installer signatures, and publisher/distribution authority.

## Identity and least authority

Desktop local authentication binds a per-install secret, nonce/HMAC, timestamp
skew, loopback/Electron policy, installation identity, and Windows owner context.
Session routes retain CSRF/trusted-host/CORS/session controls. API routes use
JSON-native authentication; admin operations require explicit owner checks.

Client keys are copy-once, scoped, bounded, expiring, revocable, and isolated by
client ownership. Provider keys never reach clients or the renderer. MCP consent
binds the exact command fingerprint, file root, granular scopes, and encrypted
credentials. Caller-supplied authority and public registration are rejected.

## Network and process controls

The backend and internal services are loopback/private by default. An open port
is not trusted without installation-specific service identity verification.
Internal database/object/supervisor/diagnostic ports are not client interfaces.
CORS/browser and public-internet gateway use are unsupported.

The private Windows gateway remains disabled until exact signed-release TLS,
certificate chain/name/revocation, key ACL, firewall source/interface/profile,
two-machine, failure/recovery, redaction, update/rollback, and owner approval pass.

MCP supports local stdio only. The backend owns process lifecycle, bounded I/O,
timeout/cancellation, and a Windows Job Object that terminates the process tree.
Network connectors, shells/package runners, unrestricted file roots, and
repository hot-start are outside the initial contract.

## Governed AI and content controls

Requests pass the API/security envelope, injection defense, TruthGate policy and
budget controls, measured routing, bounded provider/tool execution, output
controls, evidence/claim validation, convergence, memory/audit, and causal trace.
Retrieved documents, provider output, and connector results remain untrusted.

Content is bounded, typed, hashed where required, redacted at output boundaries,
and checked for secret disclosure and prompt-injection indicators. The system
distinguishes policy, validation, provider, quota/rate, timeout, cancellation,
capability, readiness, and internal failures without exposing exception details
or inventing safe-looking success.

Phase 19 extends this boundary to every Knowledge Algorithm. Selection and
direct execution use server-owned principal/scope, policy, dependency DAG,
deadline, cancellation, recursion/fan-out, resource, provider/tool, and
side-effect budgets. Effectful KAs require risk-specific confirmation,
idempotency, an approved app-owned service port, and an authoritative receipt.
SDK-local handlers, direct provider/store/network access, unmanaged queues,
forged effects, dependency cycles, and silent exception skips are prohibited.
Per-KA tests cover injection, path/network abuse, unsafe input, resource
exhaustion, sensitive data, cancellation, duplicate requests, partial effects,
recovery, and trace-persistence failure as applicable.

CP19-I source qualification now enforces `max_effects` before execution and
connects this boundary to the durable simulation, MCP, and provider paths. MCP
inline credentials block before the connector call; post-call output remains
untrusted and is evaluated by bounded security/operations KAs. Provider
required context is budgeted before egress. Applied simulation/MCP/provider
receipts are emitted only by their owning services after the real operation and
require service, operation, resource, idempotency, request SHA-256, and result
SHA-256 identity. Complete per-KA adversarial proof remains CP19-K and
rebuilt-installed proof remains CP19-M.

CP19-J binds every direct product plan to the exact authenticated desktop
session or external client key. Its idempotency namespace, list/detail access,
confirmation token, cancellation, and evidence reads cannot cross that
principal boundary even when two client keys belong to the same local owner.
Inputs and results use authenticated encryption at rest; status/list responses
are content-free. Confirmation stores only an expiring digest bound to the plan
ID and request fingerprint. Content-free Redis leases prevent cross-worker
duplicate execution and are renewed while work is active. Startup
reconciliation fails an unleased interrupted run explicitly instead of
replaying a potentially effectful plan. An applied effect claim is rejected
unless its receipt has matching plan, service, idempotency, and SHA-256
identity. Expired runs are not readable and expired terminal/planned records
are purged with their encrypted request/result payloads.

## Data and secret protection

Production requires a protected Windows volume, restricted runtime-root ACLs,
DPAPI for installation/provider/connector/offline-replay secrets, and approved
field encryption. The renderer receives opaque file-picker tokens, not arbitrary
filesystem paths. Required data services reject development fallbacks.

Coordinated backups are encrypted with an unpersisted user recovery passphrase
and use a signed/hash-verified manifest. Secret/settings/environment files, logs,
and keys are excluded. Restore verifies an isolated root before activation.
Deletion reconciles required stores and reports partial failure.

Logs, metrics, errors, diagnostics, traces, exports, and support bundles exclude
or redact credentials, authorization headers, prompts/documents, provider
payloads, private keys, and decrypted backups according to their contract.
CP19-E also requires the complete L10 privacy suite to redact detected PII from
the released answer and all trace-bearing governed state; findings contain only
type/count summaries and never the matched clear-text values.
External telemetry is disabled by default and requires explicit opt-in; a DSN
alone cannot authorize egress.

## Release and update trust

Product 4.3.0, Windows 4.3.0.0, exact Python/Node/Electron locks, immutable
workflow actions, SBOMs, manifests, content inventories, attestations, publisher
identity, signature/timestamp, malware/license review, and release authority form
one promotion boundary. Candidate mode cannot authorize production.

Automatic update is disabled until signed metadata, publisher identity,
downgrade/replay/interruption/rollback, staged activation, and offline behavior
pass. Unsigned, wrong-publisher, tampered, replayed, downgraded, stale, or
unauthorized artifacts fail closed.

## Principal threats and controls

| Threat | Primary controls | Residual/required evidence |
|---|---|---|
| Malicious renderer/client | Preload allowlist, opaque tokens, API auth/scopes, no secrets/direct stores | Packaged penetration and client isolation review |
| Prompt/document/tool injection | Admission defense, untrusted labeling, bounds, secret/injection checks, evidence validation | Hostile installed corpus/connector matrix |
| Malicious or over-privileged KA selection/effect | Canonical manifest, server-owned context, policy/scopes, bounded DAG, confirmation, idempotency, authoritative service receipt, causal trace | Phase 19 per-KA adversarial/effect matrix at CP19-L and rebuilt-installed acceptance at CP19-M |
| Credential/content leakage | DPAPI/encryption, backend-owned calls, redaction, support preview, no direct provider access | Installed all-output canary/no-egress proof |
| Foreign service/port/process | Installation identity, immutable service verification, lock, supervisor, Job Object | Installed collision/restart matrix |
| Cross-store inconsistency or partial deletion | Durable authority, migrations, hashes/revisions, reconciliation, explicit partial failure | Populated installed repair/remnant evidence |
| Backup/update/supply-chain tampering | Encryption/manifests, signatures, exact locks, SBOMs, attestations, trust policy | Signed clean restore/update and independent review |
| Gateway network exposure | Loopback default, disabled private profile, TLS/firewall/client scopes | Two-machine signed qualification |
| Dependency vulnerability | Locked inventory, Dependabot/CodeQL/scans, release-blocking severity policy | Alert 389 patched or owner-accepted under policy |

## Incident response

Stop the affected external path or operation, protect people/data, preserve
redacted correlation and artifact identity, rotate/revoke exposed authority,
preview approved support evidence, repair the root cause without weakening the
gate, and rerun the exact normal/adversarial/failure/recovery matrix against the
replacement build. Vulnerabilities use the private process in root `SECURITY.md`.

## Current assurance status

Source/contract security gates cover authentication, public errors, trust
boundaries, provider budgets/privacy, data service identity, gateway scopes,
MCP consent/containment, diagnostics/support redaction, dependency/release trust,
and fail-closed update policy. Production remains **NO-GO** pending signed
installed security/privacy/network/failure matrices, protected-volume/ACL and
no-egress canaries, penetration and independent review, final legal/object-store
authority, and Phase 19 KA security/effect qualification. Alert 389 is fixed by
removing the affected SDK and qualifying the restricted replacement client; its
release evidence remains required. No certification or formal conformance
should be inferred from control mappings.
