# CP19-H Truth, data, and knowledge lifecycle integration

**Date:** 2026-07-25

**Status:** Passed at source checkpoint

**Release effect:** None; production remains NO-GO and rebuilding remains blocked

## Finding

CP19-G completed the canonical refinement workflow, but the surrounding
Truth/data/knowledge lifecycle still had disconnected or incomplete KA use.
Entry and L8 policy did not share one typed KA-backed decision. Retrieval did
not enforce authorized TruthMemory recall or use causal retrieval ranking.
Validated memory was not staged and promoted through the release safety chain.
TruthLink and FROST did not publish the governed stage/child-KA lifecycle as a
release dependency. Ingestion and retention owned real store effects but did
not dispatch their assigned KA pipeline through the canonical selector.

## Runtime authority

Manifest `2026.07.25-cp19h.1` retains 213 canonical capabilities and one
controller. It production-admits 89 capabilities in total, including the 60
distinct IDs assigned to four subsystem owners and 61 operation references.
The repeated `KA-1079` reference is one canonical promotion capability reused
by two operations under the same lifecycle authority, not a duplicate
implementation or canonical ID. The dependency graph has 136 edges and zero
cycles. `KA-029`, `KA-034`, `KA-051`, `KA-054`, `KA-055`, and `KA-063` remain
experimental and disabled.

`KnowledgeLifecycleCoordinator` reads the owner/operation registry from the
manifest, rejects IDs outside the requested owner operation, and executes only
through `ManifestKASelector`, `KAPlanExecutor`, and the shared
`CanonicalKAController`.

## Governed answer lifecycle

- Entry TruthGate executes the policy/safety/privacy KAs and records one typed
  `GovernedPolicyDecision`; a blocking result stops before routing or provider
  execution.
- L8 executes its manifest-owned policy plan and records the same decision
  contract. TruthCore remains a stage library inside the one governed
  orchestrator and does not own an alternate answer, provider, or persistence
  path.
- Retrieval may recall only validation-approved, nonexpired,
  nonquarantined/noncontained memory matching the session and declared
  owner/principal/tenant scope. `KA-079` causally orders evidence and citations
  without dropping unmatched evidence.
- A response memory write is staged before release. It is committed only after
  L10 and the selected integrity, provenance, containment, quarantine,
  promotion, and lifecycle chain pass. Failed governed-trace persistence rolls
  back the write.
- TruthLink and FROST publish real begin/finish stage transitions and child-KA
  transitions with causal parent/child identifiers and verified snapshots.
  Publication failure is recorded and prevents release.

## Data and effect boundary

Secure ingestion dispatches `KA-071` through `KA-078` after acquisition and
before SQL, vector, graph, object, or outbox materialization. The KAs return
bounded proposals and cannot claim applied store effects. Existing
authoritative services still perform materialization, idempotency,
reconciliation, and receipt handling. A required KA failure marks the durable
job failed and leaves zero knowledge-graph or outbox effects.

Retention deletion dispatches its cache-invalidation and failure/recovery KAs
while the existing cross-store deletion coordinator remains the only deletion
authority. Partial store results remain fail closed and cannot report complete.

## Proof

- 13 CP19-H integration tests pass;
- 79 affected governed-execution, ingestion, retention, and CP19-H tests pass;
- all 767 Knowledge Algorithm tests pass;
- all 2,541 source tests pass with 19 skipped and 21 known warnings;
- all six TypeScript SDK tests pass;
- the current manifest/runtime/selector authority verifiers pass;
- Python compilation and critical Ruff checks pass; and
- all active documentation gates pass after generated artifacts are refreshed.

## Boundary and next checkpoint

CP19-H does not claim that simulation, MCP, providers, gateway, security,
operations, durable jobs, effect-service receipts, the product API/SDK/desktop
workflow, the complete 213-row individual proof, rebuild authorization, or
installed acceptance are complete. CP19-I is active. The signed rebuild remains
blocked through CP19-L and installed acceptance remains CP19-M.
