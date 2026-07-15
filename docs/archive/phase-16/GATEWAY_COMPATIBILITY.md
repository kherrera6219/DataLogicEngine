# Client Gateway Compatibility Matrix

## Document metadata

| Field | Value |
|---|---|
| Contract | `dle-gateway.v1` |
| Last updated | 2026-07-13 |
| Status | Active engineering contract; installed qualification pending |
| Owner | Platform Architecture + API Governance |

## Supported profiles

| Profile | Source implementation | Production disposition |
|---|---|---|
| `desktop_loopback` | Supported | Default desktop and built-in reference-client profile. |
| `same_host_gateway` | Supported | Named same-host applications use copy-once DataLogicEngine client keys. Installed acceptance remains pending. |
| `private_windows_gateway` | Fail-closed | Disabled until TLS/mTLS, certificate lifecycle, firewall, two-machine, security, and rollback qualification pass. |
| Public internet, anonymous, browser registration, multi-tenant SaaS | Not supported | Rejected product boundary. |

Provider credentials are never client credentials. OpenAI and Google keys remain
inside the installed service. Clients receive only `ukg_` DataLogicEngine keys.

## Native API and SDK window

| Client | Version | Contract | Supported behavior |
|---|---:|---|---|
| Native HTTP | `/api/v1`, `dle-gateway.v1` | Current | Sync chat, governed SSE, durable run/status/result/cancel, capabilities, trace summary, idempotency, typed failures. |
| Python SDK | `ukg-sdk` 0.7.x | `dle-gateway.v1` | Sync/async chat, SSE, durable jobs, cancellation, capabilities, trace/result reads, typed errors and safe retry. |
| TypeScript SDK | `@datalogicengine/sdk` 0.1.x | `dle-gateway.v1` | Chat, SSE, durable jobs, cancellation, capabilities, trace/result reads, typed errors and safe retry. |

The path version is authoritative. The SDKs reject an unexpected gateway
contract version. `docs/contracts/gateway-v1-compatibility.json` is the checked
baseline; CI fails when a published path, method, successful response, request
property, or enum value is removed without a new major contract.

## Native streaming behavior

The native SSE route emits live governed admission/stage, heartbeat,
backpressure, evidence, validation, completion, cancellation, and safe-failure
events. Provider answer text is withheld until validation succeeds, then emitted
as `delivery_mode: validated_output` chunks. This is not raw provider-token
streaming. Resume and replay of a disconnected stream are not supported in v1;
clients must start a new idempotent sync request or durable async run.

## Durable job behavior

- A create request requires an idempotency key.
- PostgreSQL is the job authority and stores encrypted request state.
- Redis holds expiring content-free worker leases, cancellation, and state.
- Small encrypted results remain in PostgreSQL.
- Large encrypted retained results use the app-owned S3-compatible
  `gateway-results` bucket and are hash-verified before release.
- An interrupted running job is not automatically replayed because provider
  spend may already have occurred. It terminates as
  `JOB_INTERRUPTED_RETRY_UNSAFE`.

## Bounded OpenAI compatibility

The optional facade is shape compatibility, not provider impersonation. Both
routes still require a DataLogicEngine client key and enter the canonical
governed orchestrator.

| OpenAI-style field or behavior | Status | DataLogicEngine behavior |
|---|---|---|
| `GET /v1/models` | Supported | Returns only `dle-standard`, `dle-enhanced`, and `dle-local-review`. |
| `POST /v1/chat/completions` | Supported | One completion through the native governed contract. |
| `messages` | Supported | `user`, `assistant`, and `system`; native size limits apply. |
| `stream` | Supported | OpenAI-shaped SSE chunks; output remains validation-gated. |
| `temperature` | Supported | Range 0 through 2. |
| `max_tokens` or `max_completion_tokens` | Supported | One may be supplied; server/client policy can lower the ceiling. |
| `n` | Supported only as `1` | Any other value is rejected. |
| `user` | Supported | Becomes bounded session identity, not a multi-tenant user account. |
| `Idempotency-Key` | Sync only | Streaming rejects resume semantics that have not qualified. |
| Tools/functions, logprobs, penalties, seed, response format, raw provider model names, provider overrides | Not supported | Unknown or unsupported fields are rejected with `422`; none are silently ignored. |

The compatibility response contains a `dle` extension with governed request,
run, trace, confidence-measurement, and actual provider/model information.

## Qualification boundary

Source tests do not satisfy signed-installed interoperability. Same-host and
private two-machine OpenAI/Google acceptance, certificate/firewall drift,
restart, failure/load/soak, clean upgrade/rollback, and provider-configured
trace evidence remain Phase 8 release blockers for the rebuilt application.
