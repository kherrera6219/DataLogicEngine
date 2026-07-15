# Model Context Protocol Connector Integration

## Document metadata

| Field | Value |
|---|---|
| Document version | v3.0.0 |
| Last updated | 2026-07-14 |
| Status | Phase 11 engineering checkpoint; installed production qualification open |
| Owner | Platform Engineering and Security |
| Decision record | `docs/adr/ADR-0008-governed-mcp-connector-boundary.md` |

## Current contract

DataLogicEngine supports owner-approved local MCP servers as governed external
connectors. The selected production candidate contract is deliberately narrow:

- MCP protocol version `2025-11-25`;
- local standard input/output (`stdio`) transport;
- one exact absolute executable with no shell or package runner;
- explicit working folder, file roots, scopes, limits, and consent fingerprint;
- app-owned process lifecycle and Windows Job Object containment;
- PostgreSQL authority, content-free Redis live state, and the `mcp-results`
  object bucket for large results;
- all connector output labeled untrusted and held outside answer authority until
  normal policy, privacy, evidence, validation, and trace controls accept it.

This checkpoint does not approve external MCP connectors for the production
release. Production start fails with `MCP_INSTALLED_QUALIFICATION_REQUIRED`
until the rebuilt-installed Windows process, file, network, lifecycle, Electron,
backup/restore, and adversarial acceptance matrix records qualification.

## Supported and absent capabilities

| Capability | Current status |
|---|---|
| Local stdio connector | Implemented and source-qualified |
| Exact command/scoped owner consent | Implemented |
| Tools, resources, and prompts reported by a running server | Implemented with partial-discovery state |
| Tool/resource/prompt results | Governed, hashed, bounded, redacted, and durably recorded |
| Explicit cancellation | Implemented for a server-owned running execution ID |
| Streamable HTTP or WebSocket MCP server | Not supported |
| Caller-selected resource subscriptions/SSE | Not supported; retired endpoints return 410 or JSON-RPC method-not-found |
| MCP sampling | Not advertised; requests fail closed because no approved governed provider path is exposed |
| Automatic repository configuration or hot start | Retired; `config/mcp_servers.json` is not an authority |
| Default UKG, pillar, graph, KA, or simulation connector | Removed; no placeholder default is registered |
| Network-capable stdio connector | Rejected pending a separately qualified network containment contract |

The REST API is the authenticated DataLogicEngine control plane. It is not a
claim that DataLogicEngine exposes the MCP Streamable HTTP transport.

## Trust and authority model

### Identity and scope

REST and JSON-RPC identity is derived from the authenticated server session or
desktop boundary. Caller-provided `user_id`, tenant, principal, role, or scope
fields are rejected. Missing execution context fails closed.

Connector scopes use this form:

```text
connector:<connector-name>:read
connector:<connector-name>:write
connector:<connector-name>:execute
```

Wildcards and scopes owned by another connector are rejected. The owner may
approve a non-empty subset of the requested scopes. A command/configuration
fingerprint change makes prior consent stale and prevents start.

### Command and capability policy

Registration validates before persistence and never starts the process. The
policy requires:

1. an absolute existing executable;
2. no PowerShell, command shell, script host, package runner, or shell control
   characters;
3. an absolute existing working folder inside an approved file root;
4. bounded arguments, environment, file roots, and resource limits;
5. secret environment variables expressed only as DPAPI credential references;
6. no network destinations under the current qualification;
7. granular connector-owned scopes.

The exact normalized definition is SHA-256 fingerprinted. The owner UI displays
the executable, arguments, file root, fingerprint, and requested access before
approval.

### Credentials

Credential values are accepted only during registration, protected with Windows
DPAPI, and stored as ciphertext in PostgreSQL. Renderer-safe responses contain
credential environment names and reference names only. Plaintext is resolved
inside the backend immediately before process creation and is never returned to
the renderer, ledger, Redis event, or log.

### Process lifecycle

The backend owns a durable asyncio loop for stdio readers across Flask requests.
Each connector is attached to a Windows Job Object with kill-on-close and a
process-memory ceiling. Start fails if containment cannot be established.
Timeout, malformed JSON-RPC, oversized output, stderr bounds, application exit,
stop, revoke, and process-tree termination are failure-first paths.

Named calls bind the durable `execution_id` to the running coroutine. An owner
cancellation cancels that operation, sends `notifications/cancelled` on a
best-effort basis, and persists terminal `cancelled` state. Timeout follows the
same bounded cancellation path.

Declared file roots are a policy and consent boundary. Installed production
qualification must still prove the final OS-level file-isolation mechanism; the
source checkpoint does not represent the Job Object as a filesystem sandbox.

## Result governance

Connector content is serialized into `mcp-result.v1` with:

- SHA-256 and byte length;
- `untrusted_connector_output` trust label;
- bounded content/preview;
- secret redaction;
- prompt-injection indicators;
- durable operation, scope, principal, duration, error, and trace metadata.

Results up to 64 KiB may be stored in the PostgreSQL execution record. Larger
results are stored in the required `mcp-results` object bucket with integrity
metadata and only the object key/hash retained in PostgreSQL. Execution-history
responses intentionally omit stored result content.

MCP output has no direct answer-producing path. A later governed request may use
connector evidence only through the standard DMRF, privacy, evidence, validator,
and trace boundary; the connector cannot mark its own output trusted.

## Persistence map

