# CP19-J Knowledge Algorithm product workflow

**Date:** 2026-08-01

**Status:** Passed at source checkpoint

**Release effect:** None; production remains NO-GO and rebuilding remains blocked

## Finding

CP19-I connected the internal product subsystems to the canonical Knowledge
Algorithm runtime, but the public product surface still exposed a compatibility
execution call rather than a durable plan/confirm/execute workflow. It had no
principal-owned run record, exact confirmation contract, durable cancellation
or recovery policy, generated SDK parity, or one desktop surface for inspecting
the real result and its trace, artifacts, and effects.

## Canonical product workflow

Manifest `2026.07.25-cp19j.1` retains all 213 canonical capabilities, one
implementation/controller per identity, 149 production-enabled capabilities,
and the 136-edge zero-cycle dependency graph. The new product workflow invokes
only `ManifestKASelector`, `KAPlanExecutor`, and `CanonicalKAController`.
Compatibility execution also passes through that boundary; it no longer owns a
second execution path.

The server derives the principal, scopes, runtime context, available
capabilities, risk, and budgets. Clients may supply input and request a
canonical capability, but cannot assert trusted context, available services,
provider access, effect authority, or a successful outcome.

## Durable, principal-owned runs

Alembic revision `0a1b2c3d4e5f` adds `ka_product_runs` as the single revision
head. The table stores principal ownership, an idempotency key and request
fingerprint, public content-free plan metadata, encrypted request/result
payloads, integrity hashes, state, cancellation, error, and timestamps. API-key
principals are namespaced by the exact key as well as the owner account, so two
keys owned by one user cannot replay or read each other's runs.

Idempotent planning returns the same run only for the same principal and exact
request fingerprint. Conflicting reuse fails closed. Startup reconciliation
resumes queued work through a content-free cross-process Redis lease. Active
workers renew that lease; a periodic reconciler marks an unleased interrupted
run failed with `KA_RUN_INTERRUPTED`. It never silently replays work whose
effects may already have occurred. Expired runs are excluded from every
principal read, and expired terminal/planned records are purged so encrypted
payloads do not outlive the configured run-retention period.

## Confirmation, cancellation, and effects

High/critical-risk or effect-oriented plans require the exact server-issued
confirmation token and digest. The durable runner checks cancellation between
canonical execution units and records truthful queued, running,
cancellation-requested, cancelled, succeeded, or failed states. Completed results are released only
after their encrypted payload and integrity hash agree.

KA output remains a proposal. The product workflow never invents an applied
effect. Its effect evidence surface returns only a receipt already bound by the
authoritative owning service and rejects invalid receipt structure or hashes.

## Authenticated API, SDK, and desktop

Four least-authority scopes now separate catalog/run reads, planning,
execution, and cancellation. Twelve `/api/v1/ka` product routes provide the
catalog plus plan, list, detail, execute, cancel, result, trace, artifact, and
effect operations. The legacy external history route is retired rather than
leaking unowned records.

Both generated SDKs expose the complete workflow. The Python SDK provides nine
synchronous and nine asynchronous operations; the TypeScript SDK provides nine
operations. The desktop Algorithms page uses the real backend for catalog
search, plan review, exact confirmation, execution, cancellation, polling, and
all evidence views. Tool History now lists the same principal-owned durable
runs.

## Proof

- all 213 canonical capabilities and 149 enabled entries remain present;
- all 12 product API paths and four KA scopes pass contract verification;
- 41 focused backend/frontend workflow tests pass;
- all six Python SDK tests and all seven TypeScript SDK tests pass;
- the full frontend suite passes 426 tests across 87 files;
- frontend type checking and the production Next.js build pass;
- all 2,557 Python source tests pass with 19 skipped and 35 known warnings;
- the 26-revision Alembic graph has one base and one head;
- the data inventory owns 87 SQL entities and 32 logical contracts;
- OpenAPI parsing, compilation, Ruff, manifest/runtime/integration/selector,
  product-version, documentation, and source-hygiene gates pass.

## Boundary and next checkpoint

CP19-J proves the source product workflow. It does not claim a complete
individual proof row for each of the 213 capabilities, clean-source rebuild
authorization, installed accessibility or Electron acceptance, signing,
independent review, provider-human acceptance, or soak completion. CP19-K is
active for complete per-KA proof. The signed rebuild remains blocked through
CP19-L, and exact rebuilt-installed acceptance remains CP19-M.
