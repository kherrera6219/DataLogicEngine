# Phase 11 Engineering Checkpoint Summary

Date: 2026-07-14
Status: **Engineering checkpoint complete; rebuilt-installed exit gates retained.**

## Outcome

Phase 11 replaces the permissive and partly simulated MCP surface with one
governed local connector boundary. Production-visible connectors are explicitly
registered, reviewed, fingerprinted, consented, scoped, started, discovered,
called, cancelled, stopped, and removed through durable owner controls.

## Delivered

- ADR-0008 selects MCP `2025-11-25` over local `stdio`; remote MCP transports,
  OAuth, tasks, roots, elicitation, connector sampling, and caller-owned context
  are outside the supported production set.
- Exact executable, argument, working-directory, environment, file-root, network,
  scope, and resource-limit validation with consent invalidation on definition
  changes.
- DPAPI-protected credential values that are never serialized to the renderer.
- PostgreSQL authority for definitions, consent, lifecycle, discovery, execution,
  hashes, errors, and result references; content-free Redis live-state mirrors are
  published only after the authoritative commit.
- Bounded durable stdio JSON-RPC, timeout and explicit cancellation, Windows Job
  Object process-tree containment, output caps, protocol checks, and hostile
  malformed/oversized/delayed/child-process fixtures.
- Untrusted-result envelopes, secret redaction, prompt-injection risk marking,
  privacy/evidence/trace metadata, inline result caps, and governed large-result
  storage in the required `mcp-results` object bucket.
- Removal of fake web search, echo sampling, placeholder UKG/pillar/KA/graph/
  simulation defaults, repository JSON auto-start, and bulk startup.
- Owner-facing connector registration, exact-authority review, consent,
  discovery, health, execution, cancellation, restart, stop, revoke, and removal
  controls.

## Validation snapshot

- Backend: **2,094 passed, 18 skipped**.
- Frontend: **83 files / 411 tests passed**.
- Focused MCP and adjacent route regression: **60 passed**; the final
  warnings-as-errors MCP/route rerun passed **49**.
- Frontend lint passed with one pre-existing warning; TypeScript and production
  build passed with 30 static routes.
- Ruff, Python compilation, schema parity, migration inventory, data-contract
  inventory, route inventory, and documentation reference validation passed.
- Alembic: 24 revisions, head `e0f1a2b3c4d5`.
- Data authority: 86 PostgreSQL entities, 31 logical contracts, nine required
  object buckets, and 481 classified routes.

## Release decision

This checkpoint is not production approval. CP11-C and CP11-E still require the
rebuilt installed application to prove Windows file/network isolation, DPAPI and
ACL behavior, child cleanup, crash/reboot recovery, service/store reconciliation,
and the complete Electron workflow. Alert 389, independent reviews, signing,
other earlier installed gates, and final object-store Replacement Control remain
release blockers. SeaweedFS remains a candidate only; no production object-store
selection has been made.
