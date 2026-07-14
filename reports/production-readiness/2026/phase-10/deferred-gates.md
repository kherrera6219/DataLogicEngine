# Phase 10 Deferred Installed Gates

Date: 2026-07-14

These gates require the later rebuilt and installed application and are not
represented as passed by source tests:

1. Owner-configured OpenAI and Google live simulations prove exact call, token,
   tool, timeout, cancellation, known/unknown price, and cost-ceiling behavior.
2. Backend/process/service interruption proves verified-checkpoint resume or
   safe terminal failure without duplicate provider calls.
3. Redis progress/control events match PostgreSQL transitions and installed UI
   state during pause, resume, cancel, retry, failure, and materialization.
4. Required transcript/result objects exist in the production S3 service with
   exact revision/hash parity; approved live summaries/relationships reconcile
   with Chroma/Neo4j and restore/delete correctly.
5. Installed Simulation Monitor passes keyboard, visual, error, offline/service
   failure, and owner acceptance against the real backend.
6. Result conclusions, citations, validators, confidence/Not measured state,
   trace, and artifact export pass populated owner review.

Failure of any item blocks production/public release.
