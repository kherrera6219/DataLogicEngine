# Changelog

## 0.7.0 (2026-07-13)

- Added thin synchronous and asynchronous `dle-gateway.v1` clients.
- Added chat, live governed SSE, durable runs, result polling, cancellation,
  capability discovery, and client-owned trace retrieval.
- Added typed gateway errors, safe idempotent retry, and exact contract-version
  validation without any client-side provider or reasoning stack.
- Documented that provider credentials remain inside the installed service.

## 0.6.0 (2026-07-13)

- Removed duplicate client-owned provider and TruthEngine orchestration.
- Converted compatibility entry points into service-client shims over the
  canonical governed backend.

## 0.5.0 (2026-05-27)

- Added offline-capable `DSQPClient` that no longer depends on backend package imports.
- Kept `CoordinateResolver17` wired to bundled taxonomy JSON files for local/offline resolution.
- Updated package metadata and package data for SDK v0.5.0.

## 0.3.1 (2026-01-30)

- **Readiness**: Added `py.typed` marker for PEP 561 compliance.
- **Observability**: Added structured logging to `api_client` (duration, status, masked headers).
- **Versioning**: Added `X-API-Version` header to all requests.
- **Samples**: Added `examples/quickstart.py`.

## 0.3.0 (2026-01-05)

- Consolidated v0.2.0 + v0.2.1 into a single SDK release.
- TruthEngine v7.3 wired in as `ukg_sdk.truth_engine` with spec loader support.
- Added/updated KA execution hooks (live registry → execution map) and KA hooks.
- Added 10-layer stack, 12-step refinement, and FROST context-simulation modules.
- Maintained provider adapters (OpenAI / Azure OpenAI / Anthropic) and memory adapters.
