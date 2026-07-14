# ADR-0005: External Gateway Principal, Profile, and Virtual-Model Boundary

## Metadata

| Field | Value |
|---|---|
| Status | Accepted for Phase 8 implementation; private exposure remains qualification-gated |
| Date | 2026-07-14 |
| Decision owner | Kevin |
| Plan authority | Phase 8, sections 16.1-16.4 |
| Contract version | `dle-gateway.v1` |

## Context

DataLogicEngine must serve named same-host and, later, qualified private Windows
applications without treating those applications as desktop users, exposing
provider credentials, or creating a second reasoning path. The pre-Phase 8
gateway mixed desktop session routes with external API-key routes, used broad
read/write permissions, exposed provider topology, and lacked a versioned
product-profile and virtual-model boundary.

## Decision

1. The supported profiles are `desktop_loopback`, `same_host_gateway`, and
   `private_windows_gateway`. Loopback is the default. Private mode fails closed
   until TLS, certificate, Windows Firewall, client-policy, and two-machine
   qualification pass.
2. Owner, desktop-session, service, and external-client principals are distinct.
   An external client key never grants desktop control-plane or provider-
   administration authority.
3. External client permissions use explicit scopes: `chat`, `stream`,
   `run:create`, `run:read`, `run:cancel`, `trace:read`, `evidence:read`, and
   `models:read`. Direct provider/model selection additionally requires
   `routing:override`. Administrative scopes cannot be granted to normal clients.
   Retained legacy read/write metadata is migration-only; read never permits
   model execution.
4. `dle-standard`, `dle-enhanced`, and `dle-local-review` are governed virtual
   models. Their execution mode and provider-call ceiling are applied by the
   server. Direct provider/model overrides require both an applicable client
   scope and the key's server-owned allowlist.
5. Google and OpenAI credentials, concrete provider inventory, and administrative
   status remain owner control-plane data. Authenticated external capability
   discovery returns only the contract version, active safe profile, authorized
   scopes, and virtual-model catalog.
6. Native `/api/v1/gateway` is the authoritative external contract. The built-in
   desktop client and external clients converge on the same `GovernedRequest`
   and orchestrator, differing only in authenticated principal and server-owned
   policy.
7. An OpenAI-compatible facade is not implied by this ADR. It may be added only
   after an exact compatibility matrix, strict unsupported-field rejection, and
   proof that the adapter cannot bypass the native contract.
8. Current SSE remains truthfully described as buffered governed delivery. It is
   not called native provider-token streaming until the Phase 8 event,
   cancellation, disconnect, backpressure, resume, and persistence gates pass.

## Alternatives considered

1. Reuse desktop user/session authorization for application clients. Rejected
   because it grants the wrong authority and prevents per-client isolation.
2. Expose concrete provider/model inventory and accept provider keys from each
   client. Rejected because it leaks topology and moves credential custody out
   of the application.
3. Present unqualified OpenAI compatibility as the primary API. Rejected because
   permissive shape adaptation could silently discard fields or bypass governed
   behavior.
4. Enable private HTTP immediately and qualify TLS later. Rejected because it
   expands the Windows trust boundary before its controls are proven.

## Consequences

- Client authentication is header-based and uses copy-once `ukg_` secrets;
  browser session CSRF rules remain separate.
- Production admission counters fail closed when required Redis state is
  unavailable.
- Desktop provider and session-history routes reject client-key principals.
- OpenAPI, SDKs, examples, and compatibility tests must pin `dle-gateway.v1`.
- Private access, native SSE, durable asynchronous runs, idempotency, client-key
  rotation/deletion, and the compatibility facade remain Phase 8 gates, not
  capabilities accepted by this record.

## Implementation references

- `backend/llm_gateway/external_contract.py`
- `backend/llm_gateway/admission_limiter.py`
- `backend/llm_gateway/api.py`
- `backend/llm_gateway/schemas.py`
- `backend/security/listener_policy.py`
- `docs/openapi.yaml`
- `tests/unit/test_phase8_gateway_contract.py`
- `tests/contract/test_phase8_gateway_openapi_contract.py`

## Supersedes / superseded by

- Supersedes: none
- Superseded by: none
