# Private Windows Gateway Qualification Runbook

## Current status

`private_windows_gateway` is intentionally disabled and unqualified. Setting
`DLE_GATEWAY_PROFILE=private_windows_gateway` fails closed. This document defines
the later qualification procedure; it is not permission to expose the current
application on a private or public network.

## Entry requirements

Qualification may start only from the signed rebuilt release candidate after:

1. full PostgreSQL, Redis, Neo4j, ChromaDB, and MinIO readiness passes;
2. one owner-supplied OpenAI and Google credential passes installed validation;
3. same-host native, SSE, async/cancel, SDK, and compatibility acceptance passes;
4. backup/restore and rollback succeed with gateway client/job state;
5. the security review approves the certificate, listener, firewall, key,
   logging, support-bundle, and incident-response design.

## Required configuration

1. Select a certificate trusted by the approved client machine. Validate the
   subject/SAN, chain, purpose, key usage, expiration, and revocation behavior.
2. Protect the private key with Windows ACLs and the approved local secret
   boundary. Never include it in logs, backup plaintext, or support bundles.
3. Bind only the approved gateway address and port. Internal PostgreSQL, Redis,
   Neo4j, ChromaDB, MinIO, supervisor, and diagnostic ports remain unreachable.
4. Create a Windows Firewall rule only after owner confirmation. Restrict
   profile, interface, source range, address, protocol, and port.
5. Issue a least-privilege copy-once DataLogicEngine client key. Optional mTLS
   certificate identity is recorded separately from API-key identity.
6. Keep CORS disabled. Browser clients and public-internet exposure are outside
   the approved product boundary.

## Acceptance matrix

From a separate supported Windows client, verify:

- valid TLS chain/name and failure for an untrusted, expired, revoked, or
  mismatched certificate;
- native sync, live governed SSE, durable async/result/cancel, idempotent retry,
  Python SDK, TypeScript SDK, and bounded OpenAI compatibility;
- least-privilege scope denial, immediate key revocation, rotation overlap,
  expiry, queue/concurrency isolation, and no cross-client trace/job access;
- provider, Redis, PostgreSQL, object-store, network, disk, and application
  restart failure behavior without duplicate provider spend or silent bypass;
- firewall drift detection and safe listener shutdown;
- no provider credentials, authorization headers, prompt/response content, or
  certificate private material in logs, errors, metrics, exports, or support;
- backup/restore, upgrade, rollback, repair, disable, and uninstall handling.

## Disable and incident response

1. Disable the private profile and stop the listener.
2. Remove or disable the application-owned firewall rule.
3. Revoke affected DataLogicEngine client keys and mTLS identities.
4. Replace or revoke the certificate if private-key compromise is possible.
5. Preserve redacted audit, trace, and system evidence; do not export content or
   secret material by default.
6. Re-enable only after the root cause is corrected and the acceptance matrix is
   rerun against the exact replacement build.

## Exit record

Record the signed installer hash, source commit, machines/Windows builds,
certificate identity and dates (never the private key), firewall rule, client
versions, provider/model, timestamps, test results, failures, recovery results,
reviewers, and final approval. Until that record is accepted, the profile stays
disabled.
