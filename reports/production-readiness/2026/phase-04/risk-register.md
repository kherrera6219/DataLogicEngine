# Phase 4 Risk Register

| Risk | Disposition | Control / next gate |
|---|---|---|
| Partial cross-store materialization | Closed for implemented Phase 4 writers | Transactional outbox, hash/revision envelope, idempotent handlers, retries, reconciliation state |
| Partial or unauthenticated backup | Closed for current-version engineering | Required component set, manifest HMAC, per-file SHA-256, AES-256-GCM, archive readback |
| Mixed-version or partial restore | Closed for current-version engineering | Isolated services/root, per-store verification, cross-store check, atomic swap, prior-root rollback |
| Deletion falsely reports success | Closed for canonical user deletion | Per-store tombstone status, remnant checks, partial-failure exception, retired partial route |
| Unsupported 0.1.1 retained-data upgrade | Deferred release blocker | Rebuild/install/populate/uninstall/reinstall/upgrade matrix on release candidate |
| Signed clean-machine recovery | Deferred release blocker | Signed installer and clean Windows recovery drill |
| Active data volume or root ACL unprotected | Deferred release blocker; current machine failed proof | Supported Windows BitLocker/device-encryption and installed-root ACL matrix |
| Independent backup/restore review | Deferred release blocker | Independent architecture/security/operations review |
| SSD/snapshot secure deletion guarantee | Accepted residual risk with disclosure | Retention expiry and cryptographic erasure where applicable; never claim universal physical erasure |
| SeaweedFS production selection | Deferred owner decision | Full Replacement Control and explicit final approval; MinIO remains authority |
| Later Phase 8/9 durable entities/workflows | Assigned to owning phases | Ownership matrix keeps missing job/idempotency/virtual-model and legacy memory consolidation visible |
| ChromaDB critical code-injection advisory, no patched release | Mitigated for engineering; open release blocker | Locked Rust server is not the affected Python backend; Python client rejects persisted embedding functions/schema; upgrade/replace and adversarially qualify before release |
