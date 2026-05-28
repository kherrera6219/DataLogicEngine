# Changelog

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

