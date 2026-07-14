# Phase 5 Rollback Notes

Date: 2026-07-13

1. Preserve the database and object-store backup before reverting an installed
   deployment. Do not re-enable duplicate gateway/SDK orchestration as a partial
   rollback.
2. Migration `b1c2d3e4f5a6` expands trace-run status storage from 20 to 32
   characters. Downgrade is safe only after verifying no stored status exceeds
   the older limit; otherwise retain the expanded schema.
3. A source rollback must restore gateway, caller, trace, frontend contract, SDK,
   and migration changes together. Mixing the old callers with `governed.v1`
   produces an unsupported contract split.
4. Persisted Phase 5 traces may remain as historical audit data. They use stable
   IDs and explicit contract version metadata and do not require deletion for a
   source rollback.
5. If the canonical orchestrator fails in a future release candidate, stop the
   release and restore the last known-good complete application/data backup;
   never bypass policy, trace, or validation to regain availability.

