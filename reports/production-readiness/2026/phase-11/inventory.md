# Phase 11 MCP and Connector Inventory

Date: 2026-07-14
Status: live before-change inventory
Plan authority: `PRODUCTION_COMPLETION_PLAN_2026.md`, Phase 11

## Supported production contract selected for implementation

- External MCP connectors use the standard `stdio` transport only.
- The negotiated stable protocol baseline is `2025-11-25`.
- The authenticated loopback REST and JSON-RPC endpoints are DataLogicEngine
  control-plane adapters; they are not a public Streamable HTTP MCP server.
- Streamable HTTP, legacy HTTP+SSE, arbitrary desktop IPC, remote MCP OAuth, MCP
  tasks, roots, elicitation, and connector-initiated sampling are not production
  capabilities in this phase. They must be absent or fail closed.
- Resources, prompts, and tools are exposed only when backed by real operations.
  Connector results remain untrusted evidence until they pass DataLogicEngine
  privacy, injection, evidence, validation, and trace controls.
- A local connector command is code execution. Registration does not execute it;
  the owner must approve the exact command fingerprint and requested scopes before
  start or after any scope/command expansion.

The selection follows the current official MCP stable transport and security
guidance: stdio is a standard transport; local-server startup requires exact
command visibility and explicit consent; HTTP authorization does not apply to
stdio; and local HTTP transports require additional origin, authentication, and
DNS-rebinding controls that are outside the selected Phase 11 production set.

## Live implementation map

| Surface | Current implementation | Before-change finding |
|---|---|---|
| REST control plane | `backend/routes/mcp_routes.py` | Auth decorators exist, but configuration is written directly to repository JSON and immediately hot-started. Resource/tool/prompt IDs are not consistently bound to the requested server. |
| JSON-RPC adapter | `backend/mcp_server/router.py` | Server-owned context reaches tool calls, but the adapter advertises an obsolete `0.1.0` protocol plus resources and sampling that it does not govern completely. |
| Scope authority | `core/mcp/scope_enforcement.py` | REST tool calls fail closed, but the shared helper still permits missing context by default when strict mode is not enabled. |
| Subscriptions | `backend/mcp_server/subscriptions.py` | State is process-memory only and the caller may choose `clientId`; the SSE route accepts a caller-selected stream identifier. |
| Sampling | `backend/mcp_server/sampling.py` | With no provider it returns a deterministic echo labelled as a local completion. This is fabricated production behavior. |
| External server configuration | `config/mcp_servers.json` and `core/mcp/mcp_manager.py` | The tracked default uses unpinned `npx -y`; command, arguments, cwd, environment, file, network, and consent policy are not validated. |
| Process lifecycle | `core/mcp/mcp_client.py` | Subprocesses inherit the full environment; stdout/stderr, request duration, and output are unbounded; stop calls terminate only the immediate process; per-request Flask loops cannot own durable background readers. |
| Built-in system tools | `core/mcp/servers/system.py` | File paths use a string-prefix containment test and tools carry no granular scope metadata. `web_search` returns simulated results. |
| Default UKG server | `core/mcp/mcp_manager.py` | Pillars are hardcoded; graph/KA/simulation paths return unavailable, formatted fake, or error strings as successful tool/resource results; KA modules are imported and invoked directly instead of through the governed KA controller. |
| Durable authority | `models.py` MCP tables | Server/resource/tool/prompt metadata exists, but there is no durable consent grant, lifecycle event, execution/result/error ledger, command fingerprint, containment state, or credential reference authority. |
| Credential boundary | MCP configuration and API serialization | Environment values can be stored and returned in plaintext. MCP-specific DPAPI protection and renderer-safe redaction are absent. |
| Result governance | REST/JSON-RPC tool paths | Tool results are stringified and returned without an untrusted-evidence envelope, prompt-injection classification, size cap, privacy gate, durable result hash, or trace association. |
| Admin UI | `frontend/app/admin/mcp` | The UI can register a name/version and delete it, but cannot review the exact executable/args, requested roots/network/scopes, approve/revoke consent, start/stop/restart, inspect discovery/health, or see governed execution records. |
| Existing tests | Phase G, integration route, and unit MCP tests | Fourteen tests pass, but they preserve fake sampling and permissive mocked `npx` startup. Two un-awaited mock warnings reveal lifecycle cleanup weakness. No malicious fixture coverage exists. |

## Before-change baseline

Command:

```text
python -m pytest tests/phase_g/test_advanced_mcp.py tests/integration_routes/test_mcp_route_auth_boundaries.py tests/unit/test_mcp_tracing_repo_rest_coverage.py -q
```

Result: `14 passed, 2 warnings in 1.46s`.

The warnings are un-awaited mocked subprocess `write` and `terminate` calls. A
green baseline is not Phase 11 acceptance because the tests currently assert the
fake sampling path and do not exercise containment, consent, durable lifecycle,
or malicious connector behavior.

## First implementation sequence

1. Add failure-first tests for context authority, exact consent fingerprints,
   configuration validation, command/path/env/network rejection, output bounds,
   prompt-injection classification, timeout/cancellation, and server-object
   binding.
2. Add durable PostgreSQL models and migration for consent, lifecycle, execution,
   result/error hashes, containment state, and DPAPI credential blobs.
3. Replace repository JSON auto-start with server-owned database configuration,
   validation, explicit approval, and start/stop/restart operations.
4. Put stdio clients on a durable runtime loop with bounded JSON-RPC, minimal
   environment, redacted logs, timeouts, cancellation, and Windows process-tree
   cleanup.
5. Remove fake/default registrations and route each retained UKG, graph, KA, or
   provider behavior through a real governed service.
6. Add the owner-facing consent/lifecycle/health UI and finish focused plus full
   regression evidence.

## Installed gate boundary

Engineering can prove fail-closed behavior, Windows job/process-tree code, and
malicious fixtures in the repository. Final CP11-C/CP11-E acceptance still needs
the rebuilt installed application to demonstrate process containment, ACL and
DPAPI behavior, start/call/cancel/stop/restart/remove, crash recovery, and no
orphaned children on the supported Windows matrix. Those installed checks remain
open and do not permit a production-ready claim.
