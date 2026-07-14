# ADR-0008: Governed MCP Connector Boundary

## Document metadata

| Field | Value |
|---|---|
| Status | Accepted - Phase 11 engineering selection; installed production qualification open |
| Date | 2026-07-14 |
| Owner | Platform Architecture and Security |
| Decision scope | External MCP protocol, transport, authority, process, persistence, and result boundary |
| Supersedes | Implicit multi-transport/default-UKG behavior in earlier MCP documentation |
| Superseded by | None |

## Context

The previous MCP implementation mixed in-memory demo servers, caller-selected
subscription identities, deterministic echo sampling, repository JSON hot-start,
package-runner commands, and formatted UKG/KA/graph placeholders. It did not
provide one durable consent, process containment, credential, lifecycle, or
result-governance boundary suitable for the Windows product.

MCP is an external code and data boundary. A connector can execute a child
process, receive selected input, return adversarial content, and attempt file,
network, resource, or scope expansion. Supporting every protocol transport and
feature before the installed containment contract is proven would enlarge the
release surface without a required product workflow.

## Decision

DataLogicEngine selects MCP `2025-11-25` over local stdio as the only external
connector transport candidate for the initial Windows production release.

- The authenticated REST/JSON-RPC control plane derives identity and scope from
  server state. It is not an MCP Streamable HTTP transport.
- Registration validates and persists one absolute executable, arguments,
  working folder, file roots, environment references, scopes, and limits without
  executing it.
- The owner approves the exact SHA-256 command fingerprint and a granular scope
  subset before first start or scope expansion.
- Secret values are DPAPI protected and never returned to the renderer.
- The backend owns the durable stdio event loop and Windows Job Object. Process
  start fails if containment is unavailable; stop/app exit kills the tree.
- PostgreSQL owns configuration, consent, lifecycle, discovery, and executions;
  Redis carries content-free live state; large governed results use the
  `mcp-results` object bucket.
- Connector output is untrusted evidence. It cannot bypass DMRF, privacy,
  evidence, validation, or trace controls to influence an answer.
- Network-capable connectors, Streamable HTTP, WebSocket, caller-selected
  subscriptions, and MCP sampling are absent from the initial production
  contract.
- Default UKG/pillar/KA/graph/simulation registrations are removed. Future
  built-ins must call real approved services under the same contract or remain
  absent.
- Production start remains disabled until rebuilt-installed qualification sets
  the controlled qualification result. Source tests do not grant production
  approval.

## Alternatives considered

### Keep repository JSON plus automatic package-runner startup

Rejected. Configuration-file modification or dependency resolution could alter
executable behavior without a new consent decision, and package runners expand
network and supply-chain authority.

### Expose Streamable HTTP or WebSocket immediately

Rejected for the first release. Those transports add listener, origin,
authorization, session, DNS-rebinding, and network-isolation work that is not
required for the local connector workflow.

### Preserve sampling and route it to any configured provider

Rejected. That would create another provider-call and budget boundary. Sampling
is not advertised until a product requirement and the existing governed provider
path can prove call, cost, privacy, trace, cancellation, and result parity.

### Keep placeholder built-in tools for discoverability

Rejected. A production-visible capability must perform its documented real
operation or be absent.

## Consequences

Positive:

- one small protocol and process surface;
- visible, exact owner consent;
- no caller-controlled authority;
- no plaintext renderer credential path;
- durable, traceable, content-bounded operations;
- hostile output cannot declare itself trusted;
- unsupported features fail explicitly.

Costs and constraints:

- connectors must ship or install a stable executable before registration;
- network-only MCP servers are unsupported;
- a changed executable path, arguments, root, scope, or limit requires review;
- Job Objects do not provide filesystem sandboxing, so installed OS-level file
  isolation remains a release gate;
- backup/restore, packaged UI, crash/reboot, and Windows security-product
  acceptance must pass before production enablement.

## Acceptance boundary

CP11-A, CP11-B, and CP11-D pass at the source/engineering boundary. CP11-C has
source adversarial command/path/network/output/timeout/cancellation/process-tree
coverage, while installed OS file isolation and security-product behavior remain
open. CP11-E is explicitly installed-only and remains release-blocking.

## Implementation references

- `backend/mcp_server/policy.py`
- `backend/mcp_server/credential_store.py`
- `backend/mcp_server/live_state.py`
- `backend/routes/mcp_routes.py`
- `core/mcp/mcp_client.py`
- `core/mcp/mcp_manager.py`
- `core/mcp/process_containment.py`
- `core/mcp/runtime_loop.py`
- `migrations/versions/e0f1a2b3c4d5_add_mcp_connector_authority.py`
- `frontend/app/admin/mcp/servers/page.tsx`
- `tests/mcp/`
- `reports/production-readiness/2026/phase-11/`
