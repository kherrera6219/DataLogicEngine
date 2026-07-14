# Phase 8 Risk Register

Date: 2026-07-13

| Risk | Disposition |
|---|---|
| Source contract tests could be mistaken for installed interoperability | CP8-I and installed parts of CP8-B/C/F/G/J remain explicit release blockers. |
| Private listener could expose the app before TLS/firewall qualification | `private_windows_gateway` fails closed and remains disabled. Loopback is the default. |
| Client credentials could expose provider or admin authority | Clients receive copy-once `ukg_` keys only; provider secrets stay server-owned and administrative scopes are not client scopes. |
| Retries could duplicate provider spend or side effects | PostgreSQL idempotency authority binds client and idempotency key; incomplete/unsafe replay terminates explicitly. |
| Concurrency limits could race across workers | Atomic Redis counters and expiring concurrency/worker leases are required in production and fail closed when unavailable. |
| Streaming could release unvalidated provider text | Stage events are live, but provider text is withheld until validation and released only as `validated_output`. |
| Large job results could overflow PostgreSQL or disappear | Encrypted large payloads use `gateway-results` with bucket/key/hash/size references and safe 202/503 behavior. |
| Restart could silently re-run unsafe work | Running work becomes `JOB_INTERRUPTED_RETRY_UNSAFE`; queued work may resume only through the durable job contract. |
| OpenAI compatibility could imply full OpenAI API parity | The facade is bounded by the versioned compatibility matrix and rejects unsupported fields. |
| Health/trace routes could disclose topology or another client's data | Health requires authentication; external trace reads require scope and proven key ownership, with evidence separately scoped. |
| ChromaDB critical advisory | Alert 389 remains release-blocking pending a reviewed patched version and adversarial qualification. |
| Object-store selection | SeaweedFS remains candidate-only; MinIO remains the production architecture pending full Replacement Control and owner approval. |
