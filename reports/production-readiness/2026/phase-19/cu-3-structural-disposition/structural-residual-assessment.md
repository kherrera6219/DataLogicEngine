# CU-3 structural residual assessment

| Field | Value |
|---|---|
| Assessment date | 2026-08-18 |
| Source HEAD | `254be21ffe4b8b0ff9233e975530ee12c7ac7c8d` |
| Working tree | Dirty; CU-0 through CU-2 review/evidence changes are uncommitted |
| Scope | Phase 5 residual decomposition decision support |
| Result | Audit complete; owner disposition remains required |
| Release effect | None; production/public release remains **NO-GO** |

## Measured residuals

| Boundary | Current size | Current state | Main compatibility concern |
|---|---:|---|---|
| `backend/llm_gateway/api.py` | 3,109 lines / 123,826 bytes | Monolithic Flask API module | At least 13 active tests patch symbols through the module namespace, including `LLMGateway`, `AtomicGatewayLimiter`, `ExternalAPIKey`, `cache`, and `get_gateway_job_runner` |
| `backend/routes/mcp_routes.py` | 1,859 lines / 73,433 bytes | Monolithic MCP route module | Route/auth/resource tests import and exercise the current module boundary |
| `backend/governed_execution/orchestrator.py` | 2,681 lines / 107,131 bytes | Layer contracts extracted; orchestration body retained | Phase 19 causality, refinement, TruthGate, lifecycle, and unit tests depend on the current controller boundary |
| `frontend/electron/main.ts` | 1,808 lines / 63,284 bytes | Path and environment helpers extracted; IPC/lifecycle body retained | Electron route and visual smoke tests exercise the current main-process boundary |

The earlier package-conversion attempt for the gateway and MCP API boundaries
was reverted because it changed patch-visible module bindings. The current tree
still contains those compatibility dependencies. No evidence supports treating
the four residual splits as completed.

## Risk and ordering assessment

Reopening any of these boundaries now would change the source used for the
pending CP19-M candidate. It would require focused behavior and route parity,
the complete applicable source gates, and a new exact clean-source rebuild
before installed evidence could proceed. That work does not remove the present
OpenAI quota or production-signing authority blockers.

The safest implementation pattern remains:

1. extract pure helpers without changing route or controller ownership;
2. preserve every patch-visible name on its existing public module;
3. move one boundary at a time in this order: gateway, governed orchestrator,
   MCP routes, then Electron main;
4. require focused tests after each extraction and full applicable validation
   before accepting the next boundary; and
5. rebuild and rebind every installed acceptance receipt to the resulting exact
   clean commit.

## Recommendation

Defer the four major decompositions to a named post-release maintenance phase.
They are maintainability work, not evidence that can close the current external,
signing, installed, accessibility, independent-review, pilot, or soak gates.
This recommendation is not an owner waiver and does not mark CU-3 complete.

If the owner instead requires the splits before release, that decision must
explicitly reopen the source line and invalidate any earlier candidate as the
CP19-M acceptance target. Partial helper extraction alone must not be recorded
as completion of CU-3.

## Durable decision still needed

The product owner must select one outcome in the active authority documents:

- pre-release source reopen, followed by all four split acceptance criteria and
  a replacement exact-artifact cycle;
- post-release maintenance deferral with a named target phase; or
- formal residual-risk waiver with scope, rationale, approver, and review date.

Until that choice is recorded, CU-3 remains disposition-blocked and the current
code remains unchanged.
