# SDK developer contract — v0.6

The Python package is a client boundary. The installed backend is the sole owner
of the `governed.v1` request lifecycle and its trace transaction.

## Supported architecture

1. The client sends a request to `/api/v1/gateway/chat`.
2. The backend performs admission, DMRF routing, retrieval, deterministic DSQP,
   TruthCore/KA preflight, provider execution, validation, and persistence.
3. The client returns the backend trace ID and measured fields without inventing
   confidence, stages, durations, or local audit events.

SDK code must not call a model provider directly as part of a product request,
run a local KA safety pipeline, reconstruct DSQP, or synthesize a second trace.
Provider adapter modules may remain for backend/internal compatibility but are
not orchestration entry points.

## Compatibility testing

The SDK suite uses an HTTP mock transport and asserts:

- the request targets `/api/v1/gateway/chat`;
- an object passed through the deprecated `provider=` parameter is never called;
- returned `contract_version`, `status`, trace ID, and nullable confidence are
  preserved;
- legacy `TruthEngine` names use the same service boundary;
- the overlay has no KA-061 or DSQP execution hooks.

Installed OpenAI/Gemini qualification belongs to CP5-E and is not satisfied by
SDK unit tests.