| Store | Responsibility |
|---|---|
| PostgreSQL `mcp_servers` | Validated renderer-safe definition, health, capabilities, consent state, command fingerprint |
| PostgreSQL `mcp_consent_grants` | Principal, exact fingerprint, requested/approved scopes, approval/revocation lifecycle |
| PostgreSQL `mcp_lifecycle_events` | Registered, approved, denied, started, stopped, revoked, and failure state |
| PostgreSQL `mcp_execution_records` | Server-owned request hash, required scopes, result hash/reference, trust, injection signal, error, duration, trace |
| PostgreSQL MCP tool/resource/prompt tables | Live discovered capability inventory and required scopes |
| Redis `mcp:live:*` | Content-free ephemeral lifecycle/execution state and bounded event stream |
| Object bucket `mcp-results` | Large governed result artifacts |

PostgreSQL remains authoritative. Redis can be rebuilt and never contains tool
arguments, result content, secrets, or credentials.

## Owner workflow

Use `/admin/mcp/servers`:

1. Register a connector with its absolute executable, one argument per line,
   working folder, approved file root, read/write request, and optional protected
   credential.
2. Review the exact rendered command, SHA-256 fingerprint, and each requested
   scope. Registration alone does not execute anything.
3. Approve only required scopes.
4. Start the connector. The backend negotiates the exact protocol version and
   discovers only capabilities the server reports.
5. Inspect health and discovered tools/resources/prompts in the MCP hub.
6. Stop, restart, revoke, or delete from the owner control surface. Revocation
   stops the process and clears approved scopes.

Production builds keep Start disabled in the backend until installed connector
qualification is recorded. Do not hand-set
`DLE_MCP_CONNECTORS_QUALIFIED=true`; the installed qualification controller is
the authority for that value.

## REST control-plane routes

Primary prefix: `/api/v1/mcp`.

| Method and route | Purpose |
|---|---|
| `GET /servers` | List PostgreSQL-owned definitions plus current in-process runtime inventory |
| `POST /servers` | Validate and register without executing |
| `GET /servers/{server_id}` | Renderer-safe detail |
| `DELETE /servers/{server_id}` | Stop and remove one connector |
| `POST /servers/{server_id}/consent` | Approve exact fingerprint and scope subset |
| `DELETE /servers/{server_id}/consent` | Revoke authority and stop |
| `POST /servers/{server_id}/start` | Start only after consent, fingerprint, credential, containment, and production-qualification checks |
| `POST /servers/{server_id}/stop` | Stop and reap the process tree |
| `POST /servers/{server_id}/restart` | Re-run the start checks after stop |
| `GET /servers/{server_id}/lifecycle` | Read bounded durable lifecycle history |
| `GET /servers/{server_id}/executions` | Read content-free durable execution history |
| `POST /servers/{server_id}/executions/{execution_id}/cancel` | Cancel one owned running operation |
| `GET /servers/{server_id}/tools` | List live discovered tools |
| `POST /servers/{server_id}/tools/{tool_id}/call` | Execute a server-bound tool under consent and scopes |
| `GET /servers/{server_id}/resources` | List live discovered resources |
| `GET /servers/{server_id}/resources/{resource_id}` | Read a server-bound resource under consent and scopes |
| `GET /servers/{server_id}/prompts` | List live discovered prompts |
| `POST /servers/{server_id}/prompts/{prompt_id}/get` | Resolve a server-bound prompt under consent and scopes |
| `GET /stats` | Live registry/runtime counts |
| `GET /config` | Renderer-safe PostgreSQL authority view |

Repository configuration updates, setup-default, and caller-selected
subscription endpoints are retired and return 410.

## Failure codes

Important stable codes include:

- `MCP_EXPLICIT_CONSENT_REQUIRED`;
- `MCP_CONSENT_FINGERPRINT_MISMATCH`;
- `MCP_CONSENT_SCOPE_DENIED`;
- `MCP_SCOPE_DENIED`;
- `MCP_CALLER_CONTEXT_REJECTED`;
- `MCP_EXECUTABLE_*`, `MCP_ARGUMENT_REJECTED`, and `MCP_CWD_*`;
- `MCP_NETWORK_CONNECTORS_NOT_QUALIFIED`;
- `MCP_PROCESS_CONTAINMENT_FAILED`;
- `MCP_OUTPUT_LIMIT_EXCEEDED` and `MCP_MALFORMED_JSON_RPC`;
- `MCP_REQUEST_TIMEOUT` and `MCP_EXECUTION_CANCELLED`;
- `MCP_REDIS_LIVE_STATE_UNAVAILABLE`;
- `MCP_INSTALLED_QUALIFICATION_REQUIRED`.

Public responses are generic and stable. Raw exceptions, stderr, arguments,
secret values, and result content do not appear in lifecycle/history errors.

## Qualification evidence and remaining gates

Source evidence is under `reports/production-readiness/2026/phase-11/`. Tests use
a real hostile stdio fixture for discovery, call, prompt/resource behavior,
delay, cancellation, malformed JSON-RPC, oversized output, and a spawned child
process. Policy tests cover command/path/argument/environment/network/scope
abuse, DPAPI serialization, caller-context forgery, ID binding, result injection,
and durable store behavior.

Still required against the rebuilt installed application:

1. OS-level file isolation and unauthorized file/network probes;
2. owner UI add/discover/call/cancel/stop/restart/remove acceptance;
3. backend/Electron crash, app exit, reboot, and orphan-process recovery;
4. real PostgreSQL/Redis/object-store restart and backup/restore parity;
5. packaged secret/log/support-bundle inspection;
6. visual/accessibility acceptance and malicious connector corpus execution.

## Protocol references

- MCP 2025-11-25 transports: <https://modelcontextprotocol.io/specification/2025-11-25/basic/transports>
- MCP authorization: <https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization>
- MCP security guidance: <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
- MCP changelog: <https://modelcontextprotocol.io/specification/2025-11-25/changelog>
- Sampling/roots/logging deprecation proposal: <https://modelcontextprotocol.io/seps/2577-deprecate-roots-sampling-and-logging>
