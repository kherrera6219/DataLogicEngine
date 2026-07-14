# Phase 8 External Gateway Engineering Checkpoint

Date: 2026-07-13

Verdict: **CP8-A, CP8-D, CP8-E, and CP8-H passed. CP8-B, CP8-C, CP8-F,
CP8-G, and CP8-J passed at the source/engineering boundary with installed proof
retained. CP8-I and every rebuilt-installed acceptance item remain deferred
release blockers. Production/public release remains NO-GO.**

## Delivered

- Defined `dle-gateway.v1`, three fail-closed profiles, explicit owner/desktop/
  service/client principals, least-privilege scopes, PostgreSQL-authoritative
  virtual models, and ADR-0005.
- Added copy-once `ukg_` client credentials, bounded rotation overlap, immediate
  revoke/expire, deletion, last-use and lifecycle audit, and per-client provider,
  model, request, token, concurrency, and scope policy.
- Replaced process-local admission with atomic Redis minute/day/concurrency
  controls and added content-free expiring worker leases, state, and cancellation.
- Published strict native sync, stage-native governed SSE, durable async/status/
  result/cancel, durable idempotency, capabilities, owned trace summaries, stable
  error envelopes, and bounded `/v1/models` and `/v1/chat/completions` behavior.
- Kept all answer-producing routes on `governed.v1`. SSE reports actual stages
  and withholds provider text until validation before `validated_output`.
- Added PostgreSQL authorities for virtual models, idempotency, and durable jobs;
  encrypted large results use the app-owned `gateway-results` S3 bucket with
  size/hash verification and safe unavailable behavior.
- Added restart-safe job disposition, per-client execution concurrency, key-
  lifecycle cancellation, and explicit unsafe-to-replay terminal behavior.
- Separated outbound Provider Connections from inbound Client Gateway desktop
  administration and added truthful client usage, jobs, health, and examples.
- Added Python SDK 0.7.0, a TypeScript SDK, PowerShell/Python/TypeScript/OpenAI
  examples, OpenAPI compatibility diff CI, compatibility documentation, and a
  private gateway runbook.

## Checkpoint disposition

| Checkpoint | Result | Evidence |
|---|---|---|
| CP8-A - Product boundary | Passed | Versioned profiles, principals, scopes, virtual models, ADR-0005, architecture and security contracts. |
| CP8-B - Secure profiles | Engineering passed; installed retained | Loopback default and unsupported/private exposure fail closed; installed TLS/firewall/certificate/private proof is deferred. |
| CP8-C - Client identity | Engineering passed; installed retained | Copy-once/create/auth/rotate/revoke/expire/delete/audit tests pass; expanded installed backup/restore and compromise drill are deferred. |
| CP8-D - API contract | Passed | Native sync/SSE/async/cancel/idempotency/discovery/error/trace and bounded OpenAI contract tests pass. |
| CP8-E - Canonical causality | Passed | Gateway and compatibility routes adapt into `governed.v1`; validation cannot be bypassed and provider text is not released early. |
| CP8-F - Control plane | Engineering passed; installed retained | Split settings and backend lifecycle/usage/job contract tests pass; packaged visual and reference-client acceptance are deferred. |
| CP8-G - Data plane | Engineering passed; installed retained | PostgreSQL/Redis/S3 authorities, encrypted object results, hashes, leases, cancellation, and fail-closed tests pass; installed expanded lifecycle drill is deferred. |
| CP8-H - SDK and docs | Passed | OpenAPI, compatibility baseline/diff, Python and TypeScript SDKs, examples, API/versioning/runbook docs agree. |
| CP8-I - Installed interoperability | Deferred release blocker | Rebuilt same-host and private two-machine clients must complete real governed OpenAI and Google requests. |
| CP8-J - Failure and load | Engineering passed; installed retained | Failure-first auth/schema/scope/limit/idempotency/cancel/restart/object/security tests pass; installed load/soak/failure matrix is deferred. |

## Validation snapshot

- Backend: 1,993 passed, 18 skipped, 21 warnings in 109.83 seconds.
- Frontend: 403 passed across 82 files; typecheck and production build passed;
  lint passed with one pre-existing warning and zero errors.
- Python SDK: 30 passed.
- TypeScript SDK: 5 passed; build passed.
- Contract suite: 22 passed, 1 skipped; OpenAPI compatibility diff passed.
- Migration suite: 18 passed; 21 revisions, one head `b7c8d9e0f1a2`.
- Focused gateway, admission, idempotency, jobs, trace, object-result, storage,
  route, and compatibility selections passed.
- Ruff, Python compilation, documentation validation, and whitespace validation
  passed at checkpoint close.

See `checks.json`, `artifacts.json`, `test-results/summary.md`,
`docs-reviewed.md`, `risk-register.md`, and `rollback.md` for the handoff record.
