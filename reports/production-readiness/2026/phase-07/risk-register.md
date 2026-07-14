# Phase 7 Risk Register

Date: 2026-07-13

| Risk | Disposition |
|---|---|
| Deterministic provider fixtures could be mistaken for live acceptance | CP7-F remains explicitly deferred to the rebuilt installed app with owner-supplied keys. |
| Complete-response chunking could be marketed as native streaming | Every current SSE event says `delivery_mode: buffered`; native governed SSE is Phase 8. |
| Unknown provider pricing could appear free or bypass all limits | Price stays nullable/unknown; call and token ceilings always apply. |
| Successful output could escape without durable usage evidence | Ledger write failure is fail-closed and prevents result release. |
| Retry/refinement could exceed owner intent | Every attempt consumes the request and durable usage budgets. |
| Cross-provider failover could disclose content to an unselected provider | Only one supported selected provider/model is attempted; no silent cross-provider failover exists. |
| Offline replay could retain unsafe/non-transient work | Only network/outage/timeout is eligible; Windows production requires DPAPI, bounded expiry/size, idempotency, and policy re-check. |
| Removed direct audio provider paths reduce current capability | Audio returns an explicit 501 capability boundary until a governed adapter is approved; no hidden call remains. |
| ChromaDB critical advisory | Existing alert 389 mitigation remains release-blocking and unchanged by Phase 7. |
| Object-store selection | SeaweedFS remains candidate-only; MinIO remains the production architecture pending full Replacement Control and owner approval. |
